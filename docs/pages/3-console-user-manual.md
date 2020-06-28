# FakerNet Console User Manual

The FakerNet console uses the [prompt_toolkit](https://python-prompt-toolkit.readthedocs.io/en/master/) framework, which allows for a number of features like autocomplete and command history. 

## CLI Features

### History

You can use the up and down arrow keys to go back and forth through the command history.

### Tab Complete

You can also use tab to autocomplete commands. 

### Command List

Commands will appear as you type. When one of these lists is open, you can use the arrow keys to select, and tab to insert the completion.

## Server and Non-server mode

FakerNet accesses the FakerNet service through a REST API. If it can connect to the REST API, the console will go into server mode, and have the server IP in front of the prompt. The console will then send its commands to the service instead of run the commands itself. Otherwise, ```local``` appears in front of the prompt to indicate non-server mode, where the console will run the commands itself.

## Modes

The console operates in two primary level, main level and function level. 

### Main Level

Main level is the top level, and the place you start in. You can run the following commands:

* ```run <MODULE> <FUNCTION>```: This is used to call a function, and given a module and function name, will run the function, or put you into function mode.
* ```list_servers```: This lists all servers running from all modules.
* ```exit```: This exits the console.
* ```save```: This saves the current state of up and down servers. An option name can be set afterwards to name the state. The default name is ```default```.
* ```restore```: This restores from a state save. An option name can be set afterwards to set the state to load. The default name is ```default```.

### Function Level

This level is entered when running a module function that requires parameters. Functions that don't need parameters will just run the function. The module and function name will appear in the prompt when in the function level:
```
local(dns.add_record)>
```

* ```set <VAR_NAME> <VALUE>```: This sets a value for a function parameter.
* ```unset <VAR_NAME>```: This clears a value for a function parameter.
* ```back```: This goes back to the main level
* ```show```: Shows the current function's variables and their values
* ```execute```: Executes the function
* ```run <MODULE> <FUNCTION>```: Call another function. This also clears any currently set values for the current function.
