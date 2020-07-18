# encoding: utf-8

'''easyzone

A module to manage the common record types of a zone file,
including SOA records.  This module sits on top of the
dnspython package and provides a higher level abstraction
for common zone file manipulation use cases.
'''

__author__ = 'Chris Miles/Jacob Hartman'
__copyright__ = '(c) Chris Miles 2007-2011, Jacob Hartman 2019'
__version__ = '1.2.3'


# ---- Imports ----

# - Python Modules -
from time import localtime, strftime, time
import types
import os

# - dnspython Modules - http://www.dnspython.org/
try:
    import dns.zone
except ImportError:
    import sys
    sys.stderr.write("Requires dns module from http://www.dnspython.org/\n")
    sys.exit(1)

import dns.rdtypes.ANY.CNAME
import dns.rdtypes.ANY.NS
import dns.rdtypes.ANY.MX
import dns.rdtypes.IN.A
import dns.rdtypes.ANY.TXT
import dns.rdtypes.ANY.PTR
import dns.rdtypes.ANY.SOA

import dns.rdataset

from dns.rdataclass import *
from dns.rdatatype import *

# ---- Exceptions ----

class ZoneError(Exception):
    '''An error from easyzone.Zone'''

class NameError(Exception):
    '''An error from easyzone.Name'''

class RecordsError(Exception):
    '''An error from easyzone.Records'''


# ---- Classes ----

# class SOA(object):
#     '''Represents the SOA fields of the root node of a Zone.
#     '''
#     def __init__(self, soa):
#         self._soa = soa
    
#     def get_mname(self):
#         return str(self._soa.mname)
    
#     def set_mname(self, value):
#         name = dns.name.Name( value.split('.') )
#         self._soa.mname = name
    
#     mname = property(get_mname, set_mname)
    
#     def get_rname(self):
#         return str(self._soa.rname)
    
#     def set_rname(self, value):
#         name = dns.name.Name( value.split('.') )
#         self._soa.rname = name
    
#     rname = property(get_rname, set_rname)
    
#     def get_serial(self):
#         return self._soa.serial
    
#     def set_serial(self, value):
#         self._soa.serial = value
    
#     serial = property(get_serial, set_serial)
    
#     def get_refresh(self):
#         return self._soa.refresh
    
#     def set_refresh(self, value):
#         self._soa.refresh = value
    
#     refresh = property(get_refresh, set_refresh)
    
#     def get_retry(self):
#         return self._soa.retry
    
#     def set_retry(self, value):
#         self._soa.retry = value
    
#     retry = property(get_retry, set_retry)
    
#     def get_expire(self):
#         return self._soa.expire
    
#     def set_expire(self, value):
#         self._soa.expire = value
    
#     expire = property(get_expire, set_expire)
    
#     def get_minttl(self):
#         return self._soa.minimum
    
#     def set_minttl(self, value):
#         self._soa.minimum = value
    
#     minttl = property(get_minttl, set_minttl)



class Records(object):
    '''Represents the records associated with a name node.  
    Record items are common DNS types such as 'A', 'MX',
    'NS', etc.
    '''
    def __init__(self, rectype, rdataset):
        self.type = rectype
        self._rdataset = rdataset
    
    def add(self, item):
        if self.type == 'MX':
            assert isinstance(item, (tuple, list))
            assert len(item) == 2
            assert isinstance(item[0], int)
            assert isinstance(item[1], str)
        elif self.type == 'TXT':
            assert isinstance(item, str)
            if item.startswith('"') and item.endswith('"'):
                # strip quotes off both ends; dns module will add them automatically
                item = item[1:-1]
        else:
            assert isinstance(item, str)
        
        rd = _new_rdata(self.type, item)
        self._rdataset.add(rd)
    
    def delete(self, item):
        rd = _new_rdata(self.type, item)
        try:
            self._rdataset.remove(rd)
        except ValueError:
            raise RecordsError("No such item in record: %s" %item)
    
    def __iter__(self):
        return iter(self._rdataset)
    
    def next(self):
        if self.type == 'MX':
            r = self._item_iter.next()
            return (r.preference, str(r.exchange))
        else:
            return str(self._item_iter.next())
    
    def get_items(self):
        return [r for r in self]
    
    items = property(get_items)


class Name(object):
    '''Represents a name node within a zone file.  This could
    be the root node (the zone itself) or a hostname or subdomain
    node.
    
    Each node can consist of one or more records of various
    types, e.g. 'MX', 'A', 'NS', etc.
    
    If `node` is a dns.node object then the records associated
    with that node will be available as the `records` attribute.
    
    If the node contains SOA fields (i.e. the  root ('@') node)
    then the `soa` attribute points to an SOA object.
    '''
    def __init__(self, name, node=None, ttl=None):
        self.name = name
        self.soa = None
        self.ttl = ttl
        self._node = node
        
    
    def records(self, rectype, create=False, ttl=None):
        typeval = dns.rdatatype.from_text(rectype)
        if typeval is None:
            raise NameError("Invalid type: %s" %rectype)
        
        r = self._node.get_rdataset(dns.rdataclass.IN, typeval, create=create)
    
        if r is None:
            return None
        
        if self.ttl and r.ttl == 0:
            r.update_ttl(self.ttl)
        
        rec = Records(rectype, r)
        
        return rec
    
    def clear_all_records(self, exclude=None):
        '''Clear all the records for this name node.
        '''
        if exclude is None:
            self._node.rdatasets = []
        else:
            exclude_type = dns.rdatatype.from_text(exclude)
            if exclude_type is None:
                raise NameError("Invalid exclude: %s" % exclude)
            
            for r in self._node.rdatasets:
                if r.rdtype != exclude_type:
                    self._node.rdatasets.remove(r)
    




