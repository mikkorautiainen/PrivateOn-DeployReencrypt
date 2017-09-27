#!/usr/bin/env python

##
##   PrivateOn-DeployReencrypt -- Because privacy matters
##
##   Author: Mikko Rautiainen <info@tietosuojakone.fi>
##
##   Copyright (C) 2016-2017  PrivateOn / Tietosuojakone Oy, Helsinki, Finland
##   Released under the GNU Lesser General Public License
##

##
##  This module does the heavy-lifting for the DeployReencrypt application
##


import decimal
import logging
import inspect
import random
import re
import string
import subprocess
import sys
import time
import os


## constants
DEBUG_LEVEL = logging.DEBUG
LOG_FILE = '/tmp/reencrypt.log'
OUT_FILE = '/tmp/reencrypt.out'
KEY_FILE = '/tmp/keyfile'
CRYPTSETUP = '/sbin/cryptsetup'
CRYPTSETUP_REENCRYPT = '/sbin/cryptsetup-reencrypt'
SUDO = '/usr/bin/sudo'


## functions
def run_command(command, description, target):
    error_message = None
    command = add_sudo(command)
    try:
        subprocess.check_call(command, shell=True)
    except subprocess.CalledProcessError, err:
        error_message = "Error: %s failed for %s with process error: returned non-zero exit status %s" % (description, target, str(err.returncode) )
        return error_message
    except OSError as err:
        error_message = "Error: %s failed for %s with OS error: %s" % (description, target, err.strerror)
        return error_message
    except:
        err = sys.exc_info()[1]
        error_message = "Error: %s failed for %s with generic error: %s" % (description, target, err)
        return error_message

    return error_message



def run_command_with_output(command, description, target):
    output = None
    error_message = None
    command = add_sudo(command)
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError, err:
        error_message = "Error: %s failed for %s with process error: %s" % (description, target, err.output)
        return [], error_message
    except OSError as err:
        error_message = "Error: %s failed for %s with OS error: %s" % (description, target, err.strerror)
        return [], error_message
    except:
        err = sys.exc_info()[1]
        error_message = "Error: %s failed for %s with generic error: %s" % (description, target, err)
        return [], error_message

    return output, error_message



def run_command_with_stderr(command, description, target):
    error_message = None
    command = add_sudo(command)
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError, err:
        error_message = "Error: %s failed for %s with process error: %s" % (description, target, err.output)
        return error_message
    except OSError as err:
        error_message = "Error: %s failed for %s with OS error: %s" % (description, target, err.strerror)
        return error_message
    except:
        err = sys.exc_info()[1]
        error_message = "Error: %s failed for %s with generic error: %s" % (description, target, err)
        return error_message

    return error_message



def popen_command(command, description, target):
    error_message = None
    command = add_sudo(command)
    try:
        FNULL = open(os.devnull, 'w')
        subprocess.Popen(command, shell=True, stdout=FNULL)
        FNULL.close()
    except subprocess.CalledProcessError, err:
        error_message = "Error: %s failed for %s with process error: returned non-zero exit status %s" % (description, target, str(err.returncode) )
        return error_message
    except OSError as err:
        error_message = "Error: %s failed for %s with OS error: %s" % (description, target, err.strerror)
        return error_message
    except:
        err = sys.exc_info()[1]
        error_message = "Error: %s failed for %s with generic error: %s" % (description, target, err)
        return error_message

    return error_message



def add_sudo(command):
    # if not root user
    if os.geteuid() != 0:
        # if command has pipe, add after pipe
        if re.search('|', command):
            result = command.split('|',1)
            if len(result) >= 2:
                command = result[0] + ' | ' + SUDO + ' ' + result[1]
            else:
                command = SUDO + ' ' + command
        else:
            command = SUDO + ' ' + command

    return command



