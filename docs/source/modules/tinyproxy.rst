.. _module-tinyproxy:

tinyproxy
=========

    
This module uses the tinyproxy application to provide HTTP proxying capabilities. This could be used for relay internally or, with the proper iptables rules, provide external internet access to select systems in the environment. 

If you allow FakerNet services internet access while blocking certain internal networks, tinyproxy could be used for systems to temporarily gain at least web-based internet access by pointing to the proxy.

See :ref:`param-types` for parameter types.

list
^^^^

View all tinyproxy servers

add_server
^^^^^^^^^^

Add a tinyproxy server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "fqdn","TEXT"
    "ip_addr","IP"

remove_server
^^^^^^^^^^^^^

Delete a tinyproxy server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

start_server
^^^^^^^^^^^^

Start a tinyproxy server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

stop_server
^^^^^^^^^^^

Start a tinyproxy server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

