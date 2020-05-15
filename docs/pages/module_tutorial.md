# Module Building Tutorial

This tutorial will step you through the creation of a FakerNet module. This tutorial will step through the creation of the inspircd module.

## Create Module File

First, you need to create the module file in the ```modules``` directory. Name it something like ```<app>.py```, so in out case we well create the file ```<FAKERNET_ROOT>/modules/inspircd.py```.

## Create Module Class

All modules need to have a main class so that FakerNet can pick it up. It should look something like this:
```python
# You need this to validate parameters for your functions
import lib.validate as validate
# You need this so your class can inherit from it.
from lib.base_module import BaseModule

class ClassName(BaseModule):
    # Class code goes here

__MODULE__ = ClassName
```

> Don't forget the ```__MODULE__ = ClassName```, this is how FakerNet finds the class

## Class Constants

Classes have a handful of required constants inside the class to provide meta-data for the module. This meta-data is used by the parent class for some time-saving methods and the framework for getting info on the module.

Here's an example of some class constants:
```python
__FUNCS__ = {
    "list": {
        "_desc": "View all SimpleMail servers"
    },
    "remove_server": {
        "_desc": "Delete a SimpleMail server",
        "id": "INTEGER"
    },
    "add_server": {
        "_desc": "Add a SimpleMail server",
        "fqdn": "TEXT",
        "mail_domain": "TEXT",
        "ip_addr": "IP"
    },
    "start_server": {
        "_desc": "Start a SimpleMail server",
        "id": "INTEGER"
    },
    "stop_server": {
        "_desc": "Start a SimpleMail server",
        "id": "INTEGER"
    }
} 

__SHORTNAME__  = "simplemail"
__DESC__ = "A simple mail server"
__AUTHOR__ = "Jacob Hartman"
__SERVER_IMAGE_NAME__ = "simplemail"
```

* ```__FUNCS__```: Lists available module functions. 
* ```__SHORTNAME__```: A short alphanumeric name used to identify the module in the framework. Shortnames are referenced when calling functions in other modules.
* ```__DESC__```: A description of the module.
* ```__AUTHOR__```: The author.
* ```__SERVER_IMAGE_NAME__```: The name of the Docker image. Used by the parent class to make creating a container instance easier.

## Local Constants

Use of a few local constants is encouraged, particularly for two things: the work directory path and the Docker image name.

The work directory is a location where the FakerNet host mounts parts of the Docker image's filesystem to gain access to configuration files and store data across instances. It is encouraged to use a local constant for this, as you will probably need this path alot.

Example from ```simplemail``` module:
```python
SERVER_BASE_DIR = "{}/work/simplemail".format(os.getcwd())
INSTANCE_TEMPLATE = "simplemail-server-{}"
```

## Class Methods

### ```__init__```

You need to create a specific ```__init__``` method for your class:
```python
def __init__(self, mm):
    self.mm = mm
```

```mm``` is the FakerNet module manager, which allows you to call functions from other modules inside your module.

### Required Methods

There are a few methods that every module must have:

* ```check```: This method ensures the necessary database table is created and does any other pre-execution setup operations.
* ```run```: This is method called when a module function is called. We'll fill this out later.
* ```build```: This method is used when building the image for the module. Usually called by the ```build.py``` helper tool.
* ```save```: This is method is called during a save. Returns data to save and restore later.
* ```restore```: This method is called during a restore. Opposite of the functionality of ```save```.
* ```get_list```: This method is called when getting a list of all running containers.

Here's the boilerplate code you need for these functions:
```python
def run(self, func, **kwargs):
    dbc = self.mm.db.cursor()
    # Put list of functions here
    if func == "":
        pass
    else:
        return "Invalid function '{}.{}'".format(self.__SHORTNAME__, func), None

def check(self):
    dbc = self.mm.db.cursor()

    # This creates the module's working directory.
    if not os.path.exists(SERVER_BASE_DIR):
        os.mkdir(SERVER_BASE_DIR)

    dbc.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='<TABLE_NAME>';")
    if dbc.fetchone() is None:
        dbc.execute("CREATE TABLE <TABLE_NAME> (server_id INTEGER PRIMARY KEY, server_fqdn TEXT, server_ip TEXT, <OTHER COLUMNS>);")
        self.mm.db.commit()

def build(self):
    self.print("Building {} server image...".format(self.__SHORTNAME__))

def save(self):
    return None, None

def restore(self, restore_data):
    pass

def get_list(self):
    return None, []

```

