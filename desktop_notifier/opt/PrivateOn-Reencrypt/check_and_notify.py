#!/usr/bin/env python3

##
##    PrivateOn-Reencrypt -- Because privacy matters
##
##  Author: Oleh Zymmnytskiy <oleh.g.zymnytskiy@gmail.com>
##
##  Copyright (C) 2017  PrivateOn / Tietosuojakone Oy, Helsinki, Finland
##  Released under the GNU Lesser General Public License
##

##
##  This notifier reminds the user to re-encrypt their disk.
##  The notification is disabled by either running the PrivateOn-Reencrypt livecd 
##  or by pressing the "don't remind" button.
##

import os, sys
import time
import getopt
import subprocess

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Notify', '0.7')

from gi.repository import Gtk, Notify

interval = 0

keys, args = getopt.getopt(sys.argv[1:], 'i:')

for key, value in keys:
    if key == '-i':
        interval = int(value)

CONFIG_PATH = '/boot/deploy.conf'
NOTIFICATION_TITLE = ''
NOTIFICATION_BODY = """You have not re-encrypted your disk yet.
Re-encryption is easy with our included tool.
<a href="https://clientarea.privateon.net/index.php/knowledgebase">LUKS master key</a>"""
NOTIFICATION_ACTION = "don't show me this reminder again"
CONFIRM_TEXT = """Are you sure you don’t want to be reminded to re-encrypt your disk?
Please read our FAQ entry about the importance of changing the LUKS master key.
<a href="https://privateon.net/faq/">LUKS master key</a>"""

def read_config(path):
    lines = open(path).read().split('\n')
    config_files = list(filter(lambda x: not x.startswith('#') and len(x), lines))

    result = {}
    for line in config_files:
        key, value = map(lambda x: x.strip(), line.split('='))

        result[key] = value

    return result

show_message_dialog = False

def disable_notification(notification, action):
    global show_message_dialog

    show_message_dialog = False
    notification.close()
    confirm = Gtk.MessageDialog(None, 0, Gtk.MessageType.QUESTION, Gtk.ButtonsType.YES_NO)
    confirm.set_markup(CONFIRM_TEXT)
    response = confirm.run()
    confirm.destroy()

    if response == Gtk.ResponseType.YES:
        subprocess.call('sudo %s/config_handler.sh -u NO' % os.path.dirname(__file__), shell=True)

    Gtk.main_quit()

def on_notification_closed(notification):
    global show_message_dialog

    if not show_message_dialog:
        Gtk.main_quit()

def show_notification():
    Notify.init('private-on-reencrypt')
    notification = Notify.Notification.new(NOTIFICATION_TITLE, NOTIFICATION_BODY)
    notification.set_timeout(Notify.EXPIRES_NEVER)
    notification.add_action("disable", NOTIFICATION_ACTION, disable_notification)
    notification.connect('closed', on_notification_closed)
    notification.show()

    Gtk.main()

time.sleep(interval)

config = read_config(CONFIG_PATH)

if config['reencrypted'] == 'NO' and config['remind_user'] == 'YES':
    show_notification()

