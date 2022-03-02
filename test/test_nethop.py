import unittest
import os
import sys
import subprocess
import json
import dns.resolver
import time

from constants import *
from module_test_base import ModuleTestBase

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parentdir)

import docker
import pylxd

from lib.util import clean_ovs, convert_ovs_table
from lib.module_manager import ModuleManager
import lib.validate

class TestNetworkHop(ModuleTestBase, unittest.TestCase):

    def setUp(self):
        self.module_name = 'nethop'
        self.module_type = 'lxd'
        self.load_mm()

        commands = [
            'config t',
            'router rip',
            'no network testnet0',
            'write mem',
            'no router rip',
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

    def stop_server(self, server_ids):
        for server_id in server_ids:
            error, _ = self.mm[self.module_name].run("stop_hop", id=server_id)
            self.assertTrue(error == None, msg=error)
            time.sleep(5)

    def create_server(self):
        error, hop1_id = self.mm['nethop'].run("add_network_hop", front_ip='172.16.3.160', fqdn='net2.test', net_addr='192.168.200.0/24', switch='testnet1', description='test')
        self.assertTrue(error == None, msg=self.dump_lxd_info(error))

        time.sleep(60)

        error, hop2_id = self.mm['nethop'].run("add_network_hop", front_ip='192.168.200.10', fqdn='net3.test', net_addr='192.168.100.0/24', switch='testnet2', description='test2')
        self.assertTrue(error == None, msg=self.dump_lxd_info(error))

        # Wait for RIP to settle
        time.sleep(60)

        return (hop1_id, hop2_id)

    def remove_server(self, server_ids):
        for server_id in server_ids:
            error, _ = self.mm[self.module_name].run("remove_network_hop", id=server_id)
            self.assertTrue(error == None, msg=self.dump_lxd_info(error))
            time.sleep(5)

    def do_test_basic_functionality(self, server_id):
        traceroute = subprocess.check_output(["/usr/sbin/traceroute", '-n', '192.168.100.1']).decode().strip()

        traceroute_split = traceroute.split("\n")

        # self.assertTrue(len(traceroute_split) == 3, msg=self.dump_lxd_info(str(traceroute_split)))

        error, cont_id = self.mm['lxd'].run("add_container", ip_addr='192.168.100.100', fqdn='lxd-hop.test', template='ubuntu_1804_base', password='testtest')
        self.assertTrue(error == None, msg=self.dump_lxd_info(error))

        subprocess.check_output(["/bin/ping", '-c', '2', '192.168.100.100'])

        traceroute = subprocess.check_output(["/usr/sbin/traceroute", '-n', '192.168.100.100']).decode().strip()

        traceroute_split = traceroute.split("\n")

        # self.assertTrue(len(traceroute_split) == 4, msg=self.dump_lxd_info(str(traceroute_split)))