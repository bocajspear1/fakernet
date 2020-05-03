import subprocess
import json

def _convert_ovs_type(item):
    if isinstance(item, list):
        if item[0] == 'uuid':
            return item[1]
        elif item[0] == 'set':
            ret_list = []
            for subitem in item[1]:
                ret_list.append(_convert_ovs_type(subitem))
            return ret_list
        elif item[0] == 'map':
            ret_map = {}
            for subitem in item[1]:
                ret_map[subitem[0]] = subitem[1]
            return ret_map
        else:
            return item
    else:    
        return item

def convert_ovs_table(ovs_data):
    headings = ovs_data['headings']
    data = ovs_data['data']
    out_list = []
    for row in data:
        out_map = {}
        for i in range(len(headings)):
            
            column = headings[i]
            out_map[column] = _convert_ovs_type(row[i])
            
        out_list.append(out_map)
    
    
    return out_list


def remove_all_ovs():
    output = subprocess.check_output(["/usr/bin/sudo", "/usr/bin/ovs-vsctl", "-f", "json", "list", "bridge"]).decode()
    bridge_list = json.loads(output)
    bridge_data = convert_ovs_table(bridge_list)

    for bridge in bridge_data:
        subprocess.check_output(["/usr/bin/sudo", "/usr/bin/ovs-vsctl", "del-br", bridge['name']]).decode()


def clean_ovs():
    output = subprocess.check_output(["/usr/bin/sudo", "/usr/bin/ovs-vsctl", "-f", "json", "list", "bridge"]).decode()
    bridge_list = json.loads(output)
    bridge_data = convert_ovs_table(bridge_list)

    output = subprocess.check_output(["/usr/bin/sudo", "/usr/bin/ovs-vsctl", "-f", "json", "list", "port"]).decode()
    port_list = json.loads(output)
    port_data = convert_ovs_table(port_list)

    output = subprocess.check_output(["/usr/bin/sudo", "/usr/bin/ovs-vsctl", "-f", "json", "list", "interface"]).decode()
    interface_list = json.loads(output)
    interface_data = convert_ovs_table(interface_list)

    interface_map = {}
    for interface in interface_data:
        interface_map[interface['_uuid']] = interface
        

    port_map = {}
    for port in port_data:
        port_map[port['_uuid']] = port
        if isinstance(port['interfaces'], str):
            port_map[port['_uuid']]['interfaces'] = interface_map[port['interfaces']]

    for row in bridge_data:
        for iface_id in row['ports']:
            if iface_id in port_map:
                port = port_map[iface_id]
                if 'error' in port['interfaces'] and 'could not open' in port['interfaces']['error']:
                    subprocess.check_output(["/usr/bin/sudo", "/usr/bin/ovs-vsctl", "del-port", row['name'], port['name']]).decode()

            

    
    # print(bridge_list['data'])
