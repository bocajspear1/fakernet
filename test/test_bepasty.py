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

class TestBepasty(ModuleTestBase, unittest.TestCase):

    def setUp(self):
        self.module_name = 'pastebin-bepasty'
        self.load_mm()
        self.server_1_ip = '172.16.3.130'
        self.server_fqdn = 'pastebin.test'

    def stop_server(self, server_id):
        error, _ = self.mm[self.module_name].run("stop_server", id=server_id)
        self.assertTrue(error == None, msg=error)
        time.sleep(5)

    def create_server(self):
        error, server_id = self.mm[self.module_name].run("add_server", ip_addr=self.server_1_ip, fqdn=self.server_fqdn)
        self.assertTrue(error == None, msg=error)
        time.sleep(30)
        return server_id

    def remove_server(self, server_id):
        error, _ = self.mm[self.module_name].run("remove_server", id=server_id)
        self.assertTrue(error == None, msg=error)

    def do_test_basic_functionality(self, server_id):
        resp = requests.get("https://{}/".format(self.server_fqdn), verify=TEST_CA_PATH)
        self.assertTrue(resp.status_code == 200)

    def test_bepasty(self):
        server_1_ip = '172.16.3.130'
        error, server_id = self.mm['pastebin-bepasty'].run("add_server", ip_addr=server_1_ip, fqdn=self.server_fqdn)
        self.assertTrue(error == None, msg=error)

        time.sleep(10)
        data = {
            "text": "test_data",
            "contenttype": "",
            "filename": "this_is_a_test2",
            "maxlife-value": "1",
            "maxlife-unit": "months"
        }
     
        url_test = "https://{}/+upload".format(self.server_fqdn)
        resp = requests.post(url_test, data=data, verify=TEST_CA_PATH) 

        self.assertTrue(resp.status_code == 200, msg="status was {}".format(resp.status_code))
        # Ensure we got redirected
        self.assertTrue(resp.url != url_test)

        url_split = str(resp.url).split("/")
        last = url_split[len(url_split)-1]
        name = last.split("#")[0]

        full_path = parentdir + "/work/pastebin-bepasty/1/storage/{}.meta".format(name)
        self.assertTrue(os.path.exists(full_path), msg="{} does not exist".format(full_path))

        error, _ = self.mm['pastebin-bepasty'].run("stop_server", id=server_id)
        self.assertTrue(error == None, msg=error)
        time.sleep(2)
        error, _ = self.mm['pastebin-bepasty'].run("start_server", id=server_id)
        self.assertTrue(error == None, msg=error)
        time.sleep(5)

        resp = requests.get("https://{}/{}/+inline".format(self.server_fqdn, name), verify=TEST_CA_PATH) 
        self.assertTrue(resp.status_code == 200)

        error, server_id = self.mm['pastebin-bepasty'].run("remove_server", id=server_id)
        self.assertTrue(error == None, msg=error)


