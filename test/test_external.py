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

    def test_external_empty(self):
        # Test adding host before adding a network
        error, result = self.mm['external'].run("add_external_host", fqdn="whoops.test", ip_addr="192.168.20.2", host_desc="Test")
        self.assertFalse(error == None, msg=result)

        # Test removing non-existant host
        error, result = self.mm['external'].run("remove_external_host", id=200)
        self.assertFalse(error == None, msg=result)

        # # Test removing non-existant host
        error, result = self.mm['external'].run("remove_external_network", id=200)
        self.assertFalse(error == None, msg=result)

    def test_external(self):
        
        # Test empty
        error, host_list = self.mm['external'].run("list_hosts")
        self.assertTrue(error == None, msg=error)
        self.assertTrue(len(host_list['rows']) == 0)
        self.assertTrue(len(host_list['columns']) == 4)
        self.assertTrue("ID" in host_list['columns'])

        error, net_list = self.mm['external'].run("list_networks")
        self.assertTrue(error == None, msg=error)
        self.assertTrue(len(net_list['rows']) == 0)
        self.assertTrue(len(net_list['columns']) == 3)
        self.assertTrue("ID" in net_list['columns'])

        error, network_id = self.mm['external'].run("add_external_network", net_addr="10.10.20.0/24", description="Test External Network")
        self.assertTrue(error == None, msg=error)

        error, host_id = self.mm['external'].run("add_external_host", ip_addr="10.10.20.2", host_desc="Test", fqdn="external1.test")
        self.assertTrue(error == None, msg=error)

        error, host_list = self.mm['external'].run("list_hosts")
        self.assertTrue(error == None, msg=error)
        self.assertTrue(len(host_list['rows']) == 1)
        self.assertTrue("ID" in host_list['columns'])
        self.assertTrue(len(host_list['columns']) == 4)
        self.assertTrue(len(host_list['rows'][0]) == 4)
        self.assertTrue(host_list['rows'][0][0] == host_id, msg=str(host_list['rows']))

        error, net_list = self.mm['external'].run("list_networks")
        self.assertTrue(error == None, msg=error)
        self.assertTrue(len(net_list['rows']) == 1)
        self.assertTrue("ID" in net_list['columns'])
        self.assertTrue(len(net_list['columns']) == 3)
        self.assertTrue(len(net_list['rows'][0]) == 3, msg=str(net_list['rows']))
        self.assertTrue(net_list['rows'][0][0] == network_id, msg=str(net_list['rows']))

        error, network_id2 = self.mm['external'].run("add_external_network", net_addr="10.10.30.0/24", description="Test External Network 2")
        self.assertTrue(error == None, msg=error)

        error, host_id2 = self.mm['external'].run("add_external_host", ip_addr="10.10.30.2", host_desc="Test", fqdn="external2.test")
        self.assertTrue(error == None, msg=error)

        error, _ = self.mm['external'].run("remove_external_host", id=host_id2)
        self.assertTrue(error == None, msg=error)

        error, _ = self.mm['external'].run("remove_external_network", id=network_id2)
        self.assertTrue(error == None, msg=error)

        error, _ = self.mm['external'].run("remove_external_host", id=host_id)
        self.assertTrue(error == None, msg=error)

        error, _ = self.mm['external'].run("remove_external_network", id=network_id)
        self.assertTrue(error == None, msg=error)

        # Test empty
        error, host_list = self.mm['external'].run("list_hosts")
        self.assertTrue(error == None, msg=error)
        self.assertTrue(len(host_list['rows']) == 0)
        self.assertTrue("ID" in host_list['columns'])

        error, net_list = self.mm['external'].run("list_networks")
        self.assertTrue(error == None, msg=error)
        self.assertTrue(len(net_list['rows']) == 0)
        self.assertTrue("ID" in net_list['columns'])

        
        

        