def check_out_file ():
    error_message = None
    # wait for process to start
    time.sleep(1)

    # if OUT_FILE is missing, give wait another 3 second
    if not os.path.isfile(OUT_FILE):
        time.sleep(3)
        # if OUT_FILE still missing, give error message
        if not os.path.isfile(OUT_FILE):
            error_message = "Error: The reencrypt process failed to start: The cause of error is unknown."
            return error_message

    # read OUT_FILE
    try:
        with open(OUT_FILE, 'r') as out_file:
            for line in out_file:
                # skip warning text row
                if re.search('this is experimental code', line):
                    continue
                # everything OK if line has Progress or file is empty 
                if re.search('Progress', line):
                    break
                # everything else is an error message
                if not error_message:
                    error_message = "Error: Running reencrypt process: " + line.strip()
                else:
                    error_message = ", " + line.strip()
    except OSError as err:
        error_message = "Error: Can't read file %s: %s" % (OUT_FILE, err.strerror)
        return error_message
    except:
        error_message = "Error: Can't read file %s: Generic failure" % (OUT_FILE)
        return error_message

    return error_message



def test_password(part, password, slot=None):
    error_message = None

    # check that password is not empty
    if not password:
        error_message = "Error: The password can not be an empty string"
        logging.error(error_message)
        return error_message

    # run cryptsetup luksOpen --test-passphrase
    command = "printf '" + password + "'" + ' | ' + CRYPTSETUP + ' luksOpen --test-passphrase '
    command = command + part

    if slot is not None:
        command = command + " -S " + str(slot)

    description = 'LUKS volume pasword check'
    error_message = run_command_with_stderr(command, description, part)

    return error_message



def test_other_slots(part, password, key_slot):
    if test_password(part, password, key_slot) == None:
        for slot_num in range(8):
            if slot_num == int(key_slot):
                continue
            if test_password(part, password, slot_num) == None:
                return True
    return False



def read_luks_header(part):
    # logging
    function_name = inspect.stack()[0][3]
    logging.basicConfig(filename=LOG_FILE, level=DEBUG_LEVEL)
    logging.info("Starting reencrypt_backend.%s", function_name)

    # run luksDump
    command = CRYPTSETUP + ' ' + 'luksDump' + ' ' + part
    description = 'LUKS header dump'
    output, error_message = run_command_with_output(command, description, part)

    if not output:
        logging.error(error_message)
        return [], [], error_message

    # initiate luks_details + luks_dict
    luks_details = []
    luks_dict = {}
    luks_dict['cipher_name'] = 'UNKNOWN'
    luks_dict['cipher_mode'] = 'UNKNOWN'
    luks_dict['hash'] = 'UNKNOWN'
    luks_dict['key_size'] = 'UNKNOWN'
    luks_dict['uuid'] = 'UNKNOWN'
    for slot_num in range(8):
        luks_dict['key_slot_' + str(slot_num)] = 'UNKNOWN'

    # parse output
    for line in output.splitlines():
        # write luks_details list
        luks_details.append(line)

        # parse Cipher name
        if re.search('^Cipher name', line):
            result = re.match(r"Cipher name:(.*)", line)
            if result:
                luks_dict['cipher_name'] = result.group(1).strip()

        # parse Cipher mode
        if re.search('^Cipher mode', line):
            result = re.match(r"Cipher mode:(.*)", line)
            if result:
                luks_dict['cipher_mode'] = result.group(1).strip()

        # parse Hash spec
        if re.search('^Hash spec', line):
            result = re.match(r"Hash spec:(.*)", line)
            if result:
                luks_dict['hash'] = result.group(1).strip()

        # parse Key size
        if re.search('^MK bits', line):
            result = re.match(r"MK bits:(.*)", line)
            if result:
                luks_dict['key_size'] = result.group(1).strip()

        # parse UUID
        if re.search('^UUID', line):
            result = re.match(r"UUID:(.*)", line)
            if result:
                luks_dict['uuid'] = result.group(1).strip()

        # parse Key Slots
        if re.search('^Key Slot', line):
            result = re.match(r"Key Slot ([0-7]):", line)
            if result:
                slot_num = result.group(1)
                if re.search('ENABLED', line):
                    luks_dict['key_slot_' + slot_num] = 'ENABLED'
                elif re.search('DISABLED', line):
                    luks_dict['key_slot_' + slot_num] = 'DISABLED'
                else:
                    luks_dict['key_slot_' + slot_num] = 'UNKNOWN'

    logging.info("Completed reencrypt_backend.%s", function_name)
    logging.shutdown()

    return luks_dict, luks_details, error_message