## Writing the ```check``` Method

The first method you should write for your module is ```check```. It is called when the module is loaded, and if you're hacking around the code, should always be called before the module is used. This is mainly because this function should ensure the table for your module is created and that the working directory for your module (where each instance's shared volumes will be located) is created. The boilerplate code should take care of the working directory creation, but you'll need to modify the table creation with the table name you want and any fields you want to add. 

### Module Table

Modules mostly all have a table assigned to them that stores data about them. You should add fields and data you want stored even when the instance of the image might be shutdown and makes it easier to manage your instances. This is usually data like the IP address (so can assign an address each time the instance starts), the fully qualified domain name, and perhaps a description.

The most important field is the ID field, which is ```server_id``` in the boilerplate code. You'll use this as the instance's unique identifer in your functions, so don't remove it.

## Building Your Image

First, you need a container to actually build and that will deploy the service you want. This is usually a Docker image, and you can develop it how you want. However, you must follow these requirements:

* The service must be deployed on a single Docker image. FakerNet does not support multi-image setups, such as in ```docker-compose```.
* The service should be operating as soon as deployed, as there is no ```service start/stop``` in Docker.
* Service Dockerfile and other configuration files that will be copied in should be in a single folder in ```./docker-images```.

### Create Directory and Dockerfile

First, create the directory that will hold the files for the Docker image:

```
mkdir ./docker-images/inspircd
```

First, we need to add a Dockerfile to define how the image is built. For this module, we'll be using ```ubuntu:20.04``` and the ```inspircd``` package available. This Dockerfile is pretty straighforward and simple. See [Docker's documentation](https://docs.docker.com/engine/reference/builder/) for more info on Dockerfiles.

```Dockerfile
FROM ubuntu:20.04 

WORKDIR / 

RUN apt-get update; apt-get install -y inspircd

USER irc

RUN cat /etc/inspircd/inspircd.rules

CMD LD_LIBRARY_PATH=/usr/lib/inspircd /usr/sbin/inspircd --nofork --nopid --config /etc/inspircd/inspircd.conf
```

### Adding Configuration Files

To make each instance unique, some files must be deployed at instance creation. In our case, this will be the inspircd's configuration files. The configuration file mentioned, ```/etc/inspircd/inspircd.conf```, we will deploy into a shared volume between the host and the image alongside a few other needed files. This allows the setup to be configurable for each instance, always available at instance creation, allow configurations to persist through container starts and stops, and allow easy external access for any configuration modifications (this is especially needed in modules like ```dns```, where lots of files are modified)

However, we do need to add a way to quickly modify the configuration file when creating an instance. In this module, we'll just use the built in Python string templates to keep it simple, but you could use any templating system you want. You could even manually create it yourself in the module's code.

Here's an excerpt from the configuration file with Python template variables in it:
```
<server name="$DOMAIN"
        description="An IRC Server"
        network="Localnet">
```

Place this configuration file in the same directory as the Dockerfile.

### Adding Build Code

Now we can modify our module class's ```build``` method to build the Docker image when called. Since our's is simple and doesn't need much, we can just call Docker to build it. In other cases, you could have this code clone in a repository, maybe make some patches, and then use Docker to build it.

For out use though, just add:
```python
self.mm.docker.images.build(path="./docker-images/inspircd/", tag=self.__SERVER_IMAGE_NAME__, rm=True)
```

So the method should look like this:
```python
def build(self):
    self.print("Building {} server image...".format(self.__SHORTNAME__))
    self.mm.docker.images.build(path="./docker-images/inspircd/", tag=self.__SERVER_IMAGE_NAME__, rm=True)
```

Remember ```__SERVER_IMAGE_NAME__```? Since we used this as the image's tag, we can use some helper functions from the base module class to start and instance of the Docker without having to refer to it by name all the time.

### Doing the Build

Once you're satisfied with your image, build it using your module's code using the ```build.py``` tool:

```
python3 build.py <YOUR_MODULE_NAME>
```

You can then test it using the tag value you set in ```__SERVER_IMAGE_NAME__```:

```
docker run -it <__SERVER_IMAGE_NAME__>
```

