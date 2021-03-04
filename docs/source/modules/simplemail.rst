.. _module-simplemail:

simplemail
==========

    
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

