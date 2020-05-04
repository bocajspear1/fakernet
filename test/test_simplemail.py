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

from lib.util import clean_ovs, convert_ovs_table
from lib.module_manager import ModuleManager
import lib.validate

import smtplib
import imaplib
import requests

class TestSimpleMail(unittest.TestCase):

    def setUp(self):
        self.mm = ModuleManager()
        self.mm.load()
        self.mm['simplemail'].check()

    def test_simplemail(self):
        server_1_ip = '172.16.3.170'
        error, server_1_id = self.mm['simplemail'].run("add_server", ip_addr=server_1_ip, fqdn='mail1.test', mail_domain='mail1.test')
        self.assertTrue(error == None, msg=error)

        time.sleep(12)

        username1 = "test1@mail1.test"
        password = "testtest"

        resp = requests.post("https://"+server_1_ip+"/newaccount.php", data={
            "username": username1,
            "password": password
        }, verify=False)
        self.assertTrue(resp.status_code == 200)

        username2 = "test2@mail1.test"

        resp = requests.post("https://"+server_1_ip+"/newaccount.php", data={
            "username": username2,
            "password": password
        }, verify=False)
        self.assertTrue(resp.status_code == 200)


        smtp_sender = smtplib.SMTP(server_1_ip)

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
        imap = imaplib.IMAP4_SSL(server_1_ip)

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