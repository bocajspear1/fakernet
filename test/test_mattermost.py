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

from lib.util import clean_ovs, convert_ovs_table
from lib.module_manager import ModuleManager
import lib.validate

import socket
import requests

class TestMattermost(ModuleTestBase, unittest.TestCase):

    def setUp(self):
        self.module_name = 'mattermost'
        self.load_mm()
        self.server_1_ip = '172.16.3.170'
        self.domain_1_name = 'mattermost1.test'

    def stop_server(self, server_id):
        error, _ = self.mm[self.module_name].run("stop_server", id=server_id)
        self.assertTrue(error == None, msg=error)
        time.sleep(5)
        
    def create_server(self):
        error, server_id = self.mm[self.module_name].run("add_server", ip_addr=self.server_1_ip, fqdn=self.domain_1_name)
        self.assertTrue(error == None, msg=error)
        time.sleep(30)
        return server_id

    def remove_server(self, server_id):
        error, _ = self.mm[self.module_name].run("remove_server", id=server_id)
        self.assertTrue(error == None, msg=error)

    def do_test_basic_functionality(self, server_id):
        resp = requests.get("https://{}/".format(self.domain_1_name), verify=TEST_CA_PATH)
        self.assertTrue(resp.status_code == 200)


