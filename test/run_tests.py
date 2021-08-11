import unittest
import argparse
import sys
import importlib
import os
import subprocess

from constants import *

import test_base
import test_network_reservation
import test_dns
import test_nethop
import test_lxd
import test_simplemail
import test_inspircd
import test_bepasty
import test_alpine_webdav
import test_tinyproxy
import test_mattermost
import test_easyzone
import test_minica
import test_external

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--force', action='store_true', help="Force tests without prompting for clearing everything")
    parser.add_argument('-w', '--web', action='store_true', help="Run tests through the web server rather than locally")
    parser.add_argument('-m', '--module', help="Module to run tests on")

    args = parser.parse_args()
    if not args.force:

        print("\033[91m{}\033[00m".format("!!!!!! - WARNING - !!!!!!\nTo create a clean slate for testing, running the test suite will:"))
        print("\033[91m{}\033[00m".format("* Delete all Docker instances\n* Delete all LXD instances \n* Clear Open vSwitch switch configurations\n* Clear the FakerNet configuration"))

        print("\033[93m{}\033[00m".format("\nEnter 'runtests' in the prompt to continue."))
        selection = input("type 'runtests' to run the tests> ")
        if selection.strip() != 'runtests':
            print("Exiting...")
            sys.exit(1)

    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    runner = None

    subprocess.run("sudo iptables -t nat -A POSTROUTING -s 172.16.3.0/24 -j MASQUERADE ", shell=True)
    subprocess.run("sudo iptables -P FORWARD ACCEPT", shell=True)
    subprocess.run(f"sudo iptables -t nat -A OUTPUT -p udp -m udp --dport 53 -j DNAT ! -d 127.0.0.0/24 --to-destination {TEST_DNS_ROOT}:53", shell=True)
    subprocess.run(f"sudo iptables -t nat -A OUTPUT -p udp -m udp --dport 53 -j DNAT ! -s 172.16.3.0/24 ! -d 127.0.0.0/24 --to-destination {TEST_DNS_ROOT}:53", shell=True)

    suite.addTests(loader.loadTestsFromModule(test_base))
    if args.module:
        # singletest = importlib.import_module("test_" + args.module)
        singletest = importlib.import_module(args.module)
        suite.addTests(loader.loadTestsFromModule(singletest))
    else:

        testlist = open(os.path.dirname(os.path.abspath(__file__)) + "/active_tests.txt")
        testlines = testlist.read().split("\n")
        testlist.close()

        for line in testlines:
            line = line.strip()
            if not line.startswith("#") and line.strip() != "":
                print("Loaded {}".format(line))
                module = importlib.import_module(line)
                suite.addTests(loader.loadTestsFromModule(module))

    runner = unittest.TextTestRunner(verbosity=3)
    result = runner.run(suite)

    # Redirect DNS so we can resolve internal names
    subprocess.run(f"sudo iptables -t nat -D OUTPUT -p udp -m udp --dport 53 -j DNAT ! -d 127.0.0.0/24 --to-destination {TEST_DNS_ROOT}:53", shell=True)
    subprocess.run(f"sudo iptables -t nat -D OUTPUT -p udp -m udp --dport 53 -j DNAT ! -s 172.16.3.0/24  ! -d 127.0.0.0/24 --to-destination {TEST_DNS_ROOT}:53", shell=True)
    # Let internet-accessing modules get out with NAT
    subprocess.run("sudo iptables -t nat -D POSTROUTING -s 172.16.3.0/24 -j MASQUERADE ", shell=True)

    if result.wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)
