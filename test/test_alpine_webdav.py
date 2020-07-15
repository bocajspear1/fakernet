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
from webdav3.client import Client

class TestWebdav(unittest.TestCase):

    def setUp(self):
        self.mm = ModuleManager()
        self.mm.load()
        self.mm['simplemail'].check()

    def test_webdav(self):
        server_1_ip = '172.16.3.140'
        error, server_id = self.mm['webdavalpine'].run("add_server", ip_addr=server_1_ip, fqdn='webdav.test')
        self.assertTrue(error == None, msg=error)

        time.sleep(10)
        webdav_url = "https://172.16.3.140/files/"

        full_path = parentdir + "/work/webdavalpine/1/webdav/admin.pass"
        self.assertTrue(os.path.exists(full_path), msg="{} does not exist".format(full_path))

        admin_pass = open(full_path, "r").read().strip()

        resp = requests.get("https://172.16.3.140/", verify=False)
        self.assertTrue(resp.status_code == 200)

        options = {
            'webdav_hostname': webdav_url,
            'webdav_login':    "admin",
            'webdav_password': admin_pass
        }
        client = Client(options)
        client.verify = False 
        result = client.check("public")
        self.assertTrue(result == True)
        result = client.list()
        self.assertTrue(len(result) > 0)
        subprocess.check_output(["touch /tmp/testdata"], shell=True)
        client.upload_sync("public/testdata", "/tmp/testdata")
        result = client.check("public/testdata")
        self.assertTrue(result == True)

        unauth_client = Client({
            'webdav_hostname': webdav_url
        })

        unauth_client.verify = False
        public_list = unauth_client.list("public/")
        self.assertTrue(len(public_list) > 0)

        try:
            unauth_client.upload_sync("public/testdata2", "/tmp/testdata")
            self.fail()
        except:
            pass

        error, _ = self.mm['webdavalpine'].run("stop_server", id=server_id)
        self.assertTrue(error == None, msg=error)
        time.sleep(2)
        error, _ = self.mm['webdavalpine'].run("start_server", id=server_id)
        self.assertTrue(error == None, msg=error)

        time.sleep(10)

        resp = requests.get("https://172.16.3.140/", verify=False)
        self.assertTrue(resp.status_code == 200)

        options = {
            'webdav_hostname': webdav_url,
            'webdav_login':    "admin",
            'webdav_password': admin_pass
        }
        client2 = Client(options)
        client2.verify = False 
        public_list = client2.list("public/")
        self.assertTrue(len(public_list) > 0)
        self.assertTrue(public_list[1] == "testdata")

        error, _ = self.mm['webdavalpine'].run("remove_server", id=server_id)
        self.assertTrue(error == None, msg=error)


        


