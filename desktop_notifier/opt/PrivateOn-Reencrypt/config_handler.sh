#!/bin/bash

##
##    PrivateOn-Reencrypt -- Because privacy matters
##
##  Author: Mikko Rautiainen <info@tietosuojakone.fi>
##
##  Copyright (C) 2017  PrivateOn / Tietosuojakone Oy, Helsinki, Finland
##  Released under the GNU Lesser General Public License
##

##
##  This script enables the user to read and update deploy.conf
##  This script should be run with sudo.
##


CONFIG_FILE='/boot/deploy.conf'


# Check that user is root
if test "$(id -u)" -ne 0; then
    echo "${0##*/}: only root can use ${0##*/}" 1>&2
    exit 1
fi


function display_usage()
{
    echo "Usage: $0 [OPTION] [VALUE]"
    echo "Read and update $CONFIG_FILE"
    echo ""
    echo -e "\t-h --help"
    echo -e "\t-g --get"
    echo -e "\t-u --update [VALUE]"
    echo ""
}


function get_file()
{
    cat $CONFIG_FILE | /usr/bin/grep =
}


function update_file()
{
    if [ $1 = "YES" ]; then
        sed -i -e '/remind_user =/ s/= .*/= YES/' $CONFIG_FILE
    elif [ $1 = "NO" ]; then
        sed -i -e '/remind_user =/ s/= .*/= NO/' $CONFIG_FILE
    else
        echo "$0: invalid Value '$1'" 1>&2
        exit 1
    fi
}


case "$1" in
    "-h"|"--help" )
        display_usage
        exit 0
        ;;
    "-g"|"--get" )
        get_file
        exit 0
        ;;
    "-u"|"--update" )
        if [  $# -gt 1 ]; then
            update_file $2
            exit 0
        else
            display_usage
            exit 1
        fi
        ;;
    * )
        echo "$0: invalid Option '$1'" 1>&2
        exit 1
        ;;
esac
