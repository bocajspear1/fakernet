import sys
import os

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parentdir)


from lib.util import *

if __name__ == '__main__':
    print("Cleaning OVS ports...")
    clean_ovs()