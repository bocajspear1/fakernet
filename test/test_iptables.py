import unittest
import os
import sys
import subprocess
import json
import dns.resolver
import time

from constants import *

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parentdir)

from lib.util import clean_ovs, convert_ovs_table
from lib.module_manager import ModuleManager
import lib.validate

import socket
import requests

class TestExternal(unittest.TestCase):

    def setUp(self):
        self.mm = ModuleManager()
        self.mm.load()
        self.mm['external'].check()

    def test_iptables_empty(self):
        # Test removing non-existant rule
        error, result = self.mm['iptables'].run("remove_rule", id=200)
        self.assertFalse(error == None, msg=result)

    def test_iptables_set_external(self):

        error, result = self.mm['iptables'].run("set_external_iface", iface="stuff")
        self.assertTrue(error == None, msg=result)

        self.assertTrue(os.path.exists("./work/iptables/ext_iface"))

        test_file = open("./work/iptables/ext_iface", "r")
        self.assertTrue(test_file.read().strip()=="stuff")
        test_file.close()

    def test_iptables_set_nat(self):

        error, result = self.mm['iptables'].run("set_external_iface", iface="eth1")
        self.assertTrue(error == None, msg=result)

        self.assertTrue(os.path.exists("./work/iptables/ext_iface"))

        test_file = open("./work/iptables/ext_iface", "r")
        self.assertTrue(test_file.read().strip()=="eth1")
        test_file.close()

        error, rule_id = self.mm['iptables'].run("add_nat_allow", range="10.10.10.10")
        self.assertTrue(error == None, msg=error)

        try:
            subprocess.check_output(f"sudo iptables -t nat -C POSTROUTING -s 10.10.10.10 -o eth1 -j MASQUERADE -m comment --comment 'FakerNet Iptables rule 1'", shell=True)
        except:
            self.fail()

        self.mm['iptables'].run("remove_rule", id=rule_id)

    def test_iptables_add_raw(self):

        error, rule_id = self.mm['iptables'].run("add_raw", cmd="-s 10.30.30.1 -j ACCEPT ", chain="FORWARD")
        self.assertTrue(error == None, msg=error)

        try:
            subprocess.check_output(f"sudo iptables -C FORWARD -s 10.30.30.1 -j ACCEPT -m comment --comment 'FakerNet Iptables rule 1'", shell=True)
        except:
            self.fail()

        try:
            subprocess.check_output(f"sudo iptables -C FORWARD -s 10.30.30.2 -j ACCEPT -m comment --comment 'FakerNet Iptables rule 1'", shell=True)
            self.fail()
        except:
            pass

        self.mm['iptables'].run("remove_rule", id=rule_id)

    def test_iptables_add_raw_to_able(self):

        error, rule_id = self.mm['iptables'].run("add_raw_to_table", table="nat", cmd="-s 10.30.30.1 -j ACCEPT ", chain="POSTROUTING")
        self.assertTrue(error == None, msg=error)

        try:
            subprocess.check_output(f"sudo iptables -t nat -C POSTROUTING -s 10.30.30.1 -j ACCEPT -m comment --comment 'FakerNet Iptables rule 1'", shell=True)
        except:
            self.fail()

        try:
            subprocess.check_output(f"sudo iptables -t nat -C POSTROUTING -s 10.30.30.2 -j ACCEPT -m comment --comment 'FakerNet Iptables rule 1'", shell=True)
            self.fail()
        except:
            pass

        self.mm['iptables'].run("remove_rule", id=rule_id)

        