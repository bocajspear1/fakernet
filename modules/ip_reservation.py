from lib.base_module import BaseModule
import lib.validate as validate

class IPReservation(BaseModule):

    def __init__(self, mm):
        self.mm = mm

    __FUNCS__ = {
        "list_ips": {
            "_desc": "View IP allocations"
        },
        "get": {
            "_desc": "Get IP reservation info",
            "ip_id": "INT"
        },
        "add_ip": {
            "_desc": "Add an IP reservation",
            "ip_addr": "IP_ADDR",
            "description": "TEXT"
        },
        "remove_ip": {
            "_desc": "Remove an IP reservation",
            "ip_addr": "IP_ADDR",
        }
    } 

    __SHORTNAME__  = "ipreserve"
    __DESC__ = "Manages IP reservations"
    __AUTHOR__ = "Jacob Hartman"

    def run(self, func, **kwargs) :
        dbc = self.mm.db.cursor()
        if func == "list_ips":
            dbc.execute("SELECT * FROM ip_list;") 
            results = dbc.fetchall()
            return None, {
                "rows": results,
                "columns": ["ID", "IPAddress", "Network ID", "Description"]
            }
        elif func == "add_ip":
            perror, _ = self.validate_params(self.__FUNCS__['add_ip'], kwargs)
            if perror is not None:
                return perror, None

            err, results = self.mm['netreserve'].run('list')
            if err is not None:
                return err, None

            ip = kwargs['ip_addr']
            in_network = False
            for result in results['rows']:
                if validate.is_ip_in_network(ip, result[1]):
                    in_network = result[0] 

            if in_network is not False:
                dbc.execute('SELECT * FROM ip_list WHERE ip=?', (ip,))
                result = dbc.fetchone()
                if result is not None:
                    return "IP already allocated", None
                dbc.execute('INSERT INTO ip_list (ip, net_id, ip_desc) VALUES (?, ?, ?)', (ip, in_network, kwargs['description']))
                self.mm.db.commit()
                return None, (in_network, ip)
            else:
                return "IP not in any allocated networks", None
        elif func == "delete_ip_by_id":
            pass
        elif func == "remove_ip":
            perror, _ = self.validate_params(self.__FUNCS__['remove_ip'], kwargs)
            if perror is not None:
                return perror, None

            ip_addr = kwargs['ip_addr']

            dbc.execute("SELECT ip FROM ip_list WHERE ip=?", (ip_addr,))
            result = dbc.fetchone()
            if not result:
                return "IP {} is not allocated".format(ip_addr), None

            dbc.execute("DELETE FROM ip_list WHERE ip=?", (ip_addr,))
            self.mm.db.commit()
            return None, True
        else:
            return "Invalid function '{}.{}'".format(self.__SHORTNAME__, func), None

    def check(self):
        dbc = self.mm.db.cursor()

        dbc.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ip_list';")
        if dbc.fetchone() is None:
            dbc.execute("CREATE TABLE ip_list (ip_id INTEGER PRIMARY KEY, ip TEXT, net_id INTEGER, ip_desc TEXT);")
            self.mm.db.commit()

    def build(self):
        pass

    def restore(self, restore_data):
        pass

    def save(self):
        pass

__MODULE__ = IPReservation