def read_master_key(part, password):
    # logging
    function_name = inspect.stack()[0][3]
    logging.basicConfig(filename=LOG_FILE, level=DEBUG_LEVEL)
    logging.info("Starting reencrypt_backend.%s", function_name)

    # check that password is not empty
    if not password:
        error_message = "Error: The password can not be an empty string"
        logging.error(error_message)
        return error_message

    # make random target name
    map_name = 'target_' + ''.join( random.choice(string.lowercase) for i in range(5) )

    # run cryptsetup luksOpen
    command = "printf '" + password + "'" + ' | ' + CRYPTSETUP + ' luksOpen '
    command = command + part + ' ' + map_name

    description = 'open LUKS volume'
    error_message = run_command_with_stderr(command, description, part)

    if error_message:
        logging.error(error_message)
        return 'UNKNOWN', error_message

    # turn off logging to prevent recoring the master key
    logging.shutdown()

    # run dmsetup table
    command = 'dmsetup table --showkeys'
    description = 'read volume table'
    output, error_message1 = run_command_with_output(command, description, part)
    # note: continue even if no output or error_message1 not empty

    # turn logging back on
    logging.basicConfig(filename=LOG_FILE, level=DEBUG_LEVEL)

    # parse output
    master_key = 'UNKNOWN'
    for line in output.splitlines():
        # parse target line
        if re.search( '^' + map_name, line ):
            result = line.split(' ')
            if len(result) >= 6:
                master_key = result[5]

    # run cryptsetup luksOpen
    command = CRYPTSETUP + ' luksClose ' + map_name

    description = 'close LUKS volume'
    error_message2 = run_command_with_stderr(command, description, part)

    if error_message1:
        logging.error(error_message1)
        return master_key, error_message1

    if error_message2:
        logging.error(error_message2)
        return master_key, error_message2

    logging.info("Completed reencrypt_backend.%s", function_name)
    logging.shutdown()

    return master_key, error_message1



def add_key(part, password_current, password_new, key_slot):
    # logging
    function_name = inspect.stack()[0][3]
    logging.basicConfig(filename=LOG_FILE, level=DEBUG_LEVEL)
    logging.info("Starting reencrypt_backend.%s", function_name)

    # check that password is not empty
    if (not password_current) or (not password_new):
        error_message = "Error: The password can not be an empty string"
        logging.error(error_message)
        return error_message

    # delete tmp keyfile, just in case
    if os.path.isfile(KEY_FILE):
        os.remove(KEY_FILE)

    # write password_new to KEY_FILE
    key_file = open(KEY_FILE, 'w')
    key_file.write(password_new) 
    key_file.close()

    # run cryptsetup luksAddKey
    command = "printf '" + password_current + "'" + ' | ' + CRYPTSETUP + ' luksAddKey '
    command = command + part + ' --key-slot ' + str(key_slot) + ' ' + KEY_FILE

    description = 'Adding LUKS key'
    error_message = run_command_with_stderr(command, description, part)

    # delete tmp keyfile
    try:
        os.remove(KEY_FILE)
    except: 
        pass

    if error_message:
        logging.error(error_message)
        return error_message

    logging.info("Completed reencrypt_backend.%s", function_name)
    logging.shutdown()

    return error_message



