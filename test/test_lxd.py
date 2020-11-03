import unittest
import os
import sys
import subprocess
import json
import dns.resolver

from constants import *

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parentdir)

import docker
import pylxd

from lib.util import clean_ovs, convert_ovs_table
from lib.module_manager import ModuleManager
import lib.validate

class TestLXD(unittest.TestCase):

    def setUp(self):
        self.mm = ModuleManager()
        self.mm.load()
        self.mm['lxd'].check()

    def test_add_container(self):
        container_fqdn = 'lxd1.test'
        error, cont_id = self.mm['lxd'].run("add_container", ip_addr='172.16.3.150', fqdn=container_fqdn, template='ubuntu_1804_base', password='testtest')
        self.assertTrue(error == None, msg=error)

        subprocess.check_output(["/bin/ping", '-c', '2', '172.16.3.150'])

        lxc_output = subprocess.check_output(["/usr/bin/lxc", 'list']).decode()
        assert container_fqdn.replace(".", "-") in lxc_output

        error, server_list = self.mm.list_all_servers()
        self.assertTrue(error == None, msg=error)
        for item in server_list:
            assert(len(item)==5)
            if item[0] == "lxd":
                assert item[4] == "running" 

        error, _ = self.mm['lxd'].run("remove_container", id=cont_id)
        self.assertTrue(error == None, msg=error)
        