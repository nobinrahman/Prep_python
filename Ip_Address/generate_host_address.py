# Write code to generate hosts addresses for a given network add and mask.
# Assume there is a lib function that converts ip to num and num to ip

import ipaddress

# Define the network
network = ipaddress.IPv4Network('172.16.128.0/20')
print(network)

# Get the first and last host addresses
first_host = network.network_address + 1
last_host = network.broadcast_address - 1

# Print the range of host addresses
print(f"The range of host addresses for network {network.network_address}/{network.prefixlen} is:")
print(f"First Host: {first_host}")
print(f"Last Host: {last_host}")


# Range of ip address
count = 0 
network = ipaddress.IPv4Network('172.16.128.0/20')
for ip in network.hosts():
    count = count + 1
    print(ip)
    print(count)