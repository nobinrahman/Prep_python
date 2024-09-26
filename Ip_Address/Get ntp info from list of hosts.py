# Get ntp info from list of hosts

import paramiko

# Function to connect to a host, execute 'show ntp associations', and save output to file
def get_ntp_addresses(hosts_file, output_file):
    try:
        # Read list of hosts from file
        with open(hosts_file, 'r') as file:
            hosts = file.read().splitlines()

        # Initialize SSH client
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect to each host and execute 'show ntp associations'
        with open(output_file, 'w') as output:
            for host in hosts:
                try:
                    client.connect(hostname=host, username='cisco', password='MSFT123!')
                    stdin, stdout, stderr = client.exec_command('show ntp associations')
                    output.write(f"=== {host} ===\n")
                    output.write(stdout.read().decode('utf-8'))
                except Exception as e:
                    output.write(f"Error connecting to {host}: {e}\n")

        print(f"NTP addresses extracted and saved to {output_file}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

# Define file paths
hosts_file_path = '/Users/khrahman/Documents/Personal/Interview Prep/Automation/Ip_Address/list_of_host.txt'
output_file_path = '/Users/khrahman/Documents/Personal/Interview Prep/Automation/Ip_Address/ntp_output.txt'

# Call function to get NTP addresses and save to file
get_ntp_addresses(hosts_file_path, output_file_path)
