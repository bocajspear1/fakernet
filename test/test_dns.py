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

import docker
import pylxd

from lib.util import clean_ovs, convert_ovs_table
from lib.module_manager import ModuleManager
import lib.validate

class TestDNS(unittest.TestCase):

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
        error, _ = self.mm['dns'].run("add_host", fqdn="host1.test", ip_addr='172.16.3.20')
        self.assertTrue(error == None, msg=error)

        root_resolver = dns.resolver.Resolver()
        root_resolver.nameservers = [TEST_DNS_ROOT]

        answers = root_resolver.query('ns1.test', 'A')
        self.assertTrue(answers is not None)
        for resp in answers.response.answer:
            for item in resp.items:
                self.assertTrue(TEST_DNS_ROOT == item.to_text(), msg=item)
            
        answers = root_resolver.query('host1.test', 'A')
        self.assertTrue(answers is not None)
        for resp in answers.response.answer:
            for item in resp.items:
                self.assertTrue('172.16.3.20' == item.to_text(), msg=item)

        error, _ = self.mm['dns'].run("add_host", fqdn="host2.test", ip_addr='172.16.3.21')
        self.assertTrue(error == None, msg=error)

        answers = root_resolver.query('host2.test', 'A')
        self.assertTrue(answers is not None)
        for resp in answers.response.answer:
            for item in resp.items:
                self.assertTrue('172.16.3.21' == item.to_text(), msg=item)

        error, _ = self.mm['dns'].run("remove_host", fqdn="host1.test", ip_addr='172.16.3.20')
        self.assertTrue(error == None, msg=error)

        try:
            answers = root_resolver.query('host1.test', 'A')
            self.fail()
        except dns.resolver.NXDOMAIN: 
            pass
        except dns.exception.Timeout:
            pass

        error, _ = self.mm['dns'].run("remove_host", fqdn="host2.test", ip_addr='172.16.3.21')
        self.assertTrue(error == None, msg=error)

        try:
            answers = root_resolver.query('host2.test', 'A')
            self.fail()
        except dns.resolver.NXDOMAIN: 
            pass
        except dns.exception.Timeout:
            pass

    def test_dns_override(self):
        error, _ = self.mm['dns'].run("add_override", fqdn="example.com", ip_addr='172.16.3.50')
        self.assertTrue(error == None, msg=error)

        time.sleep(20)

        root_resolver = dns.resolver.Resolver()
        root_resolver.nameservers = [TEST_DNS_ROOT]

        answers = root_resolver.query('ns1.test', 'A')
        self.assertTrue(answers is not None)
        for resp in answers.response.answer:
            for item in resp.items:
                self.assertTrue(TEST_DNS_ROOT == item.to_text(), msg=item)
            
        answers = root_resolver.query('example.com', 'A')
        self.assertTrue(answers is not None)
        for resp in answers.response.answer:
            for item in resp.items:
                self.assertTrue('172.16.3.50' == item.to_text(), msg=item)

        error, _ = self.mm['dns'].run("remove_override", fqdn="example.com", ip_addr='172.16.3.50')
        self.assertTrue(error == None, msg=error)

        time.sleep(20)

        answers = root_resolver.query('example.com', 'A')
        self.assertTrue(answers is not None)
        for resp in answers.response.answer:
            for item in resp.items:
                self.assertFalse('172.16.3.50' == item.to_text(), msg=item)

    def test_dns_external_subdomain(self):

        SECOND_IP = '172.16.3.41'

        error, _ = self.mm['dns'].run("smart_add_external_subdomain", fqdn="subdomain.test", ip_addr=SECOND_IP)
        self.assertTrue(error == None, msg=error)

        error, server_id = self.mm['dns'].run("add_server", ip_addr=SECOND_IP, description="test_dns2", domain="subdomain.test")
        self.assertTrue(error == None)
        error, result = self.mm['dns'].run("add_zone", id=server_id, direction="fwd", zone="subdomain.test")
        self.assertTrue(error == None)
        error, result = self.mm['dns'].run("add_forwarder", id=server_id, ip_addr=TEST_DNS_ROOT)
        self.assertTrue(error == None)

        time.sleep(20)

        root_resolver = dns.resolver.Resolver()
        root_resolver.nameservers = [TEST_DNS_ROOT]

        answers = root_resolver.query('ns1.subdomain.test', 'A')
        self.assertTrue(answers is not None)
        for resp in answers.response.answer:
            for item in resp.items:
                self.assertTrue(SECOND_IP == item.to_text(), msg=item)

        error, _ = self.mm['dns'].run("remove_server", id=server_id)
        self.assertTrue(error == None, msg=error)

        error, _ = self.mm['dns'].run("smart_remove_external_subdomain", fqdn="subdomain.test", ip_addr=SECOND_IP)
        self.assertTrue(error == None, msg=error)

        time.sleep(20)

        try:
            answers = root_resolver.query('subdomain.test', 'NS')
            self.fail()
        except dns.resolver.NXDOMAIN: 
            pass
        except dns.exception.Timeout:
            pass
        except dns.resolver.NoAnswer:
            pass

    # @unittest.skip("long...")
    def test_dns_smart_subdomain(self):
        error, server_1_id = self.mm['dns'].run("smart_add_subdomain_server", fqdn="domain.test", ip_addr='172.16.3.10')
        self.assertTrue(error == None, msg=error)

        time.sleep(20)

        root_resolver = dns.resolver.Resolver()
        root_resolver.nameservers = [TEST_DNS_ROOT]
        root_resolver.timeout = 10.0
        root_resolver.lifetime = 10.0
        root_resolver.edns = True

        try:
            root_resolver.query('ns1.domain.test', 'A')
        except Exception as e:
            print(e)
            pass
        answers = root_resolver.query('ns1.domain.test', 'A')
        self.assertTrue(answers is not None)
        for resp in answers.response.answer:
            for item in resp.items:
                self.assertTrue('172.16.3.10' == item.to_text(), msg=item)

        error, _ = self.mm['dns'].run("add_host", fqdn="host1.domain.test", ip_addr='172.16.3.200')
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

    # @unittest.skip("long...")
    def test_dns_smart_root(self):
        root_ip_addr = '172.16.3.12'
        error, server_1_id = self.mm['dns'].run("smart_add_root_server", root_name="com", ip_addr=root_ip_addr)
        self.assertTrue(error == None, msg=error)

        time.sleep(20)

        root_resolver = dns.resolver.Resolver()
        root_resolver.nameservers = [TEST_DNS_ROOT]

        answers = root_resolver.query('ns1.com', 'A')
        self.assertTrue(answers is not None)
        for resp in answers.response.answer:
            for item in resp.items:
                self.assertTrue(root_ip_addr == item.to_text(), msg=item)

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