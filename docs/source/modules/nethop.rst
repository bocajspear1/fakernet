.. _module-nethop:

nethop
======

    
list
^^^^

View network hops

add_network_hop
^^^^^^^^^^^^^^^

Get network reservation info

..  csv-table:: Parameters
    :header: "Name", "Type"

    "front_ip","IP"
    "fqdn","TEXT"
    "net_addr","IP_NETWORK"
    "description","TEXT"
    "switch","TEXT"

remove_network_hop
^^^^^^^^^^^^^^^^^^

Remove a network hop

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

start_hop
^^^^^^^^^



..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

stop_hop
^^^^^^^^



..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

