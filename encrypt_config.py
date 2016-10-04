#!/usr/bin/env python

##
## PrivateOn-DeployReencrypt -- Because privacy matters
##
## Author: Mikko Rautiainen <info@tietosuojakone.fi>
##
## Copyright (C) 2016  PrivateOn / Tietosuojakone Oy, Helsinki, Finland
## Released under the GNU Lesser General Public License
##

##
##  This module reads the encrypted partition path from the configuration file
##  and updates the status of the re-encryption process to the file.
##


import internal_block_device_resource
import os
import parted
import re
import subprocess
import sys


CONF_FILE_NAME = 'deploy.conf'
REENCRYPT_PARAMETER = 'reencrypted'
PART_PARAMETER = 'encrypted_part'
SUDO = '/usr/bin/sudo'


#########################   Internal  Functions   #########################

def find_ext_part(blkdev_path):
    # if root use parted, if normal user use sudo blkid
    if os.geteuid() == 0:
        device = parted.getDevice(blkdev_path)
        disk = parted.Disk(device)
        primary_partitions = disk.getPrimaryPartitions()

        count = 1
        for partition in primary_partitions:
            # the boot part must be either part 1 or 2 of the device
            if count > 2:
                return []

            print "Partition: %s" % partition.path
            try:
                fs = parted.probeFileSystem(partition.geometry)
            except:
                fs = "unknown"
            print "Filesystem: %s" % fs
            if fs == 'ext2' or fs == 'ext3':
                return partition.path
            count += 1 # increment counter
    else:
        # the boot part must be either part 1 or 2 of the device
        for partition in [1, 2]:
            output = ''
            try:
                command = 'blkid ' + blkdev_path + str(partition)
                command = add_sudo(command)
                output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
            except:
                pass
            result = re.search(r"TYPE=(.*)\s", output)
            if result:
                fs = result.group(1).strip()
                fs = fs.split()[0]
                fs = fs.strip('"')
                if fs == 'ext2' or fs == 'ext3':
                    path = blkdev_path + str(partition)
                    return path

    # search failed
    return []



def find_boot_part ():
    error_message = None
    # find all internal devices 
    blkdevs = internal_block_device_resource.get_internal_devices()

    print("get_internal_devices = " + ' '.join(blkdevs))

    if not blkdevs:
        error_message = "Error: No disks found"
        print(error_message)
        return [], error_message

    result = []
    for blkdev in blkdevs:
        blkdev_path = "/dev/" + blkdev
        print "blkdev_path = %s" % blkdev_path
        result = find_ext_part(blkdev_path)
        if result:
            return result, error_message

    error_message = "Error: No ext2 or ext3 partitions found"
    print(error_message)
    return [], error_message



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



def mount_part(dev_path):
    error_message = None

    try:
        command = 'mount -o nosuid,uid=0,gid=0 ' + dev_path + ' /mnt'
        command = add_sudo(command)
        subprocess.check_call(command, shell=True)
    except subprocess.CalledProcessError, err:
        error_message = "Error: mount failed for %s with process error: %s" % (dev_path, err)
        print(error_message)
        return error_message
    except OSError as err:
        error_message = "Error: mount failed for %s with OS error: %s" % (dev_path, err)
        print(error_message)
        return error_message
    except:
        err = sys.exc_info()[1]
        error_message = "Error: mount failed for %s with error: %s" % ( dev_path, err )
        print(error_message)
        return error_message

    return error_message



def umount_part(dev_path):
    error_message = None

    try:
        command = 'umount ' + dev_path
        command = add_sudo(command)
        subprocess.check_call(command, shell=True)
    except subprocess.CalledProcessError, err:
        error_message = "Error: umount failed for %s with process error: %s" % (dev_path, err)
        print(error_message)
        return error_message
    except OSError as err:
        error_message = "Error: umount failed for %s with OS error: %s" % (dev_path, err)
        print(error_message)
        return error_message
    except:
        err = sys.exc_info()[1]
        error_message = "Error: umount failed for %s with error: %s" % ( dev_path, err )
        print(error_message)
        return error_message

    return error_message



