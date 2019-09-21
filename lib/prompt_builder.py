
import lib.validate as validate

from prompt_toolkit import prompt


def prompt_get_ip_addr(prompt_text=">"):
        
    done = False
    while not done:
        get_ip = prompt(prompt_text + " ")

        if get_ip == "!exit":
            return None

        if validate.is_ip(get_ip):
            return get_ip
        else:
            print("Invalid IP")


def prompt_get_ip_in_network(network, prompt_text=">"):
    
    done = False
    while not done:
        ip = prompt_get_ip_addr(prompt_text)
        if ip is None:
            return None 
        
        if validate.is_ip_in_network(ip, network):
            return ip
        else:
            print("IP not in network " + str(network))

def prompt_get_network(prompt_text=">"):
    
    done = False
    while not done:
        network = prompt(prompt_text + " ")

        if network == "!exit":
            return None

        if validate.is_ipnetwork(network):
            return network
        else:
            print("Invalid network")

def prompt_get_dns_name(prompt_text=">"):
    
    done = False
    while not done:
        dns = prompt(prompt_text + " ")

        if dns == "!exit":
            return None

        if validate.is_valid_dns(dns):
            return dns
        else:
            print("Invalid DNS name")

    