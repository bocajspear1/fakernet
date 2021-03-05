.. _module-external:

external
========

    
This module manages external hosts and networks. These are hosts that are not managed by FakerNet, but you want to use the DNS and IP allocation functionality in FakerNet to connect them to infrastructure. Be sure that the networks allocated can be accessed by the source device, even if they can't access FakerNet.

Usually, you'd use this for external VMs and containers.

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

