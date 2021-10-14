import unittest
import os
import sys
import subprocess
import json

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parentdir)


from lib.util import clean_ovs, convert_ovs_table
from lib.base_module import BaseModule
import lib.validate

class TestParam(BaseModule):
    pass

class TestParams(unittest.TestCase):

    def setUp(self):
        self.module = TestParam()

    def run_test(self, idef, valids, invalids):
        for valid in valids:
            error, result = self.module.validate_params(idef,
            {
                "test": valid
            }
            )
            self.assertTrue(error==None, msg=error)

        for invalid in invalids:
            error, result = self.module.validate_params(idef,
            {
                "test": invalid
            }
            )
            self.assertTrue(error!=None, msg="'{} did not fail".format(invalid))


    def test_ints(self):
        idef = {
            "test": "INTEGER"
        }
        valids = ['0', '1', '9090', '10000', '451230']
        invalids = ['a', ',./', '1.kih', '*)123ADSF', 'm4po4tnqj;rntiw\'neotniw']
        self.run_test(idef, valids, invalids)
    
    def test_text(self):
        idef = {
            "test": "TEXT"
        }
        valids = ['asdf', 'This is a thing, yes it is.', ',./', '9090']
        invalids = ['<>?', '1.kih;', '*)123ADSF', 'm4po4tnqj;rntiw\'neotniw']

        self.run_test(idef, valids, invalids)

    def test_ip(self):
        idef = {
            "test": "IP"
        }
        valids = ['1.1.1.1', '3.2.55.1', '123.123.123.123']
        invalids = ['<>?', ',./', '1.kih;', '*)123ADSF', 'm4po4tnqj;rntiw\'neotniw', '1.a.2.3', 'aaa.aaa.aaa.aaa']

        self.run_test(idef, valids, invalids)
    
    def test_ipnetwork(self):
        idef = {
            "test": "IP_NETWORK"
        }
        valids = ['1.1.1.1/23', '3.2.55.1/8', '123.123.123.123/22']
        invalids = ['<>?', ',./', '1.kih;', '*)123ADSF', '1.1.1.1', '1.a.2.3', 'aaa.aaa.aaa.aaa', '1.2.3.4/', '1.2.3.4/a']
        self.run_test(idef, valids, invalids)
        

    def test_boolean(self):
        idef = {
            "test": "BOOLEAN"
        }
        valids = ['true', 'false']
        invalids = ['<>?', ',./', '1.kih;', '*)123ADSF', '1.1.1.1', '1.a.2.3', 'aaa.aaa.aaa.aaa', '1.2.3.4/', '1.2.3.4/a', 'f1slse']
        self.run_test(idef, valids, invalids)

    def test_simple_string(self):
        idef = {
            "test": "SIMPLE_STRING"
        }
        valids = ['true', 'false', '1a1', 'abc', 'eth0']
        invalids = ['<>?', ',./', '1.kih;', '*)123ADSF', '1.1.1.1', '1.a.2.3', 'aaa.aaa.aaa.aaa', '1.2.3.4/', '1.2.3.4/a']
        self.run_test(idef, valids, invalids)

    def test_decimal(self):
        idef = {
            "test": "DECIMAL"
        }
        valids = ['1.1', '1', '6.123123123']
        invalids = ['<>?', ',./', '1.kih;', '*)123ADSF', '1.1.1.1', '1.a.2.3', 'aaa.aaa.aaa.aaa', '1.2.3.4/', '1.2.3.4/a']
        self.run_test(idef, valids, invalids)

    def test_list(self):
        idef = {
            "test": ["one", "two"]
        }
        valids = ['one', "two"]
        invalids = ['three', 'to', '<>?', ',./', '1.kih;', '*)123ADSF', '1.1.1.1', '1.a.2.3', 'aaa.aaa.aaa.aaa', '1.2.3.4/', '1.2.3.4/a']
        self.run_test(idef, valids, invalids)
        