.. _module-minica:

minica
======

    
list
^^^^

View all CA servers

remove_server
^^^^^^^^^^^^^

Delete a CA server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

add_server
^^^^^^^^^^

Add a CA server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "fqdn","TEXT"
    "ip_addr","IP"

get_server
^^^^^^^^^^

Get info on a CA server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

generate_host_cert
^^^^^^^^^^^^^^^^^^

Generate a key and signed certificate

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"
    "fqdn","TEXT"

get_ca_cert
^^^^^^^^^^^

Get a server's CA cert

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"
    "type","TEXT"

start_server
^^^^^^^^^^^^

Start a CA server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

stop_server
^^^^^^^^^^^

Stop a CA server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

