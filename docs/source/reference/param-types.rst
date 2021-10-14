.. _param-types:

Parameter Types
=================

The following is a reference of parameter types that are valid in FakerNet parameters.


..  csv-table:: Parameters
    :header: "Type", "Description", "Example"

    "``INTEGER``","A simple, non-decimal number", "``1`` ``34``" 
    "``DECIMAL``","A decimal number", "``1.2`` ``88.234``, ``2``" 
    "``TEXT``","Basic text, limited to letters, numbers, spaces, tabs, and the following: ``.,-_:=/#@``", "``this.dns`` ``hello there``" 
    "``ADVTEXT``","Text with fewer limits, limited to letters, numbers, spaces, tabs, and the following: ``.,-_!@#$%^&*()_+<>?""':|[]{}``. Be much more cautious with this", "``this.dns`` ``hello there``" 
    "``SIMPLE_STRING``","Text limited to letters and numbers", "``this1`` ``hello``" 
    "``IP``","An IP address", "``1.1.1.1`` ``192.168.7.6``" 
    "``IP_ADDR``","Same as ``IP``", "``1.1.1.1`` ``192.168.7.6``" 
    "``IP_NETWORK``","An IP network with prefix length", "``1.1.1.0/24`` ``192.168.7.0/16``" 
    "``BOOLEAN``","A boolean as a string", "``true`` ``false``" 
    "list","A selection from the list", ""

   