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

import smtplib
import imaplib
import requests

class TestSimpleMail(ModuleTestBase, unittest.TestCase):

    def setUp(self):
        self.module_name = 'simplemail'
        self.load_mm()
        self.server_1_ip = '172.16.3.170'
        self.username_1 = "testme@mail1.test"
        self.password_1 = "testtest"
        self.dns_1 = 'mail1.test' 

    def stop_server(self, server_id):
        error, _ = self.mm[self.module_name].run("stop_server", id=server_id)
        self.assertTrue(error == None, msg=error)
        time.sleep(5)

    def create_server(self):
        error, server_id = self.mm[self.module_name].run("add_server", ip_addr=self.server_1_ip, fqdn=self.dns_1, mail_domain='mail1.test')
        self.assertTrue(error == None, msg=error)
        time.sleep(25)

        resp = requests.post("https://"+self.dns_1+"/newaccount.php", data={
            "username": self.username_1,
            "password": self.password_1
        }, verify=TEST_CA_PATH)
        self.assertTrue(resp.status_code == 200)

        return server_id

    def do_test_basic_functionality(self, server_id):
        time.sleep(15)
        smtp_sender = smtplib.SMTP(self.dns_1)
        smtp_sender.starttls()
        smtp_sender.login(user=self.username_1, password=self.password_1)
        smtp_sender.close()

        imap = imaplib.IMAP4_SSL(self.dns_1)
        imap.login(self.username_1, self.password_1)
        imap.select('Inbox')
        imap.close()


    def remove_server(self, server_id):
        error, _ = self.mm[self.module_name].run("remove_server", id=server_id)
        self.assertTrue(error == None, msg=error)

    def test_simplemail(self):
        error, server_1_id = self.mm[self.module_name].run("add_server", ip_addr=self.server_1_ip, fqdn='mail1.test', mail_domain='mail1.test')
        self.assertTrue(error == None, msg=error)

        time.sleep(12)

        username1 = "test1@mail1.test"
        password = "testtest"

        resp = requests.post("https://"+self.dns_1+"/newaccount.php", data={
            "username": username1,
            "password": password
        }, verify=TEST_CA_PATH)
        self.assertTrue(resp.status_code == 200)

        username2 = "test2@mail1.test"

        resp = requests.post("https://"+self.dns_1+"/newaccount.php", data={
            "username": username2,
            "password": password
        }, verify=TEST_CA_PATH)
        self.assertTrue(resp.status_code == 200)


        smtp_sender = smtplib.SMTP(self.server_1_ip)

        # Check for unauthenticated SMTP
        try:
            smtp_sender.sendmail(username1, [username2], "This is a message!")
            self.fail()
        except:
            pass 
        
        smtp_sender.starttls()
        try:
            smtp_sender.sendmail(username1, [username2], "This is a message!")
            self.fail()
        except:
            pass 

        smtp_sender.login(user=username1, password=password)
        
        smtp_sender.sendmail(username1, [username2], "Subject: SMTP e-mail test\n\nThis is a message!")

        time.sleep(30)
        # connect to host using SSL
        imap = imaplib.IMAP4_SSL(self.dns_1)

        ## login to server
        imap.login(username2, password)

        imap.select('Inbox')

        tmp, data = imap.search(None, 'ALL')
        id_list = data[0].split()
        self.assertTrue(len(id_list) == 1, msg=str(id_list))
        for num in id_list:
            tmp, data = imap.fetch(num, '(RFC822)')
            self.assertTrue(data is not None)

        imap.close()
        smtp_sender.close()
        error, _ = self.mm['simplemail'].run("remove_server", id=server_1_id)
        self.assertTrue(error == None, msg=error)