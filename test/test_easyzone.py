import unittest
import os
import sys
import subprocess
import json
import dns.resolver

from constants import *

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parentdir)

import lib.easyzone as easyzone

class TestEasyZone(unittest.TestCase):


    def test_easyzone(self):
        zone_file = easyzone.zone_from_file("test", "./test/testzone")
        zone_file.save(autoserial=True)
   

    def tearDown(self):
        pass