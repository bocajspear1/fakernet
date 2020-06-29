# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import ipaddress
import re

def is_ipnetwork(value):
    try:
        ipaddress.ip_network(value)
        return "/" in value
    except:
        return False

def is_ip(value):
    try:
        ipaddress.ip_address(value)
        return True
    except:
        return False

def is_ip_in_network(ip, network):
    if is_ipnetwork(network) and is_ip(ip):
        net = ipaddress.ip_network(network)
        return ipaddress.ip_address(ip) in net
    return False

def is_valid_dns(name):
    return re.match(r"[0-9A-Za-z-]+$", name)
