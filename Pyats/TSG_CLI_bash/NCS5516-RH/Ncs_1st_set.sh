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
set locations {"0/0/CPU0" "0/2/CPU0" "0/4/CPU0" "0/6/CPU0" "0/8/CPU0" "0/9/CPU0" "0/10/CPU0"}

set nodes {"Node/NodeName/Rack=0;Slot=10;Instance=CPU0" "Node/NodeName/Rack=0;Slot=2;Instance=CPU0" "Node/NodeName/Rack=0;Slot=4;Instance=CPU0" "Node/NodeName/Rack=0;Slot=6;Instance=CPU0" "Node/NodeName/Rack=0;Slot=8;Instance=CPU0" "Node/NodeName/Rack=0;Slot=9;Instance=CPU0" "Node/NodeName/Rack=0;Slot=10;Instance=CPU0"}

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

    # Add additional show commands here with the same pattern
    expect "#"
    send "show controllers npu stats asic-counters instance all location 0/RP0/CPU0 | i \"FC|pier_oob_counter.*: 0\"\r"
    sleep 10

    expect "#"
    send "show reboot history location 0/RP0/CPU0\r"
    sleep 10

    expect "#"
    send "show asic-errors all detail location 0/RP0/CPU0 | utility egrep \"IRR_LAG_MAPPING|NC55\" -B1\r"
    sleep 10

    # Finish the session (this part will never be reached in an infinite loop)
    expect "#"
    send "exit\r"

    # End the expect script
    expect eof

    # Print the counter value
    puts "Command execution finished, Counter: $counter"

    # Increment the counter
    incr counter

    # Wait for 30 seconds before the next iteration
    sleep 30
}
