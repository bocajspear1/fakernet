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

        commands = [
            'config t',
            'router rip',
            'no network testnet0',
            'write mem'
        ]

        vtyshPath = subprocess.check_output(["/bin/sh", '-c', 'which vtysh']).strip().decode()
        full_command = [vtyshPath]
        for command in commands:
            full_command += ['-c', command]
        
        try:
            subprocess.check_output(full_command)
        except subprocess.CalledProcessError as e:
            pass

        error, hop1_id = self.mm['nethop'].run("add_network_hop", front_ip='172.16.3.160', fqdn='net2.test', net_addr='192.168.200.0/24', switch='testnet1', description='test')
        self.assertTrue(error == None, msg=error)

        time.sleep(60)

        error, hop2_id = self.mm['nethop'].run("add_network_hop", front_ip='192.168.200.10', fqdn='net3.test', net_addr='192.168.100.0/24', switch='testnet2', description='test2')
        self.assertTrue(error == None, msg=error)

        # Wait for RIP to settle
        time.sleep(60)

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

        error, result = self.mm['nethop'].run("remove_network_hop", id=hop2_id)
        self.assertTrue(error == None, msg=error)

        error, result = self.mm['nethop'].run("remove_network_hop", id=hop1_id)
        self.assertTrue(error == None, msg=error)
        