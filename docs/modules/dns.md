This module creates and controls a BIND DNS server in an Alpine instance. 

Each server has a primary zone that is configured at the creation of the server. This name is used by the module to automatically determine where DNS names should go. Servers can have multiple zones, but then you cannot use the automatic server detection and have to manually indicate where a domain name needs to go.