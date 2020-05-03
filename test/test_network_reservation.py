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
        self.mm['netreserve'].check()

    def test_network_list(self):
        error, result = self.mm['netreserve'].run("list")
        self.assertTrue(error == None)
        self.assertTrue(len(result['columns']) == 5)
        # We are expecting at least the one network from initialization
        self.assertTrue(len(result['rows'][0]) == 5)

    def test_add_remove_network(self):
        bridge_1 = "testnet1"
        bridge_2 = "testnet2"
        error, result_id = self.mm['netreserve'].run("add_network", description="Temp test network", net_addr="172.16.4.0/24", switch=bridge_1)
        self.assertTrue(error == None)
        error, _ = self.mm['netreserve'].run("add_network", description="Temp test network 2", net_addr="172.16.4.0/24", switch=bridge_2)
        self.assertFalse(error == None)
        error, _ = self.mm['netreserve'].run("add_network", description="Temp test network", net_addr="172.16.5.0/24", switch=bridge_1)
        self.assertFalse(error == None)
        error, result_id_2 = self.mm['netreserve'].run("add_network", description="Temp test network 2", net_addr="172.16.5.0/24", switch=bridge_2)
        self.assertTrue(error == None)

        output = subprocess.check_output(["/usr/bin/sudo", "/usr/bin/ovs-vsctl", "-f", "json", "list", "bridge"]).decode()
        bridge_list = json.loads(output)
        bridge_data = convert_ovs_table(bridge_list)

        found_1 = False
        found_2 = False
        for bridge in bridge_data:
            if bridge['name'] == bridge_1:
                found_1 = True
            elif bridge['name'] == bridge_2:
                found_2 = True
        
        self.assertTrue(found_1)
        self.assertTrue(found_2)

        error, _ = self.mm['netreserve'].run("remove_network", id=result_id)
        self.assertTrue(error == None)
        error, _ = self.mm['netreserve'].run("remove_network", id=result_id_2)
        self.assertTrue(error == None)

   

    def tearDown(self):
        pass