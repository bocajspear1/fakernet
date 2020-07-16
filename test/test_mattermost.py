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

class TestInspircd(unittest.TestCase):

    def setUp(self):
        self.mm = ModuleManager()
        self.mm.load()
        self.mm['mattermost'].check()

    def test_mattermost(self):
        server_ip = '172.16.3.170'
        domain_name = 'mattermost.test'
        error, server_id = self.mm['mattermost'].run("add_server", ip_addr=server_ip, fqdn=domain_name)
        self.assertTrue(error == None, msg=error)

        time.sleep(120)


        # error, _ = self.mm['mattermost'].run("remove_server", id=server_1_id)
        # self.assertTrue(error == None, msg=error)

