.. _using-fakernet:

Using FakerNet
==============

Once FakerNet is installed, how do we utilize the framework to get our servers built? First, we need to take a quick look at how the framework is glued together.

Modules and Functions
^^^^^^^^^^^^^^^^^^^^^

Service and server building, configuration, and removal functionality is built into **modules**. Every module exposes a series of **functions** that perform a certain, single task, such as:

* Creating a server 
* Adding a DNS record
* Stopping a server

This modular structure allows modules to call other modules and so forth so that functionality isn't reimplemented constantly, while being accessible and flexible. In FakerNet, this combination of function and module is referred to usually through the form:

..  code-block::

    <MODULE>.<FUNCTION>


Accessing Functions
^^^^^^^^^^^^^^^^^^^

Modules and their functions can be run through two main ways:

1. Locally: The functions are directly called locally, no server is involved. Good for smaller setups and testing.
2. A REST API server: The functions are called through a REST API server, usually running as a service. Good for more permanent setups and remote systems. (See :ref:`server`)

To access either of these methods is most commonly through the FakerNet console. See :ref:`cli-usage`. (You could also call the REST API directly)


Saving and Restoring
^^^^^^^^^^^^^^^^^^^^^

FakerNet supports saving and restoring running servers, creating a state of what is up and what is down. This can be used with the ``save`` and ``restore`` commands in the CLI. Without any arguments, the save state is named ``default``, and is stored in ``saves/default.json``. This will be the state loaded when the FakerNet server starts. Use these commands with a string to give the state a name or restore a named state. 


..  code-block::

    save example 
    restore example 

The named saves are stored in ``saves/<NAME>.json``