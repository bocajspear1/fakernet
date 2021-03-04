.. _module-dns:

dns
===

    
list
^^^^

View all DNS servers

remove_server
^^^^^^^^^^^^^

Delete a DNS server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","IP"

add_server
^^^^^^^^^^

Add a DNS server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "ip_addr","IP"
    "description","TEXT"
    "domain","TEXT"

add_zone
^^^^^^^^

Add a DNS zone

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"
    "zone","TEXT"
    "direction","['fwd', 'rev']"

smart_add_record
^^^^^^^^^^^^^^^^

Add a record to a DNS server, detecting server and zone

..  csv-table:: Parameters
    :header: "Name", "Type"

    "direction","['fwd', 'rev']"
    "type","TEXT"
    "fqdn","TEXT"
    "value","TEXT"
    "autocreate","BOOLEAN"

smart_remove_record
^^^^^^^^^^^^^^^^^^^

Add a record to a DNS server, detecting server and zone

..  csv-table:: Parameters
    :header: "Name", "Type"

    "direction","['fwd', 'rev']"
    "type","TEXT"
    "fqdn","TEXT"
    "value","TEXT"

add_record
^^^^^^^^^^

Add a record to a DNS server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"
    "zone","TEXT"
    "direction","['fwd', 'rev']"
    "type","TEXT"
    "name","TEXT"
    "value","TEXT"

remove_record
^^^^^^^^^^^^^

Remove a record from a DNS server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"
    "zone","TEXT"
    "direction","['fwd', 'rev']"
    "type","TEXT"
    "name","TEXT"
    "value","TEXT"

add_host
^^^^^^^^

Add a host to a DNS server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "fqdn","TEXT"
    "ip_addr","IP_ADDR"

remove_host
^^^^^^^^^^^

Remove a host to a DNS server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "fqdn","TEXT"
    "ip_addr","IP_ADDR"

start_server
^^^^^^^^^^^^

Start a DNS server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

stop_server
^^^^^^^^^^^

Stop a DNS server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

get_server
^^^^^^^^^^

Get info on a DNS server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

list_forwarders
^^^^^^^^^^^^^^^

View forwarders for DNS server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

add_forwarder
^^^^^^^^^^^^^

Add forwarder to DNS server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"
    "ip_addr","IP_ADDR"

remove_forwarder
^^^^^^^^^^^^^^^^

Remove forwarder from DNS server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"
    "ip_addr","IP_ADDR"

smart_add_subdomain_server
^^^^^^^^^^^^^^^^^^^^^^^^^^

Add subdomain server, automatically setting up root server to point to it

..  csv-table:: Parameters
    :header: "Name", "Type"

    "fqdn","TEXT"
    "ip_addr","IP_ADDR"

smart_remove_subdomain_server
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Remove subdomain server, automatically deleting entries in the parent server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

smart_add_root_server
^^^^^^^^^^^^^^^^^^^^^

Add a new root domain server (e.g. .com or .net), automatically setting up root server to point to it

..  csv-table:: Parameters
    :header: "Name", "Type"

    "root_name","TEXT"
    "ip_addr","IP_ADDR"

smart_remove_root_server
^^^^^^^^^^^^^^^^^^^^^^^^

Remove root domain server (e.g. .com or .net), automatically deleting entries in the parent server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

smart_add_external_subdomain
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Add subdomain that points to an external DNS server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "fqdn","TEXT"
    "ip_addr","IP_ADDR"

smart_remove_external_subdomain
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Add subdomain that points to an external DNS server

..  csv-table:: Parameters
    :header: "Name", "Type"

    "fqdn","TEXT"
    "ip_addr","IP_ADDR"

