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
        self.mm['simplemail'].check()

    def test_inspircd(self):
        server_1_ip = '172.16.3.180'
        domain_name = 'irc.test'
        error, server_1_id = self.mm['inspircd'].run("add_server", ip_addr=server_1_ip, fqdn=domain_name)
        self.assertTrue(error == None, msg=error)

        time.sleep(5)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server_1_ip, 6667))
        sock.settimeout(5)
        sockfile = sock.makefile("rw", newline='\r\n')
        first = sockfile.readline()
        self.assertTrue(domain_name in first, msg="line was '{}'".format(first))
        second = sockfile.readline()
        self.assertTrue(domain_name in second, msg="line was '{}'".format(first))
        sockfile.write("NICK Test\r\nUSER Test 8 x : me\r\n")
        sockfile.flush()
        time.sleep(5)
        third = sockfile.readline()
        self.assertTrue("Welcome" in third, msg="line was '{}'".format(first))
        sock.close()

        error, _ = self.mm['inspircd'].run("remove_server", id=server_1_id)
        self.assertTrue(error == None, msg=error)

