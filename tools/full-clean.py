# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import sys
import os
import argparse

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parentdir)


from lib.util import *

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--force', action='store_true', help="Force tests without prompting for clearing everything")

    args = parser.parse_args()
    if not args.force:

        print("\033[91m{}\033[00m".format("!!!!!! - WARNING - !!!!!!\nThis will script is for pre-installation cleaning, or if things got really messed up. It will:"))
        print("\033[91m{}\033[00m".format("* Delete all Docker instances\n* Delete all LXD instances \n* Clear Open vSwitch switch configurations\n* Clear the FakerNet configuration"))

        print("\033[93m{}\033[00m".format("\nEnter 'doclean' in the prompt to continue."))
        selection = input("type 'doclean' to run the tests> ")
        if selection.strip() != 'doclean':
            print("Exiting...")
            sys.exit(1)

    print("Removing Docker containers...")
    remove_all_docker()
    print("Removing LXD containers...")
    remove_all_lxd()
    print("Cleaning OVS ports...")
    clean_ovs()
    print("Removing OVS switches...")
    remove_all_ovs()
    print("Removing database...")
    remove_db()
    