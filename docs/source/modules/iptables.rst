.. _module-iptables:

iptables
========

    
This module allows management of iptables rules from FakerNet. These rules will always be added when FakerNet starts. This makes it useful for setting up things like NAT. 

..  warning::

    Rules are always added at the top. Use the ``list_order`` to get a better idea of the order the rules will be added.

.. warning:: 
    
    Rules are not removed when FakerNet stops

.. note::

    ``!`` can be used in ``add_nat_allow`` to do a "not" of the range

See :ref:`param-types` for parameter types.

list
^^^^

View iptables rules

list_order
^^^^^^^^^^

View iptables rules in order they will appear (opposite of addition)

show_ifaces
^^^^^^^^^^^

Show configured interfaces

set_external_iface
^^^^^^^^^^^^^^^^^^

Set the external interface (used for NAT)

..  csv-table:: Parameters
    :header: "Name", "Type"

    "iface","SIMPLE_STRING"

set_internal_iface
^^^^^^^^^^^^^^^^^^

Set the internal inferface

..  csv-table:: Parameters
    :header: "Name", "Type"

    "iface","SIMPLE_STRING"

add_nat_allow
^^^^^^^^^^^^^

Add NAT rule (adds to top of chain)

..  csv-table:: Parameters
    :header: "Name", "Type"

    "range","TEXT"

add_raw
^^^^^^^

Add raw rule (adds to top of chain)

..  csv-table:: Parameters
    :header: "Name", "Type"

    "cmd","ADVTEXT"
    "chain","SIMPLE_STRING"

add_raw_to_table
^^^^^^^^^^^^^^^^

Add rule to table (adds to top of chain)

..  csv-table:: Parameters
    :header: "Name", "Type"

    "cmd","ADVTEXT"
    "table","SIMPLE_STRING"
    "chain","SIMPLE_STRING"

remove_rule
^^^^^^^^^^^

Remove a iptables rule

..  csv-table:: Parameters
    :header: "Name", "Type"

    "id","INTEGER"

