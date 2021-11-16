.. _module-netreserve:

netreserve
==========

    
See :ref:`param-types` for parameter types.

list
^^^^

View network allocations

get
^^^

Get network reservation info

..  csv-table:: Parameters
    :header: "Name", "Type"

    "ip_id","INT"

add_hop_network
^^^^^^^^^^^^^^^

Add network allocation

..  csv-table:: Parameters
    :header: "Name", "Type"

    "net_addr","IP_NETWORK"
    "description","TEXT"
    "switch","SIMPLE_STRING"

add_network
^^^^^^^^^^^

Add network allocation

..  csv-table:: Parameters
    :header: "Name", "Type"

    "net_addr","IP_NETWORK"
    "description","TEXT"
    "switch","SIMPLE_STRING"

remove_network
^^^^^^^^^^^^^^

Delete a network allocation

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

get_network_switch
^^^^^^^^^^^^^^^^^^

Get the switch for a network

..  csv-table:: Parameters
    :header: "Name", "Type"

    "net_addr","IP_NETWORK"

get_network_by_switch
^^^^^^^^^^^^^^^^^^^^^

Get the switch for a network

..  csv-table:: Parameters
    :header: "Name", "Type"

    "switch","SIMPLE_STRING"

get_ip_switch
^^^^^^^^^^^^^

Get the switch for a network

..  csv-table:: Parameters
    :header: "Name", "Type"

    "ip_addr","IP"

get_ip_network
^^^^^^^^^^^^^^

Get the mask for a network

..  csv-table:: Parameters
    :header: "Name", "Type"

    "ip_addr","IP"

is_hop_network_by_switch
^^^^^^^^^^^^^^^^^^^^^^^^

Check if a network is a hop network (behind a hop router) by switch name

..  csv-table:: Parameters
    :header: "Name", "Type"

    "switch","SIMPLE_STRING"

