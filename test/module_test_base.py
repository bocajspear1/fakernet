import unittest
import os
import sys

from constants import *

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parentdir)

from lib.util import clean_ovs, convert_ovs_table
from lib.module_manager import ModuleManager
import lib.validate

class ModuleTestBase():

    module_name = "INVALID"

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
        server_id = self.create_server()
        data = self.mm[self.module_name].get_list()
        print(data)
        found = False
        for item in data:
            self.assertTrue(item[0] == self.module_name)
            self.assertTrue(len(item) == 5, msg=item)
            if item[1] == server_id:
                found = True

        self.assertTrue(found)

        self.do_test_basic_functionality(server_id)
        self.remove_server(server_id)

    def test_save_restore(self):
        server_id = self.create_server()
        self.do_test_basic_functionality(server_id)
        save_data = self.mm[self.module_name].save()
        self.stop_server(server_id)
        self.mm[self.module_name].restore(save_data)
        self.do_test_basic_functionality(server_id)
        self.remove_server(server_id)