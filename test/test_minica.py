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

class TestMiniCA(unittest.TestCase):

    def setUp(self):
        self.mm = ModuleManager()
        self.mm.load()
        self.mm['minica'].check()

    def test_minica(self):
        time.sleep(5)
        error, cert_data = self.mm['minica'].run("generate_host_cert", id=1, fqdn="test.test")
        priv_key = cert_data[0]
        cert = cert_data[1]
        print(priv_key, cert)
        
        self.assertTrue(error == None, msg=error)

        outcert = open("/tmp/testcrt.pem", "w+")
        outcert.write(cert)
        outcert.close()


