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

class TestInspircd(ModuleTestBase, unittest.TestCase):

    def setUp(self):
        self.module_name = 'inspircd'
        self.load_mm()
        self.server_1_ip = '172.16.3.180'
        self.domain_name = 'irc.test'

    def stop_server(self, server_id):
        error, _ = self.mm[self.module_name].run("stop_server", id=server_id)
        self.assertTrue(error == None, msg=error)
        time.sleep(5)

    def create_server(self):
        error, server_id = self.mm[self.module_name].run("add_server", ip_addr=self.server_1_ip, fqdn=self.domain_name)
        self.assertTrue(error == None, msg=error)
        return server_id

    def remove_server(self, server_id):
        error, _ = self.mm[self.module_name].run("remove_server", id=server_id)
        self.assertTrue(error == None, msg=error)

    def do_test_basic_functionality(self, server_id):
        time.sleep(10)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.server_1_ip, 6667))
        sock.settimeout(5)
        sockfile = sock.makefile("rw", newline='\r\n')
        first = sockfile.readline()
        self.assertTrue(self.domain_name in first, msg="line was '{}'".format(first))
        second = sockfile.readline()
        self.assertTrue(self.domain_name in second, msg="line was '{}'".format(first))
        sockfile.write("NICK Test\r\nUSER Test 8 x : me\r\n")
        sockfile.flush()
        time.sleep(5)
        third = sockfile.readline()
        self.assertTrue("Welcome" in third, msg="line was '{}'".format(first))
        sock.close()

