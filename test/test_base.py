import unittest
import os
import sys
import subprocess

from constants import *

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parentdir)

import docker
import pylxd

from lib.util import clean_ovs, remove_all_ovs
from lib.module_manager import ModuleManager
import lib.validate


class TestBasics(unittest.TestCase):

    def setUp(self):
        # Clean the slate!
        self.docker = docker.from_env()
        docker_running = self.docker.containers.list(all=True)
        for cont in docker_running:
            cont.stop()
            cont.remove()

        self.lxd = pylxd.Client()
        lxd_running = self.lxd.containers.all()
        
        for cont in lxd_running:
            if cont.status == "Running":
                cont.stop(wait=True)
            cont.delete()

        clean_ovs()
        remove_all_ovs()

        
        subprocess.run(["/bin/rm", "../fakernet.db"])
        subprocess.run(["/bin/rm", "fakernet.db"])
       
        self.mm = ModuleManager()
        self.mm.load()
        

    def test_build_base(self):
        self.mm['netreserve'].check()
        error, result = self.mm['netreserve'].run("add_network", description="test_network", net_addr="172.16.3.0/24", switch="testnet0")
        self.assertTrue(error == None)

        self.mm['dns'].check()
        error, result = self.mm['dns'].run("add_server", ip_addr=TEST_DNS_ROOT, description="test_dns", domain="test")
        self.assertTrue(error == None)
        error, result = self.mm['dns'].run("add_zone", id=1, direction="fwd", zone="test")
        self.assertTrue(error == None)

        self.mm['minica'].check()
        error, result = self.mm['minica'].run("add_server", fqdn="ca.test", ip_addr="172.16.3.3")
        self.assertTrue(error == None)

        return True

    def tearDown(self):
        pass