def delete_key(part, password_current, key_slot):
    # logging
    function_name = inspect.stack()[0][3]
    logging.basicConfig(filename=LOG_FILE, level=DEBUG_LEVEL)
    logging.info("Starting reencrypt_backend.%s", function_name)

    # check that password is not empty
    if not password_current:
        error_message = "Error: The password can not be an empty string"
        logging.error(error_message)
        return error_message

    # if password matches the slot and same password is not in used on other slot, give error
    if test_password(part, password_current, key_slot) == None:
        if test_other_slots(part, password_current, key_slot) == False:
            error_message = "The password that you entered last matches this slot."
            error_message = error_message + " \nPlease press \"Delete key\" again and enter a different password."
            logging.error("Error: User tried to delete slot where this is only matching password")
            return error_message

    # run cryptsetup luksKillSlot
    command = "printf '" + password_current + "'" + ' | ' + CRYPTSETUP + ' luksKillSlot '
    command = command + part + ' ' + str(key_slot)

    description = 'Deleting LUKS key'
    error_message = run_command_with_stderr(command, description, part)

    if error_message:
        logging.error(error_message)
        # check if error because of wrong password
        if test_other_slots(part, password_current, key_slot) == False:
            error_message = "The entered password doesn't match any of the slots."
            error_message = error_message + " \nPlease press \"Delete key\" again and enter a different password."
            logging.error(error_message)
        return error_message

    logging.info("Completed reencrypt_backend.%s", function_name)
    logging.shutdown()

    return error_message



def preflight_check(part, password):
    error_message = None
    # logging
    function_name = inspect.stack()[0][3]
    logging.basicConfig(filename=LOG_FILE, level=DEBUG_LEVEL)
    logging.info("Starting reencrypt_backend.%s", function_name)

    # check that password is not empty and valid
    error_message = test_password(part, password)
    if error_message:
        logging.error(error_message)
        return error_message

    # check that only one password slot is in use
    luks_dict, luks_details, error_message = read_luks_header(part)
    if error_message:
        return error_message
    slot_count = 0
    for slot_num in range(8):
        if luks_dict['key_slot_' + str(slot_num)] == 'ENABLED':
            slot_count = slot_count + 1

    if slot_count != 1:
        if slot_count == 2:
            error_message = "This application can only re-encrypt if one key slot is in use."
            error_message = error_message +" Please delete %d key slot." % (slot_count-1)
        elif slot_count > 2:
            error_message = "This application can only re-encrypt if one key slot is in use."
            error_message = error_message +" Please delete %d key slots." % (slot_count-1)
        else:
            error_message = "Error: No key slots detected"
        logging.error(error_message)
        return error_message

    logging.info("Completed reencrypt_backend.%s", function_name)
    logging.shutdown()

    return error_message



def do_reecnrypt(part, password):
    # logging
    function_name = inspect.stack()[0][3]
    logging.basicConfig(filename=LOG_FILE, level=DEBUG_LEVEL)
    logging.info("Starting reencrypt_backend.%s", function_name)

    # run cryptsetup-reencrypt
    command = "printf '" + password + "'" + ' | ' + CRYPTSETUP_REENCRYPT + ' ' + part + ' 2>' + OUT_FILE
    if DEBUG_LEVEL == logging.DEBUG:
        logging.debug("Debug: Re-encrypt command = %s", add_sudo(command) )

    description = 'Re-encryption'
    error_message = popen_command(command, description, part)

    if error_message:
        logging.error(error_message)
        return error_message

    # check if cryptsetup_reencrypt has writen an error message to out file
    error_message = check_out_file()
    if error_message:
        logging.error(error_message)
        return error_message

    logging.info("Completed reencrypt_backend.%s", function_name)
    logging.shutdown()

    return error_message



