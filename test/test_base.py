import unittest
import os
import sys

from constants import *

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parentdir)



from lib.util import *
from lib.module_manager import ModuleManager
import lib.validate


class TestBasics(unittest.TestCase):

    def setUp(self):
        # Clean the slate!
        remove_all_docker()
        remove_all_lxd()
        clean_ovs()
        remove_all_ovs()
        remove_db()

        self.mm = ModuleManager()
        self.mm.load()
        

    def test_build_base(self):
        self.mm['netreserve'].check()
        error, result = self.mm['netreserve'].run("add_network", description="test_network", net_addr="172.16.3.0/24", switch="testnet0")
        self.assertTrue(error == None)

        self.mm['dns'].check()
        error, result = self.mm['dns'].run("add_server", ip_addr=TEST_DNS_ROOT, description="test_dns", domain="test")
        self.assertTrue(error == None)
        error, result = self.mm['dns'].run("add_zone", id=1, direction="fwd", zone="test")
        self.assertTrue(error == None)
        error, result = self.mm['dns'].run("add_forwarder", id=1, ip_addr="8.8.8.8")
        self.assertTrue(error == None)

        self.mm['minica'].check()
        error, result = self.mm['minica'].run("add_server", fqdn="ca.test", ip_addr="172.16.3.3")
        self.assertTrue(error == None)

        return True

    def tearDown(self):
        pass