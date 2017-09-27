#!/bin/bash

##
##      Check software dependencies for PrivateOn-DeployReencrypt
##
##  This script check that the required software is found on the system.
##  You only need to run this script once during setup.
##

##
##  Copyright (C) 2016-2017  PrivateOn / Tietosuojakone Oy, Helsinki, Finland
##  Released under the GNU Lesser General Public License
##


declare -a gnu_programs=(blkid dmsetup grep mount poweroff printf reboot umount)
declare -a other_programs=(cryptsetup cryptsetup-reencrypt gksudo python2 startx sudo wmctrl xfce4-terminal)
declare -a python_modules=(decimal glob inspect logging os parted random re string subprocess sys time PyQt5)

RED='\033[0;31m'
NC='\033[0m' # No Color

##START FUNCTIONS
check_file(){
    program=$1

    if (type $program >/dev/null 2>&1); then
        echo -e "${NC}\t$program found"
    else
        (>&2 echo -e "${RED}    Error: $program is required but it's not installed!${NC}")
    fi
}

check_module(){
    module=$1

    python2 -c "import $module; print('\t$module found')"
    if [ $? -ne 0 ]; then
        (>&2 echo -e "${RED}    Error: $module is required but it's not installed!${NC}")
    fi
}
## END FUNCTIONS


echo -e "\nChecking standard GNU software..."
for program in "${gnu_programs[@]}"; do
    check_file $program
done

echo -e "\nChecking other programs..."
for program in "${other_programs[@]}"; do
    check_file $program
done

echo -e "\nChecking Python modules..."
for module in "${python_modules[@]}"; do
    check_module $module
done
#python2 -c "import os; import os; print('\tAll modules found')"

echo -e "\nCheck completed."
