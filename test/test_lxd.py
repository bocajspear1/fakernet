import unittest
import os
import sys
import subprocess
import json
import dns.resolver
import paramiko
import time

from constants import *
from module_test_base import ModuleTestBase

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parentdir)

import docker
import pylxd

from lib.util import clean_ovs, convert_ovs_table
from lib.module_manager import ModuleManager
import lib.validate

class TestLXD(ModuleTestBase, unittest.TestCase):

    def setUp(self):
        self.module_name = 'lxd'
        self.load_mm()
        self.server_1_ip = '172.16.3.150'
        self.domain_1_name = 'lxd1.test'
        self.server_2_ip = '172.16.3.151'
        self.domain_2_name = 'lxd2.test'
        self.server_3_ip = '172.16.3.152'
        self.domain_3_name = 'lxd3.test'

    def stop_server(self, server_id):
        error, _ = self.mm[self.module_name].run("stop_container", id=server_id)
        self.assertTrue(error == None, msg=self.dump_lxd_info(error))
        time.sleep(5)
        

    def create_server(self):
        error, server_id = self.mm[self.module_name].run("add_container", ip_addr=self.server_1_ip, fqdn=self.domain_1_name, template='ubuntu_1804_base', password='testtest')
        self.assertTrue(error == None, msg=self.dump_lxd_info(error))
        time.sleep(10)
        return server_id

    def remove_server(self, server_id):
        error, _ = self.mm[self.module_name].run("remove_container", id=server_id)
        self.assertTrue(error == None, msg=self.dump_lxd_info(error))

    def can_ssh_to_system(self, target, username, password):
        s = paramiko.SSHClient()
        s.set_missing_host_key_policy(paramiko.client.WarningPolicy)
        s.connect(target, 22, username, password)
        (stdin, stdout, stderr) = s.exec_command("ls /")
        self.assertTrue(stdout.read() != "", msg=self.dump_lxd_info(stdout))
        s.close()
        return True

    def do_test_basic_functionality(self, server_id):
        time.sleep(10)

        lxc_output = subprocess.check_output(["/bin/bash", "-c", "lxc list"]).decode()
        self.assertTrue(self.domain_1_name.replace(".", "-") in lxc_output, msg=self.dump_lxd_info(lxc_output))

        error, server_list = self.mm.list_all_servers()
        self.assertTrue(error == None, msg=self.dump_lxd_info(error))
        for item in server_list:
            self.assertTrue(len(item)==5, msg=self.dump_lxd_info(str(item)))
            if item[0] == "lxd":
                 self.assertTrue(item[4] == "running", msg=self.dump_lxd_info("running != {}".format(item[4])))

        # subprocess.check_output(["/bin/ping", '-c', '2', self.server_1_ip])

        username = 'root'
        password = 'testtest'

        self.assertTrue(self.can_ssh_to_system(self.server_1_ip, username, password), msg=self.dump_lxd_info("Could not SSH correctly to {} with creds {}:{}".format(self.server_1_ip, username, password))
    
    def test_templates(self):
        find_template = 'ubuntu_1804_base'
        error, template_list = self.mm['lxd'].run("list_templates")
        self.assertTrue(error == None, msg=self.dump_lxd_info(error))
        self.assertTrue(len(template_list['rows']) > 0, msg=self.dump_lxd_info("list is empty"))
        self.assertTrue(len(template_list['rows'][0]) == 3, msg=self.dump_lxd_info("rows[0] is not 3 long"))
        self.assertTrue(len(template_list['columns']) == 3, msg=self.dump_lxd_info("columns is not 3 long"))

        found = False
        for item in template_list['rows']:
            if item[2] == find_template:
                found = True
        
        self.assertTrue(found)

        error, template_list = self.mm['lxd'].run("remove_template", id=1)
        self.assertTrue(error == None, msg=self.dump_lxd_info(error))

        error, template_list = self.mm['lxd'].run("list_templates")
        self.assertTrue(error == None, msg=self.dump_lxd_info(error))
        found = False
        for item in template_list['rows']:
            if item[2] == find_template:
                found = True
        
        self.assertFalse(found)

        error, template_list = self.mm['lxd'].run("add_template", template_name=find_template, image_name=find_template)
        self.assertTrue(error == None, msg=self.dump_lxd_info(error))

        error, template_list = self.mm['lxd'].run("list_templates")
        self.assertTrue(error == None, msg=self.dump_lxd_info(error))
        found = False
        for item in template_list['rows']:
            if item[2] == find_template:
                found = True

        self.assertTrue(found)


    def test_add_two_containers(self):
        error, cont_id = self.mm['lxd'].run("add_container", ip_addr=self.server_2_ip, fqdn=self.domain_2_name, template='ubuntu_1804_base', password='testtest')
        self.assertTrue(error == None, msg=self.dump_lxd_info(error))

        error, cont_id2 = self.mm['lxd'].run("add_container", ip_addr=self.server_3_ip, fqdn=self.domain_3_name, template='ubuntu_1804_base', password='testtest')
        self.assertTrue(error == None, msg=self.dump_lxd_info(error))

        username = 'root'
        password = 'testtest'

        self.assertTrue(self.can_ssh_to_system(self.server_2_ip, username, password), msg=self.dump_lxd_info("Could not SSH correctly to {} with creds {}:{}".format(self.server_2_ip, username, password)))
        self.assertTrue(self.can_ssh_to_system(self.server_3_ip, username, password), msg=self.dump_lxd_info("Could not SSH correctly to {} with creds {}:{}".format(self.server_3_ip, username, password)))
        

        error, _ = self.mm['lxd'].run("remove_container", id=cont_id2)
        self.assertTrue(error == None, msg=self.dump_lxd_info(error))

        error, _ = self.mm['lxd'].run("remove_container", id=cont_id)
        self.assertTrue(error == None, msg=self.dump_lxd_info(error))
        