def poll_progress ():
    error_message = None
    # logging
    function_name = inspect.stack()[0][3]
    logging.basicConfig(filename=LOG_FILE, level=DEBUG_LEVEL)
    logging.info("Starting reencrypt_backend.%s", function_name)

    # initiate progress_dict
    progress_dict = {}
    progress_dict['status'] = 'UNKNOWN'
    progress_dict['percent'] = 0
    progress_dict['eta'] = None
    progress_dict['written'] = 'UNKNOWN'
    progress_dict['speed'] = None

    # if OUT_FILE is missing, give error message
    if not os.path.isfile(OUT_FILE):
        error_message = "Error: The output file for the re-encrypt process is missing"
        logging.error(error_message)
        return progress_dict, error_message

    # read OUT_FILE's last line
    last_line = None
    try:
        with open(OUT_FILE, 'r') as out_file:
            for line in out_file:
                last_line = line
    except OSError as err:
        error_message = "Error: Can't read file %s: %s" % (OUT_FILE, err.strerror)
        logging.error(error_message)
        return progress_dict, error_message
    except:
        error_message = "Error: Can't read file %s: Generic failure" % (OUT_FILE)
        logging.error(error_message)
        return progress_dict, error_message

    if not last_line:
        error_message = "Warning: Failed to read output of re-encrypt process"
        logging.warning(error_message)
        return progress_dict, error_message

    # get last entry after clearline EL2 character
    last_progress = last_line.rsplit('\x1b[2K',1)
    if len(last_progress) < 2:
        last_progress = last_line
    else:
        last_progress = last_progress[1]

    # parse last_progress
    # example line = "Progress: 100.0%, ETA 00:00,  484 MiB written, speed  77.2 MiB/s"
    components = last_progress.split(', ')
    for component in components:
        component = component.strip()

        # parse Progress
        if re.search('Progress', component):
            result = re.match(r"Progress: (.*)\%", component)
            if result:
                progress_dict['percent'] = decimal.Decimal(result.group(1).strip())

        # parse ETA
        if re.search('^ETA', component):
            result = re.match(r"ETA (.*)", component)
            if result:
                progress_dict['eta'] = result.group(1).strip()
                progress_dict['status'] = 'running'

        # parse written
        if re.search('written', component):
            result = re.match(r"(.*) written", component)
            if result:
                progress_dict['written'] = result.group(1).strip()
                progress_dict['status'] = 'running'

        # parse speed
        if re.search('^speed', component):
            result = re.match(r"speed (.*)", component)
            if result:
                progress_dict['speed'] = result.group(1).strip()
                progress_dict['status'] = 'running'


    # decide if the process is "running" or "completed"
    if progress_dict['percent'] == 100:
        progress_dict['status'] = 'completed'

    logging.info("Completed reencrypt_backend.%s", function_name)
    logging.shutdown()

    return progress_dict, error_message



def do_reboot ():
    # logging
    function_name = inspect.stack()[0][3]
    logging.basicConfig(filename=LOG_FILE, level=DEBUG_LEVEL)
    logging.info("Starting reencrypt_backend.%s", function_name)

    # run reboot
    command = '/sbin/reboot'
    description = 'Reboot'
    target = 'system'
    error_message = run_command_with_stderr(command, description, target)

    if error_message:
        logging.error(error_message)
        return error_message

    logging.info("Completed reencrypt_backend.%s", function_name)
    logging.shutdown()

    return error_message



def do_poweroff ():
    # logging
    function_name = inspect.stack()[0][3]
    logging.basicConfig(filename=LOG_FILE, level=DEBUG_LEVEL)
    logging.info("Starting reencrypt_backend.%s", function_name)

    # run poweroff
    command = '/sbin/poweroff'
    description = 'Poweroff'
    target = 'system'
    error_message = run_command_with_stderr(command, description, target)

    if error_message:
        logging.error(error_message)
        return error_message

    logging.info("Completed reencrypt_backend.%s", function_name)
    logging.shutdown()

    return error_message
