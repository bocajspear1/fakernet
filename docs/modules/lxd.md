This module manages LXD containers, which provide a more VM-like experience as compared to the Docker containers most services are in.

The hostname and container name is the `fqdn` with the dots replaced with dashes.

LXD addresses are set manually by FakerNet on start, so if you start the container outside FakerNet you will not get your address properly. (This is due to the built in LXD network management utilizing DHCP, which caused limitations). Configuring the container to have a static IP through its own startup scripts is currently left up to the user, as supporting all the different methods of setting a static IP in the container would be a real pain.