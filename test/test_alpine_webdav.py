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

class TestWebdav(unittest.TestCase):

    def setUp(self):
        self.mm = ModuleManager()
        self.mm.load()
        self.mm['simplemail'].check()

    def test_simplemail(self):
        server_1_ip = '172.16.3.140'
        error, server_id = self.mm['webdavalpine'].run("add_server", ip_addr=server_1_ip, fqdn='webdav.test')
        self.assertTrue(error == None, msg=error)

        


