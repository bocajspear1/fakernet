

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

class TestTinyproxy(unittest.TestCase):

    def setUp(self):
        self.mm = ModuleManager()
        self.mm.load()
        self.mm['tinyproxy'].check()

    def test_tinyproxy(self):
        proxy_ip = '172.16.3.175'
        domain_name = 'proxy.test'
        error, new_proxy_id = self.mm['tinyproxy'].run("add_server", ip_addr=proxy_ip, fqdn=domain_name)
        self.assertTrue(error == None, msg=error)

        time.sleep(5)

        proxies = {
            'http': 'http://{}:8080'.format(proxy_ip),
            'https': 'http://{}:8080'.format(proxy_ip),
        }

        res = requests.get("http://httpforever.com/", proxies=proxies)
        self.assertTrue(res.status_code == 200, msg="{}: \n{}".format(res.status_code, res.text))

        res = requests.get("https://google.com/", proxies=proxies)
        self.assertTrue(res.status_code == 200, msg="{}: \n{}".format(res.status_code, res.text))

        error, _ = self.mm['tinyproxy'].run("remove_server", id=new_proxy_id)
        self.assertTrue(error is None, msg=error)