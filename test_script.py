#!/usr/bin/env python

##  This script tests the exported function of encrypt_config and reencrypt_backend


from __future__ import print_function
import decimal
import time
import encrypt_config
import reencrypt_backend


########## test encrypt_config - get_encrypted_part ##########

config, error_message = encrypt_config.get_encrypted_part()
if not config:
    print("error_message = " + error_message)
    exit(5)

print("Result")
if 'dev_path' in config:
    print("dev_path = " + config['dev_path'])
print("config_file = " + config['config_file'])
print("encrypt_part = " + config['encrypt_part'] + "\n")


########## test reencrypt_backend ##########

def show_progress_dict(progress_dict):
    if progress_dict:
        print("Result ", end='')
        print("Progress = " + progress_dict['status'], end='')
        print("  percent = " + str(progress_dict['percent']), end='')
        print("  ETA = " + str(progress_dict['eta']), end='')
        print("  written = " + progress_dict['written'], end='')
        print("  speed = " + str(progress_dict['speed']))


def show_luks_dict(luks_dict):
    if luks_dict:
        print("Result ", end='')
        print("cipher_name = " + luks_dict['cipher_name'], end='')
        print("  key_slot_0 = " + luks_dict['key_slot_0'], end='')
        print("  key_slot_6 = " + luks_dict['key_slot_6'])


error_message = reencrypt_backend.add_key(config['encrypt_part'], "test", "moi", 6)

print(" ")

luks_dict, luks_details, error_message = reencrypt_backend.read_luks_header(config['encrypt_part'])
show_luks_dict(luks_dict)

error_message = reencrypt_backend.delete_key(config['encrypt_part'], "test", 6)

print(" ")

luks_dict, luks_details, error_message = reencrypt_backend.read_luks_header(config['encrypt_part'])
show_luks_dict(luks_dict)

print(" ")

output, error_message = reencrypt_backend.read_master_key(config['encrypt_part'], "test")
print("Prev Master Key = " + output)

print(" ")

error_message = reencrypt_backend.do_reecnrypt(config['encrypt_part'], "test")

if error_message:
    print("This is the error_message:" + error_message)
    exit(5)

while True:
    time.sleep(3)
    progress_dict, error_message = reencrypt_backend.poll_progress()
    show_progress_dict(progress_dict)
    if progress_dict['percent'] == 100:
        break

print(" ")

# make sure re-encrypt has really ended
time.sleep(5)

print(" ")

output, error_message = reencrypt_backend.read_master_key(config['encrypt_part'], "test")
print("Current Master Key = " + output)


########## test encrypt_config - update_config_file ##########

config['reencrypted'] = "YES"
error_message = encrypt_config.update_config_file(config)
if error_message:
    print("error_message = " + error_message)
