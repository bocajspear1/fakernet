import unittest
import os
import sys
import subprocess
import json
import dns.resolver

from constants import *

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parentdir)

import docker
import pylxd

from lib.util import clean_ovs, convert_ovs_table
from lib.module_manager import ModuleManager
import lib.validate

class TestNetworkReservation(unittest.TestCase):

    def setUp(self):
        self.mm = ModuleManager()
        self.mm.load()
        self.mm['dns'].check()

    def test_dns_list(self):
        error, result = self.mm['dns'].run("list")
        self.assertTrue(error == None)
        self.assertTrue(len(result['columns']) == 6)
        # We are expecting at least the one network from initialization
        self.assertTrue(len(result['rows'][0]) == 6)

    def test_dns_basic(self):
        pass

    @unittest.skip("long...")
    def test_dns_smart_subdomain(self):
        error, server_1_id = self.mm['dns'].run("smart_add_subdomain_server", fqdn="domain.test", ip_addr='172.16.3.10')
        self.assertTrue(error == None, msg=error)

        root_resolver = dns.resolver.Resolver()
        root_resolver.nameservers = [TEST_DNS_ROOT]

        answers = root_resolver.query('ns1.domain.test', 'A')
        self.assertTrue(answers is not None)
        for resp in answers.response.answer:
            for item in resp.items:
                self.assertTrue('172.16.3.10' == item.to_text(), msg=item)

        error, result = self.mm['dns'].run("add_host", fqdn="host1.domain.test", ip_addr='172.16.3.200')
        self.assertTrue(error == None, msg=error)

        answers = root_resolver.query('host1.domain.test', 'A')
        self.assertTrue(answers is not None)
        for resp in answers.response.answer:
            for item in resp.items:
                self.assertTrue('172.16.3.200' == item.to_text(), msg=item)

        error, server_2_id = self.mm['dns'].run("smart_add_subdomain_server", fqdn="subdomain.domain.test", ip_addr='172.16.3.11')
        self.assertTrue(error == None, msg=error)

        error, result = self.mm['dns'].run("add_host", fqdn="host1.subdomain.domain.test", ip_addr='172.16.3.201')
        self.assertTrue(error == None, msg=error)

        answers = root_resolver.query('host1.subdomain.domain.test', 'A')
        self.assertTrue(answers is not None)
        for resp in answers.response.answer:
            for item in resp.items:
                self.assertTrue('172.16.3.201' == item.to_text(), msg=item)

        error, result = self.mm['dns'].run("smart_remove_subdomain_server", id=server_2_id)
        self.assertTrue(error == None, msg=error)

        try:
            answers = root_resolver.query('host1.subdomain.domain.test', 'A')
            self.fail()
        except:
            pass

        error, result = self.mm['dns'].run("smart_remove_subdomain_server", id=server_1_id)
        self.assertTrue(error == None, msg=error)

        try:
            answers = root_resolver.query('host1.domain.test', 'A')
            self.fail()
        except:
            pass

        try:
            answers = root_resolver.query('domain.test', 'NS')
            self.fail()
        except:
            pass

    def test_dns_smart_root(self):
        error, server_1_id = self.mm['dns'].run("smart_add_root_server", root_name="com", ip_addr='172.16.3.10')
        self.assertTrue(error == None, msg=error)

        root_resolver = dns.resolver.Resolver()
        root_resolver.nameservers = [TEST_DNS_ROOT]

        answers = root_resolver.query('ns1.com', 'A')
        self.assertTrue(answers is not None)
        for resp in answers.response.answer:
            for item in resp.items:
                self.assertTrue('172.16.3.10' == item.to_text(), msg=item)

        error, result = self.mm['dns'].run("add_host", fqdn="host1.com", ip_addr='172.16.3.200')
        self.assertTrue(error == None, msg=error)

        answers = root_resolver.query('host1.com', 'A')
        self.assertTrue(answers is not None)
        for resp in answers.response.answer:
            for item in resp.items:
                self.assertTrue('172.16.3.200' == item.to_text(), msg=item)

        error, server_2_id = self.mm['dns'].run("smart_add_subdomain_server", fqdn="domain.com", ip_addr='172.16.3.11')
        self.assertTrue(error == None, msg=error)

        error, result = self.mm['dns'].run("add_host", fqdn="host1.domain.com", ip_addr='172.16.3.201')
        self.assertTrue(error == None, msg=error)

        answers = root_resolver.query('host1.domain.com', 'A')
        self.assertTrue(answers is not None)
        for resp in answers.response.answer:
            for item in resp.items:
                self.assertTrue('172.16.3.201' == item.to_text(), msg=item)

        error, result = self.mm['dns'].run("smart_remove_subdomain_server", id=server_2_id)
        self.assertTrue(error == None, msg=error)

        try:
            answers = root_resolver.query('host1.domain.test', 'A')
            self.fail()
        except:
            pass

        error, result = self.mm['dns'].run("smart_remove_root_server", id=server_1_id)
        self.assertTrue(error == None, msg=error)

        try:
            answers = root_resolver.query('ns1.com', 'A')
            self.fail()
        except:
            pass
   

    def tearDown(self):
        pass