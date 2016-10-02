#!/usr/bin/env python

##
## This code is borrowed for Ubuntu plainbox-provider-resource-generic package
##
## https://apt-browse.org/browse/ubuntu/trusty/main/i386/plainbox-provider-resource-generic/0.3-1/file/usr/lib/2013.com.canonical.certification:plainbox-resources/bin/block_device_resource
## https://askubuntu.com/questions/528690/how-to-get-list-of-all-non-removable-disk-device-names-ssd-hdd-and-sata-ide-onl/
##


import os
import re
from glob import glob

rootdir_pattern = re.compile('^.*?/devices')
internal_devices = []


def device_state(name):
    """
    Follow pmount policy to determine whether a device is removable or internal.
    """
    with open('/sys/block/%s/device/block/%s/removable' % (name, name)) as f:
        if f.read(1) == '1':
            return

    path = rootdir_pattern.sub('', os.readlink('/sys/block/%s' % name))
    hotplug_buses = ("usb", "ieee1394", "mmc", "pcmcia", "firewire")
    for bus in hotplug_buses:
        if os.path.exists('/sys/bus/%s' % bus):
            for device_bus in os.listdir('/sys/bus/%s/devices' % bus):
                device_link = rootdir_pattern.sub('', os.readlink(
                    '/sys/bus/%s/devices/%s' % (bus, device_bus)))
                if re.search(device_link, path):
                    return

    internal_devices.append(name)


def get_internal_devices ():
    for path in glob('/sys/block/*/device'):
        name = re.sub('.*/(.*?)/device', '\g<1>', path)
        device_state(name)
    return internal_devices
