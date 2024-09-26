import ipaddress

class Solution:
    def __init__(self, ip1):
        self.ip1 = ip1

    def address_type(self):
        try:
            addr = ipaddress.ip_address(self.ip1)
            if addr.is_loopback:
                return "Loopback"            
            elif addr.is_private:
                return "Private"
            elif addr.is_multicast:
                return "Multicast"
            elif addr.is_global:
                return "Public"
            else:
                return "Unknown"
        except ValueError:
            return "Invalid IP Address"

# List of IP addresses to test
ip_addresses = [
    '8.8.8.8',
    '4.4.4.4',
    '127.0.0.1',
    '256.1.1.1',
    '237.0.0.5'
]

# Testing each IP address
for ip in ip_addresses:
    solver = Solution(ip)
    result = solver.address_type()
    print(f"IP Address: {ip} - Type: {result}")


# Without using any module

class Solution:
    def __init__(self, ip1):
        self.ip1 = ip1

    def address_type(self):
        try:
            parts = self.ip1.split('.')
            if len(parts) != 4:
                return "Invalid IP Address"

            octets = []
            for part in parts:
                octet = int(part)
                if octet < 0 or octet > 255:
                    return "Invalid IP Address"
                octets.append(octet)

            if octets[0] == 127:
                return "Loopback"
            elif octets[0] == 10 or (octets[0] == 172 and 16 <= octets[1] <= 31) or (octets[0] == 192 and octets[1] == 168):
                return "Private"
            elif 224 <= octets[0] <= 239:
                return "Multicast"
            elif 1 <= octets[0] <= 223:
                return "Public"
            else:
                return "Unknown"
        except ValueError:
            return "Invalid IP Address"

# List of IP addresses to test
ip_addresses = [
    '8.8.8.8',
    '4.4.4.4',
    '127.0.0.1',
    '256.1.1.1',
    '237.0.0.5'
]

# Testing each IP address
for ip in ip_addresses:
    solver = Solution(ip)
    result = solver.address_type()
    print(f"IP Address: {ip} - Type: {result}")

