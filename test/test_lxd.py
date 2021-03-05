import unittest
import os
import sys
import subprocess
import json
import dns.resolver
import paramiko
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

class TestLXD(ModuleTestBase, unittest.TestCase):

    def setUp(self):
        self.module_name = 'lxd'
        self.load_mm()
        self.server_1_ip = '172.16.3.150'
        self.domain_1_name = 'lxd1.test'
        self.server_2_ip = '172.16.3.151'
        self.domain_2_name = 'lxd2.test'

    def stop_server(self, server_id):
        error, _ = self.mm[self.module_name].run("stop_container", id=server_id)
        self.assertTrue(error == None, msg=error)
        time.sleep(5)
        

    def create_server(self):
        error, server_id = self.mm[self.module_name].run("add_container", ip_addr=self.server_1_ip, fqdn=self.domain_1_name, template='ubuntu_1804_base', password='testtest')
        self.assertTrue(error == None, msg=error)
        time.sleep(10)
        return server_id

    def remove_server(self, server_id):
        error, _ = self.mm[self.module_name].run("remove_container", id=server_id)
        self.assertTrue(error == None, msg=error)

    def can_ssh_to_system(self, target, username, password):
        s = paramiko.SSHClient()
        s.set_missing_host_key_policy(paramiko.client.WarningPolicy)
        s.connect(target, 22, username, password)
        (stdin, stdout, stderr) = s.exec_command("ls /")
        self.assertTrue(stdout.read() != "", msg=stdout)
        s.close()
        return True

    def do_test_basic_functionality(self, server_id):
        time.sleep(10)

        lxc_output = subprocess.check_output(["/usr/bin/lxc", 'list']).decode()
        self.assertTrue(self.domain_1_name.replace(".", "-") in lxc_output, msg=lxc_output)

        error, server_list = self.mm.list_all_servers()
        self.assertTrue(error == None, msg=error)
        for item in server_list:
            assert(len(item)==5)
            if item[0] == "lxd":
                assert item[4] == "running" 

        # subprocess.check_output(["/bin/ping", '-c', '2', self.server_1_ip])

        username = 'root'
        password = 'testtest'

        self.assertTrue(self.can_ssh_to_system(self.server_1_ip, username, password), msg="Could not SSH correctly to {} with creds {}:{}".format(self.server_1_ip, username, password))
        
    def test_add_two_containers(self):
        error, cont_id = self.mm['lxd'].run("add_container", ip_addr=self.server_1_ip, fqdn=self.domain_1_name, template='ubuntu_1804_base', password='testtest')
        self.assertTrue(error == None, msg=error)

        error, cont_id2 = self.mm['lxd'].run("add_container", ip_addr=self.server_2_ip, fqdn=self.domain_2_name, template='ubuntu_1804_base', password='testtest')
        self.assertTrue(error == None, msg=error)

        username = 'root'
        password = 'testtest'

        self.assertTrue(self.can_ssh_to_system(self.server_1_ip, username, password), msg="Could not SSH correctly to {} with creds {}:{}".format(self.server_1_ip, username, password))
        self.assertTrue(self.can_ssh_to_system(self.server_2_ip, username, password), msg="Could not SSH correctly to {} with creds {}:{}".format(self.server_2_ip, username, password))
        

        error, _ = self.mm['lxd'].run("remove_container", id=cont_id2)
        self.assertTrue(error == None, msg=error)

        error, _ = self.mm['lxd'].run("remove_container", id=cont_id)
        self.assertTrue(error == None, msg=error)
        