.. _module-simplemail:

simplemail
==========

    
Simplemail is a basic mail server that uses Postfix (for SMTP) and Dovecot (for IMAP). It also contains a webserver that runs Roundcube and a simple PHP application to add more users to the mail server. This does not require and authorization to create the account, so anybody can create one.

The webserver is HTTPS, so access it at:
..  code-block::

    https://<SERVER_IP>


The account creator is available at:
..  code-block::

    https://<SERVER_IP>/newaccount.php


list
^^^^

View all SimpleMail servers

remove_server
^^^^^^^^^^^^^

Delete a SimpleMail server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

add_server
^^^^^^^^^^

Add a SimpleMail server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "fqdn","TEXT"
    "mail_domain","TEXT"
    "ip_addr","IP"

start_server
^^^^^^^^^^^^

Start a SimpleMail server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

stop_server
^^^^^^^^^^^

Start a SimpleMail server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