def check_script_directory_for_config ():
    script_directory = os.path.dirname(os.path.realpath(__file__))
    config_file = script_directory + "/" + CONF_FILE_NAME
    if os.path.isfile(config_file):
        return config_file
    else:
        return None



def read_config_file(config):
    encrypt_part = None
    error_message = None
    try:
        with open(config['config_file'], 'r') as file_in:
            # iterate lines
            for line in file_in:
                # if comment, skip
                if line[0] == '#':
                    pass
                # parse only line with "="
                elif re.search('=', line):
                    result = line.split('=')
                    result[0] = result[0].strip()
                    if result[0] == PART_PARAMETER:
                        result[1] = result[1].strip()
                        # if part if an integer, concat the part # to dev_path
                        if result[1].isdigit():
                            if 'dev_path' in config:
                                base_device = config['dev_path'].rstrip('1234567890')
                                encrypt_part = base_device + result[1]
                        else:
                            encrypt_part = result[1]
    except:
        error_message = 'Error reading \"' + config['config_file'] + '\", configuration update failed.'

    return encrypt_part, error_message 



def write_config_file(value, config_file):
    error_message = None
    tmpfilename = config_file + ".tmp"
    written_flag = False
    try:
        with open(tmpfilename, 'w') as file_out:
            with open(config_file, 'r') as file_in:
                # iterate lines
                for line in file_in:
                    # if comment, copy to new file
                    if line[0] == '#':
                        pass
                    # parse only line with "="
                    elif re.search('=', line):
                        result = line.split('=')
                        result[0] = result[0].strip()
                        if result[0] == REENCRYPT_PARAMETER:
                            line = REENCRYPT_PARAMETER + " = " + value + "\n"
                            written_flag = True
                    # write line to tmp file
                    file_out.write(line)
            # if value has not been written, add to end of file
            if not written_flag:
                line = REENCRYPT_PARAMETER + " = " + value
                file_out.write(line)
    except:
        error_message = 'Error writing to \"' + tmpfilename + '\", configuration update failed.'
        return error_message

    # move tmp file -> orig file
    try:
        os.rename(tmpfilename, config_file)
    except:
        error_message = 'Error renaming \"' + tmpfilename + '\" to \"' + config_file + '\" '

    return error_message


#########################   Exported  Functions   #########################

def get_encrypted_part ():
    config = {}
 
    config['config_file'] = check_script_directory_for_config ()
    if config['config_file']:
        config['encrypt_part'], error_message = read_config_file(config)
        return config, error_message

    # if config file not found in script directory, read for boot part
    config['dev_path'], error_message = find_boot_part()
    if not config['dev_path']:
        return [], error_message

    # Note: only show mount error, if config file check fails
    error_message_mount = mount_part(config['dev_path'])
    config['config_file'] = '/mnt/' + CONF_FILE_NAME
    if not os.path.isfile(config['config_file']):
        error_message = "Failed to read configuration information. Missing /boot/" + CONF_FILE_NAME
        if error_message_mount:
            error_message = error_message_mount + "\n" + error_message
        return [], error_message

    config['encrypt_part'], error_message = read_config_file(config)

    # Note: possible umount error is not fatal, don't show to user
    mount_part(config['dev_path'])

    return config, error_message



def update_config_file(config):
    if 'config_file' not in config:
        error_message = "Internal error: Config missing 'config_file' key"
        return error_message
    if 'reencrypted' not in config:
        error_message = "Internal error: Config missing 'reencrypted' key"
        return error_message

    # mount boot part if config has 'dev_path' key
    if 'dev_path' in config:
        error_message_mount = mount_part(config['dev_path'])

    if not os.path.isfile(config['config_file']):
        error_message = "Failed to write configuration information. Missing /boot/" + CONF_FILE_NAME
        if error_message_mount:
            error_message = error_message_mount + "\n" + error_message
        return error_message

    error_message = write_config_file(config['reencrypted'], config['config_file'])

    if 'dev_path' in config:
        # Note: possible umount error is not fatal, don't show to user
        mount_part(config['dev_path'])

    return error_message
