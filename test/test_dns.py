import unittest
import os
import sys
import subprocess
import json

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parentdir)

import docker
import pylxd

from lib.util import clean_ovs, convert_ovs_table
from lib.module_manager import ModuleManager
import lib.validate

class TestNetworkReservation(unittest.TestCase):

    def setUp(self):
        self.mm = ModuleManager()
        self.mm.load()
        self.mm['dns'].check()

    def test_dns_list(self):
        error, result = self.mm['dns'].run("list")
        self.assertTrue(error == None)
        self.assertTrue(len(result['columns']) == 6)
        # We are expecting at least the one network from initialization
        self.assertTrue(len(result['rows'][0]) == 6)

    def test_dns_basic(self):
        pass

   

    def tearDown(self):
        pass