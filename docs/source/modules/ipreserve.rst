.. _module-ipreserve:

ipreserve
=========

    
This module manages IP reservations in the defined networks, ensuring that IPs selected do not overlap. 

A network must be defined in ``netreserve`` that contains the IP for a reservation. Otherwise, an error will be returned.

See :ref:`param-types` for parameter types.

list_ips
^^^^^^^^

View IP allocations

get
^^^

Get IP reservation info

..  csv-table:: Parameters
    :header: "Name", "Type"

    "ip_id","INT"

add_ip
^^^^^^

Add an IP reservation

..  csv-table:: Parameters
    :header: "Name", "Type"

    "ip_addr","IP_ADDR"
    "description","TEXT"

remove_ip
^^^^^^^^^

Remove an IP reservation

..  csv-table:: Parameters
    :header: "Name", "Type"

    "ip_addr","IP_ADDR"

