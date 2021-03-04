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

import smtplib
import imaplib
import requests

class TestPwndrop(ModuleTestBase, unittest.TestCase):

    def setUp(self):
        self.module_name = 'pwndrop'
        self.load_mm()
        self.server_1_ip = '172.16.3.45'

    def stop_server(self, server_id):
        error, _ = self.mm[self.module_name].run("stop_server", id=server_id)
        self.assertTrue(error == None, msg=error)
        time.sleep(5)

    def create_server(self):
        error, server_id = self.mm[self.module_name].run("add_server", ip_addr=self.server_1_ip, fqdn='pwndrop.test')
        self.assertTrue(error == None, msg=error)
        time.sleep(12)
        return server_id

    def remove_server(self, server_id):
        error, _ = self.mm[self.module_name].run("remove_server", id=server_id)
        self.assertTrue(error == None, msg=error)

    def do_test_basic_functionality(self, server_id):
        resp = requests.get("https://{}/pwndrop".format(self.server_1_ip), verify=False)
        self.assertTrue(resp.status_code == 200)
