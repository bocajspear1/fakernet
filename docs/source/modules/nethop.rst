.. _module-nethop:

nethop
======

    
Nethop creates new networks and sets up a simple Alpine Linux router to act as its gateway. This allows for multi-tiered networks instead of just a flat one.

The router is a LXD container, not a Docker container, and runs Quagga that distributes routes currently by RIPv2.

If routes are having issues being distributed on the host, try restarting the Quagga service first.

See :ref:`param-types` for parameter types.

list
^^^^

View network hops

add_network_hop
^^^^^^^^^^^^^^^

Add a network hop

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

Start a hop router between networks

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

stop_hop
^^^^^^^^

Stop a hop router between networks. Will cut off communications.

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

