import unittest
import os
import sys
import time
import docker
from pylxd import Client
import requests

from constants import *

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parentdir)

from lib.util import clean_ovs, convert_ovs_table
from lib.module_manager import ModuleManager
import lib.validate

class ModuleTestBase():

    module_name = "INVALID"
    module_type = "docker"

    def load_mm(self):
        

        if TEST_WEB_VAR in os.environ and os.environ[TEST_WEB_VAR] != "":
            self.mm = ModuleManager(ip=os.environ[TEST_WEB_VAR])
        else:
            self.mm = ModuleManager()
        self.mm.load()
        self.mm[self.module_name].check()

    def do_test_basic_functionality(self, server_id):
        raise NotImplementedError

    def create_server(self):
        raise NotImplementedError

    def remove_server(self, server_id):
        raise NotImplementedError

    def stop_server(self, server_id):
        raise NotImplementedError

    def test_basic_functionality(self):
        time.sleep(30)
        server_id = self.create_server()
        data = self.mm[self.module_name].get_list()
        to_find = 1
        if type(server_id) is tuple:
            to_find = len(server_id)
        found = 0
        for item in data:
            self.assertTrue(item[0] == self.module_name)
            self.assertTrue(len(item) == 5, msg=item)
            if type(server_id) is tuple:
                if item[1] in server_id:
                    found += 1
            elif item[1] == server_id:
                found = 1

        self.assertTrue(found==to_find)

        self.do_test_basic_functionality(server_id)
        self.remove_server(server_id)

    def test_save_restore(self):
        time.sleep(30)
        server_id = self.create_server()
        self.do_test_basic_functionality(server_id)
        save_data = self.mm[self.module_name].save()
        self.stop_server(server_id)
        self.mm[self.module_name].restore(save_data)
        self.do_test_basic_functionality(server_id)
        self.remove_server(server_id)


    def _requests_fail(self, url):
        message = "Failed to connect to URL {}".format(url)
        if self.module_type == "docker":
            self.fail(msg=self.dump_docker_info(message))
        elif self.module_type == "lxd":
            self.fail(msg=self.dump_lxd_info(message))

    def do_requests_get(self, url, **kwarg):
        try:
            resp = requests.get(url, **kwarg)
            return resp
        except requests.exceptions.ConnectionError:
            self._requests_fail(url)

    def do_requests_post(self, url, **kwarg):
        try:
            resp = requests.post(url, **kwarg)
            return resp
        except requests.exceptions.ConnectionError:
            self._requests_fail( url)

    def _dump_docker_general(self):
        if not os.path.exists("./testlogs"):
            os.mkdir("./testlogs")

        client = docker.from_env()

        # Dump Docker info
        all_cont = client.containers.list(all=True)
        cont_list = []

        cont_output = ""

        for container in all_cont:
            cont_output += "{} ({}) = {}\n\n".format(container.name, container.image, container.status)

            status, output = container.exec_run("cat /proc/net/fib_trie")
            if status == 0:
                output = output.decode()
                output_split = output.split("Local:")
                cont_output += output_split[0] + "\n"

            cont_output += "\n\n"

            log_data = container.logs()
            log_file = open("./testlogs/{}-{}-dockerlogs.log".format(self.module_name, container.name), "wb+")
            log_file.write(log_data)
            log_file.close()

        log_file = open("./testlogs/{}-dockerstate.log".format(self.module_name), "w+")
        log_file.write(cont_output)
        log_file.close()    

    def dump_lxd_info(self, message):
        if not os.path.exists("./testlogs"):
            os.mkdir("./testlogs")

        self._dump_docker_general() 

        lxd = Client()

        cont_output = ""

        all_containers = lxd.containers.all()
        for container in all_containers:
            try:
                container.sync()
            except pylxd.exceptions.NotFound:
                cont_output += "{} = NOT FOUND".format(container.name)
                cont_output += "\n\n"
                continue
            cont_output += "{} = {}\n\n".format(container.name, container.state().status)

            if container.state().status.lower() == "running":


                status, stdout, stderr = container.execute(["cat", "/proc/net/fib_trie"])
                if status == 0:
                    # output = stdout.decode()
                    output = stdout
                    output_split = output.split("Local:")
                    cont_output += output_split[0] + "\n"
            else:
                cont_output += "NOT RUNNING\n"

            cont_output += "\n\n"

        log_file = open("./testlogs/{}-lxdstate.log".format(self.module_name), "w+")
        log_file.write(cont_output)
        log_file.close()   


        return message


    def dump_docker_info(self, message):
        if not os.path.exists("./testlogs"):
            os.mkdir("./testlogs")

        client = docker.from_env()

        self._dump_docker_general()
                
        return message
