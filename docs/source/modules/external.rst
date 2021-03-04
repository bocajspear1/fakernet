.. _module-external:

external
========

    
list_hosts
^^^^^^^^^^

View external hosts

list_networks
^^^^^^^^^^^^^

View external networks

add_external_host
^^^^^^^^^^^^^^^^^

Add an external host

..  csv-table:: Parameters
    :header: "Name", "Type"

    "fqdn","TEXT"
    "ip_addr","IP"
    "host_desc","TEXT"

remove_external_host
^^^^^^^^^^^^^^^^^^^^

Remove an external host

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

add_external_network
^^^^^^^^^^^^^^^^^^^^

Add an external network (wrapper for netreserve)

..  csv-table:: Parameters
    :header: "Name", "Type"

    "net_addr","IP_NETWORK"
    "description","TEXT"

remove_external_network
^^^^^^^^^^^^^^^^^^^^^^^

Remove an external network (wrapper for netreserve)

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

