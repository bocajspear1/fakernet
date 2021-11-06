.. _cli-usage:

CLI Usage
==========

The primary method of using FakerNet is using the FakerNet console. The console can run without or with a FakerNet API server. 

..  note::
    You will need to run the console without an API server at least once to perform initial configuration. 

Starting the Console
^^^^^^^^^^^^^^^^^^^^

To start the console:

..  code-block::

    ./fnconsole


To connect to a remote system:

..  code-block::

    ./fnconsole -s <SERVER IP>

You will need to login with a username and password. See :ref:`server` for details on server setup and logins.

For local API servers, the console will automatically attempt to connect to a local server on port 5051, so you will not need the ``-s`` parameter.

Using the Console
^^^^^^^^^^^^^^^^^

The FakerNet console uses the `prompt_toolkit <https://python-prompt-toolkit.readthedocs.io/en/master/>`_ framework, which allows for a number of features like autocomplete and command history. 

* The prompt shows the address of the API server it's using, or ``local`` for no API server.
* Use the up and down arrow keys to go back and forth through the command history.
* Use TAB to autocomplete commands
* Commands will appear as you type. When one of these lists is open, you can use the arrow keys to select, and tab to insert the completion.

Console Modes 
^^^^^^^^^^^^^

The console operates in two primary level, **main** level and **function** level. FakerNet is built around functions provided by modules, you will spend most of your time running in **function** mode. Using the console, you will call module functions to perform certain actions, such as creating, stop, and starting servers.

Main Mode
-----------

Main level is the top level, and the mode you start in. This mode performs FakerNet-wide operations as well as authentication operations. You can run the following commands:

* ``run <MODULE> <FUNCTION>``: This is used to call a function, and given a module and function name, will run the function, or put you into function mode.
* ``list_all``: This lists all servers running from all modules.
* ``exit``: This exits the console.
* ``save``: This saves the current state of up and down servers. An option name can be set afterwards to name the state. The default name is ``default``.
* ``restore``: This restores from a state save. An option name can be set afterwards to set the state to load. The default name is ``default``.
* ``useradd``: Add a user to for API authentication.
* ``userls``: List users for API authentication.
* ``userdel``: Remove users from API authentication.

Function Mode
---------------

This is where most of the magic happens. FakerNet breaks up functionality into modules. This allows modules to call other modules so we aren't reimplementing stuff unnecessarily. The console provides access to the functions from these modules, so we have control to create and destroy servers, configure them, etc.

This mode is entered when running a module function that requires parameters. Functions that don't need parameters will just run the function. The module and function name will appear in the prompt when in the function level:

For example:

..  code-block::

    local(dns.add_record)>

The following commands are available:

* ``show``: Shows a brief overview of the function. This includes a short description of the function and the current function's variables and their values
* ``set <VAR_NAME> <VALUE>``: This sets a value for a function parameter.
* ``unset <VAR_NAME>``: This clears a value for a function parameter.
* ``back``: This goes back to the main level
* ``execute``: Executes the function
* ``run <MODULE> <FUNCTION>``: Call another function. This also clears any currently set values for the current function.
