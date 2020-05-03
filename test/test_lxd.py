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
        error, cont_id = self.mm['lxd'].run("add_container", ip_addr='172.16.3.150', fqdn='lxd1.test', template='ubuntu_1804_base', password='testtest')
        self.assertTrue(error == None, msg=error)

        subprocess.check_output(["/bin/ping", '-c', '2', '172.16.3.150'])

        error, result = self.mm['lxd'].run("remove_container", id=cont_id)
        self.assertTrue(error == None, msg=error)
        