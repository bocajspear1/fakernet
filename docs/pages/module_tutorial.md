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

## Adding Module Functions

This is the where we define the central functionality of your module: functions. These are the things you call in ```fnconsole``` or between modules. They all go in the ```run``` method of your module.

We'll first you need to determine what functions you will expose. At minimum, you should have ones to create, destroy, stop and start instances. Once you've figured it out, you need to put them in the ```__FUNCS__``` class constant. This dict has a special structure which allows the framework to automatically figure out what parameters the function has and even for automatically generating documention for the module.

At minimum, for modules that provide a service, you need at leasts a minimum of four functions:

* ```list```: List servers and their creation and running status
* ```add_server```: Adding a server
* ```remove_server```: Remove a server
* ```start_server```: Start a server
* ```stop_server```: Stop a server

These names are not required, but encouraged to maintain consistency. There are not requirements for function names except they are a string, as they need to be ablew to be put into a Python dict.

The dict that defines the function and its arguments is simply:
```
"FUNCTION_NAME": {
    "ARG1": "TYPE",
    "ARG2": "TYPE"
}
```

Each function definition has a special field, ```_desc```, which is not an argument, but the description of the function. This is displayed in the command line interface and documentation.

Example:
```python
__FUNCS__ = {
    "list": {
        "_desc": "View all servers"
    },
    "add_server": {
        "_desc": "Add a server",
        "fqdn": "TEXT",
        "ip_addr": "IP"
    },
    "remove_server": {
        "_desc": "Delete a server",
        "id": "INTEGER"
    },
    "start_server": {
        "_desc": "Start a server",
        "id": "INTEGER"
    },
    "stop_server": {
        "_desc": "Start a server",
        "id": "INTEGER"
    }
} 
```

### ```list``` Function

First, let's work on the ```list``` function. This function simply returns a list of servers and their statuses. It requires a special return format so FakerNet can display it correctly.

To begin, the boilerplate should have your ```run``` method code look like:
```python
def run(self, func, **kwargs):
    dbc = self.mm.db.cursor()
    # Put list of functions here
    if func == "":
        pass
    else:
        return "Invalid function '{}.{}'".format(self.__SHORTNAME__, func), None
```

Run is passed the function name in ```func```, with the arguments as Python kwargs in ```kwargs```. We just determine the function and run the proper code based on the name. 

So, to add ```list``` as a valid function, change the blank string in the ```if``` statement to ```list```. Once that's done, add the code to retrieve server container data from the database.
```python
# Put list of functions here
if func == "list":
    dbc.execute("SELECT * FROM inspircd;") 
    results = dbc.fetchall()
```

To add status information, you can use a helper function built into the parent class your class inherits from: ```self.docker_status(<CONTAINER_NAME>)```. It returns the built status and running status in a two-sized tuple.

Here's code similar to other modules, which basically loops through the containers and appends it to the server data to make the results list:
```python
new_results = []
for row in results:
    new_row = list(row)
    container_name = INSTANCE_TEMPLATE.format(row[0])
    _, status = self.docker_status(container_name)
    new_row.append(status[0])
    new_row.append(status[1])
    new_results.append(new_row)
```

Then, you need to return the data as dict with the keys ```rows``` and ```columns```.  ```rows``` is the list containing the data, and ```columns``` is a list containing the names of columns in the rows. Be sure the number of row columns and columns in the ```columns``` list match and the data rows match to the names.

```python
return None, {
    "rows": new_results,
    "columns": ['ID', "server_fqdn", "server_ip", 'built', 'status']
}
```

Note that the function also returns two values, the first is an error, which is a string containing the error. The second is the data you are returning. In out case, since we have no errors, we return ```None``` for the error and our data as the second return value. All functions are expected to use this format.

### ```add_server``` and ```remove_server``` Functions

Next we'll create the functions to create and destory server containers. As we build these functions, we'll also see how to call functions in other modules.

To add the function, add a new conditional in the ```run``` method:

```python
# End of list function here
elif func == "add_server":
    pass
else:
    return "Invalid function '{}.{}'".format(self.__SHORTNAME__, func), None
```

#### Arguments

Arguments are recieved through Python kwargs. See Python's documentation for kwargs for more details. kwargs essentially packs named arguments to a dict that we can extract our argument data from. We can use the helper function, ```self.validate_params``` to ensure all our required parameters are filled. This uses the function definition in ```__FUNCS__``` to determine the required arguments. We pass the function definition from ```__FUNCS__``` and the kwargs.

Example:
```python
perror, _ = self.validate_params(self.__FUNCS__['add_server'], kwargs)
# If there's any errors, like missing a parameter, validate_params will produce an error, which we pass back instead of continuing 
if perror is not None:
    return perror, None

# Extract our variables here
fqdn = kwargs['fqdn']
server_ip = kwargs['ip_addr']
```

Note again the ```<ERROR>, <RESULT>``` return format. Remember that all functions must return this way.

#### Duplicate Checking

Next you should check that we're not duplicating an existing container. This is usually just a database check.

Example:
```python
# Check for duplicates 
dbc.execute("SELECT server_id FROM simplemail WHERE server_fqdn=? OR server_ip=?", (fqdn, server_ip))
if dbc.fetchone():
    return "inspircd server already exists of that FQDN or IP", None
```

#### Allocating IP and FQDN

Next, we need to allocate our IP address from ```ipreserve``` module and our domain name from the ```dns``` module. This ensures we have no overlaps on IP addresses or domain names.

Doing these allocations are simple, we just call functions from those modules. To do this, we do:
```
self.mm['<MODULE_NAME>'].run("function", arg1=<ARG1>, etc.)
```

For ```ipreserve``` we call ```add_ip```, giving it our IP and a brief description:
```python
# Allocate our IP address
error, _ = self.mm['ipreserve'].run("add_ip", ip_addr=server_ip, description="inspircd Server: {}".format(fqdn))
if error is not None:
    return error, None
```

For ```dns```, we call ```add_host```, which not only allocates out domain name, it adds it to the necessary DNS server as well as adding the reverse DNS lookup as well! We pass it the domain name and our IP.
```python
# Allocate our DNS name
err, _ = self.mm['dns'].run("add_host", fqdn=fqdn, ip_addr=server_ip)
if err is not None:
    return err, None
```

For both we ensure there are no errors before continuing and stops the function if we get one.

#### Inserting into the Database

Next, we need to insert our server data into the database:
```python
# Add the server to the database
dbc.execute('INSERT INTO inspircd (server_fqdn, server_ip) VALUES (?, ?)', (fqdn, server_ip))
self.mm.db.commit()

inspircd_id = dbc.lastrowid
```

We store the ```lastrowid``` so we can refer to the server later.



### ```start_server``` and ```stop_server``` Functions

## ```save``` and ```restore``` Methods

## ```get_list``` Method