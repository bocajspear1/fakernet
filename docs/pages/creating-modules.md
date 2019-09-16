# Creating Modules

All modules are Python classes that inherit from a central base module, which contains helpful methods.

All classes should include something like this:

```python
from lib.base_module import BaseModule


class MyModule(BaseModule):

    def __init__(self, mm):
        self.mm = mm

    __FUNCS__ = {
        "list": {
            "_desc": "View network allocations"
        },
        ...
    } 

    __SHORTNAME__  = "mymodule"
    __DESC__ = "A description, appears in documentation"
    __AUTHOR__ = "You"

    def run(self, func, **kwargs) :
        dbc = self.mm.db.cursor()
        if func == "somefunc":
            pass

    ...

__MODULE__ = MyModule
```

## `__FUNCS__`

This is a dict that contains info about the functions the module supports. The format is:
```
"function_name": {
    "param_name": "param_type"
}
```

This dict allows FakerNet to verify parameters and automatically build the autocomplete for the console.

A special param_name is `_desc`, which is the description of the function, and does not count as a parameter when verifiying parameters and in the console. 

## `__SHORTNAME__`

This is the name of the module used in the console and when other modules refer to this module. It must be unique.

## Required Functions

* `run`: This function is called with the function name as a string as the first argument, then kwargs for the paramaters. Be sure to match the parameters to the function definition in `__FUNCS__`
* `check`: This function is called on console startup to ensure the database tables and other configurations are set for the module.
* `build`: This function is called to build it the base Docker image for the service. Modules that do not make a Docker image should just make an empty function with just `pass`.

## `run` Function

This function is the main function of the module and contains the primary actions and activities of the module. A `if/elif/else` determines the function from the first parameters.