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
