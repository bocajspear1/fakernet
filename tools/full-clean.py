import sys
import os

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parentdir)


from lib.util import *

if __name__ == '__main__':

   

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
    