# Range of ip address of a given network.

import ipaddress 

network = ipaddress.IPv4Network('172.16.0.0/16')
for ip in network.hosts():
    print(ip)