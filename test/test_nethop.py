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

import docker
import pylxd

from lib.util import clean_ovs, convert_ovs_table
from lib.module_manager import ModuleManager
import lib.validate

class TestNetworkHop(unittest.TestCase):

    def setUp(self):
        self.mm = ModuleManager()
        self.mm.load()
        self.mm['nethop'].check()

    def test_add_nethop(self):
        error, result = self.mm['nethop'].run("add_network_hop", front_ip='172.16.3.150', fqdn='net2.test', net_addr='192.168.200.0/24', switch='testnet1', description='test')
        self.assertTrue(error == None, msg=error)

        error, result = self.mm['nethop'].run("add_network_hop", front_ip='192.168.200.10', fqdn='net3.test', net_addr='192.168.100.0/24', switch='testnet2', description='test2')
        self.assertTrue(error == None, msg=error)

        # Wait for RIP to settle
        time.sleep(30)

        traceroute = subprocess.check_output(["/usr/sbin/traceroute", '-n', '192.168.100.1']).decode().strip()

        traceroute_split = traceroute.split("\n")

        self.assertTrue(len(traceroute_split) == 3, msg=str(traceroute_split))

        error, cont_id = self.mm['lxd'].run("add_container", ip_addr='192.168.100.100', fqdn='lxd-hop.test', template='ubuntu_1804_base', password='testtest')
        self.assertTrue(error == None, msg=error)

        subprocess.check_output(["/bin/ping", '-c', '2', '192.168.100.100'])

        traceroute = subprocess.check_output(["/usr/sbin/traceroute", '-n', '192.168.100.100']).decode().strip()

        traceroute_split = traceroute.split("\n")

        self.assertTrue(len(traceroute_split) == 4, msg=str(traceroute_split))

        error, result = self.mm['lxd'].run("remove_container", id=cont_id)
        self.assertTrue(error == None, msg=error)
        