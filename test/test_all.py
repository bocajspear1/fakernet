import unittest
import argparse
import sys

import test_base
import test_network_reservation
import test_dns


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--force', action='store_true', help="Force tests without prompting for clearing everything")

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
    
    suite.addTests(loader.loadTestsFromModule(test_base))
    suite.addTests(loader.loadTestsFromModule(test_network_reservation))
    suite.addTests(loader.loadTestsFromModule(test_dns))

    runner = unittest.TextTestRunner(verbosity=3)
    result = runner.run(suite)
