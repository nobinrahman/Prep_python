#!/usr/bin/expect

# Set variables
set timeout -1
set username "cisco"
set password "MSFT123!"

# Get the host IP address from the command line argument
set host [lindex $argv 0]

# Check if the host IP address is provided
if {[llength $argv] == 0} {
    puts "Usage: ./ssh.sh <host_ip>"
    exit 1
}

# Define the list of locations
set locations {"0/0/CPU0" "0/1/CPU0" "0/2/CPU0" "0/3/CPU0" "0/4/CPU0" "0/5/CPU0" "0/6/CPU0" "0/7/CPU0"}

set nodes {"Node/NodeName/Rack=0;Slot=0;Instance=CPU0" "Node/NodeName/Rack=0;Slot=1;Instance=CPU0" "Node/NodeName/Rack=0;Slot=2;Instance=CPU0" "Node/NodeName/Rack=0;Slot=3;Instance=CPU0" "Node/NodeName/Rack=0;Slot=4;Instance=CPU0" "Node/NodeName/Rack=0;Slot=5;Instance=CPU0" "Node/NodeName/Rack=0;Slot=6;Instance=CPU0" "Node/NodeName/Rack=0;Slot=7;Instance=CPU0"}

# Start the while loop
set infinite_loop 1
set counter 1
while {$infinite_loop == 1} {

    # Start the SSH session
    spawn ssh $username@$host

    # Handle password prompt
    expect "Password:"
    send "$password\r"
    sleep 15

    # Execute commands with delays
    expect "#"
    send "term length 0\r"
    sleep 10

    expect "#"
    send "term width 0\r"
    sleep 10

    expect "#"
    send "show version\r"
    sleep 10

    expect "#"
    send "show platform\r"
    sleep 10

    # Loop through each location for the new command
    foreach location $locations {
        expect "#"
        send "show dpa objects global base location $location | in max_trunks\r"
        sleep 15
    } 

    expect "#"
    send "show spp node-counters location all | utility egrep \"CPU0|PUNT DROP_PACKET\"\r"
    sleep 10


    expect "#"
    send "show captured packets traps all location all | in LLR_PBP_SA_DROP0\r"
    sleep 5

    # Loop through each node for the node-specific command
    foreach node $nodes {
        expect "#"
        send "show operational OFA Stats NodeTable $node\r"
        sleep 10
    }

    # End the expect script
    expect eof

    # Print the counter value
    puts "Command execution finished, Counter: $counter"

    # Increment the counter
    incr counter

    # Wait for 30 seconds before the next iteration
    sleep 30
}
