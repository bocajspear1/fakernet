# Getting Started

FakerNet is primarily accessed via a command line interface, `fnconsole`. (A web based interface may be created at some point.) This command line can either use modules locally or connect to a REST API server, either remote or locally. The FakerNet server (`fnserver`) is required for automatic startup of your network setup, otherwise you have to manually start your services and reapply certain configurations every time your FakerNet system reboots.

# Before Installing the Service

Before you install the service, you need to perform the first-run setup. This is as easy as running the FakerNet console, which will set you though creating the minimum required services:

* A DNS server (the central server that all other FakerNet systems by default will forward to and yours should too)
* A MiniCA instance to generate certificates for other services.

After that, you will be dropped into the FakerNet console. If you plan to use the service, continue to the next step. If not, head to the [Console User Manual](console-user-manual.html).

# Installing the FakerNet Service

The FakerNet service can be installed using the following instructions:

### Systemd

Run in a system shell:
```
./scripts/create_systemd_service.sh
```

This should create the FakerNet service that will run as the current user.


