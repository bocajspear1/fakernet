.. _module-ipreserve:

ipreserve
=========

    
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

