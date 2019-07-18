from lib.base_module import BaseModule
import lib.validate as validate

class IPReservation():

    def __init__(self, mm):
        self.mm = mm

    __PARAMS__ = {
        "viewall": {
            "_desc": "View IP allocations"
        },
        "get": {
            "_desc": "Get IP reservation info",
            "ip_id": "INT"
        },
        "add_ip": {
            "_desc": "Add an IP reservation",
            "ip": "IP_ADDR",
            "description": "TEXT"
        },
    } 

    __SHORTNAME__  = "ipreserve"

    def run(self, func, **kwargs) :
        dbc = self.mm.db.cursor()
        if func == "viewall":
            dbc.execute("SELECT * FROM ip_list;") 
            results = dbc.fetchall()
            return results
        elif func == "add_ip":
            if not "ip" in kwargs:
                return "'ip' not set", None
            if not "description" in kwargs:
                return "'description' not set", None

            err, results = self.mm['netreserve'].run('viewall')
            if err is not None:
                return err, None

            ip = kwargs['ip']
            in_network = False
            for result in results:
                if validate.is_ip_in_network(ip, result[1]):
                    print(ip, result[1])
                    in_network = result[0] 

            if in_network is not False:
                dbc.execute('INSERT INTO ip_list (ip, net_id, ip_desc) VALUES (?, ?, ?)', (ip, in_network, kwargs['description']))
                self.mm.db.commit()
                return None, (in_network, ip)
            else:
                return "IP not in any allocated networks", None

        return "Invalid function", None

    def check(self):
        dbc = self.mm.db.cursor()

        dbc.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ip_list';")
        if dbc.fetchone() is None:
            dbc.execute("CREATE TABLE ip_list (ip_id INTEGER PRIMARY KEY, ip TEXT, net_id INTEGER, ip_desc TEXT);")
            self.mm.db.commit()

    def build(self):
        pass

__MODULE__ = IPReservation