class Zone(object):
    '''Represents a DNS zone.
    '''
    def __init__(self, domain):
        if not domain or not isinstance(domain, str):
            raise ZoneError('Invalid domain')
        if domain[-1] != '.':
            domain = domain + '.'
        self.domain = domain
        
        self._zone = None
    
    def load_from_file(self, filename):
        '''Load the details of a zone from zone file `filename`.
        '''
        self.filename = filename
        self._zone = dns.zone.from_file(filename, self.domain, relativize=False)
    
    def get_root(self):
        '''Return the root ("@") name of the zone as a Name object.
        '''
        if not self._zone:
            return None
        
        return Name('@', self._zone[self.domain])
    root = property(get_root)
    
    def get_names(self):
        '''Return a dictionary of names, keyed by name as string,
        with values as corresponding Name objects.'''
        if not self._zone:
            return None
        
        default_ttl = self._zone.get_rdataset(self.domain, dns.rdatatype.SOA)[0].minimum
        
        names = {}
        for name in self._zone.keys():
            name = str(name)
            nameobj = Name(name, self._zone[name], default_ttl)
            names[name] = nameobj
        
        return names
    names = property(get_names)
    
    def add_name(self, name):
        '''Add a new name (hostname) to the zone.
        If a node with the same name already exists it is returned instead.
        '''
        node = self._zone.get_node(name, create=True)
        if node is None:
            raise ZoneError("Could not create node named: %s" %name)
    
    def delete_name(self, name):
        '''Remove all nodes associated with a name (hostname) from the zone.
        If no such nodes exist, nothing happens.
        '''
        self._zone.delete_node(name)
    
    def save(self, filename=None, autoserial=False):
        '''Write the zone back to a file.
        
        If `filename` is not specified the zone will be written
        over the top of the file it was read from.
        
        if `autoserial`is True then the serial will be updated to the
        current date in common YYYYMMDDxx format.  The serial is
        guaranteed to be larger than the previous number.
        '''
        if autoserial:
            
            old_set = self._zone.get_rdataset(self.domain, dns.rdatatype.SOA)
            new_set = dns.rdataset.Rdataset(dns.rdataclass.IN, dns.rdatatype.SOA)
            for soa in old_set:
            # for (name, ttl, rdata) in self._zone.iterate_rdatas(SOA):
                new_serial = soa.serial+1
                new_soa = soa.replace(serial=new_serial)
                new_set.add(new_soa)
            # self._zone.delete_rdataset("@", 'SOA')
            self._zone.replace_rdataset(self.domain, new_set)


        
        if not filename:
            filename = self.filename
        outtext = self._zone.to_text(relativize=False)

        os.remove(filename)
        outfile = open(filename, "w+")
        outfile.write(outtext)
        outfile.close()
    





# ---- Module Functions ----

def zone_from_file(domain, filename):
    '''Read a zone file and return the contents as a Zone object.
    '''
    zone = Zone(domain)
    zone.load_from_file(filename)
    return zone


def _new_rdata(rectype, *args):
    '''Create a new rdata type of `rectype`.
    rectype must be one of: 'NS', 'MX', 'A', 'CNAME', 'TXT', 'PTR'
    Extra arguments are as required by the rectype.
    '''
    if rectype == 'NS':
        name = dns.name.Name( args[0].split('.') )
        rd = dns.rdtypes.ANY.NS.NS(dns.rdataclass.IN, dns.rdatatype.NS, name)
    elif rectype == 'MX':
        preference = args[0][0]
        exchange = dns.name.Name( args[0][1].split('.') )
        rd = dns.rdtypes.ANY.MX.MX(dns.rdataclass.IN, dns.rdatatype.MX, preference, exchange)
    elif rectype == 'A':
        #name = dns.name.Name( args[0].split('.') )
        name = args[0]
        rd = dns.rdtypes.IN.A.A(dns.rdataclass.IN, dns.rdatatype.A, name)
    elif rectype == 'PTR':
        name = dns.name.Name( args[0].split('.') )
        rd = dns.rdtypes.ANY.PTR.PTR(dns.rdataclass.IN, dns.rdatatype.PTR, name)
    elif rectype == 'CNAME':
        name = dns.name.Name( args[0].split('.') )
        rd = dns.rdtypes.ANY.CNAME.CNAME(dns.rdataclass.IN, dns.rdatatype.CNAME, name)
    elif rectype == 'TXT':
        rd = dns.rdtypes.ANY.TXT.TXT(dns.rdataclass.IN, dns.rdatatype.TXT, args[0])
    else:
        raise ValueError("rectype not supported: %s" %rectype)
    
    return rd


