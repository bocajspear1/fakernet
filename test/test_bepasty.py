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

import smtplib
import imaplib
import requests

class TestBepasty(unittest.TestCase):

    def setUp(self):
        self.mm = ModuleManager()
        self.mm.load()
        self.mm['simplemail'].check()

    def test_simplemail(self):
        server_1_ip = '172.16.3.130'
        error, server_id = self.mm['pastebin-bepasty'].run("add_server", ip_addr=server_1_ip, fqdn='pastebin.test')
        self.assertTrue(error == None, msg=error)

        time.sleep(3)
        data = {
            "text": "test_data",
            "contenttype": "",
            "filename": "this_is_a_test2",
            "maxlife-value": "1",
            "maxlife-unit": "months"
        }
     
        url_test = "https://172.16.3.130/+upload"
        resp = requests.post(url_test, data=data, verify=False) 

        self.assertTrue(resp.status_code == 200)
        # Ensure we got redirected
        self.assertTrue(resp.url != url_test)

        url_split = str(resp.url).split("/")
        last = url_split[len(url_split)-1]
        name = last.split("#")[0]

        full_path = parentdir + "/work/pastebin-bepasty/1/storage/{}.meta".format(name)
        self.assertTrue(os.path.exists(full_path), msg="{} does not exist".format(full_path))

        error, _ = self.mm['pastebin-bepasty'].run("stop_server", id=server_id)
        time.sleep(2)
        error, _ = self.mm['pastebin-bepasty'].run("start_server", id=server_id)

        resp = requests.get("https://172.16.3.130/{}/+inline".format(name), verify=False) 
        self.assertTrue(resp.status_code == 200)

        error, server_id = self.mm['pastebin-bepasty'].run("remove_server", id=server_id)
        self.assertTrue(error == None, msg=error)


