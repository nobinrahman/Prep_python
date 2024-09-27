#!/bin/bash

cd /auto/tftp-gud/khrahman/urgent

# Start tmux server if not already running
tmux start-server

# Create a new session
session_name="mysession_$(date +%Y%m%d_%H%M%S)"
tmux new-session -d -s "$session_name"

# Function to create two screens for a script
create_screens() {
    tmux new-window -t "$session_name" "./$1 $2"
    tmux split-window -h -l $(( (100 - 20) / 4 )) -t "$session_name" "./$1 $2"
}

# Create screens for each script
create_screens "D18_R10_1st_set.sh" "172.25.124.50"
create_screens "D18_R10_2nd_set.sh" "172.25.124.50"
create_screens "D18_R10_3rd_set.sh" "172.25.124.50"
create_screens "D18_R10_4th_set.sh" "172.25.124.50"
create_screens "D18_R10_5th_set.sh" "172.25.124.50"
create_screens "D18_R10_6th_set.sh" "172.25.124.50"
create_screens "D18_R10_7th_set.sh" "172.25.124.50"
create_screens "D18_R10_8th_set.sh" "172.25.124.50"

# Attach to the session
tmux attach-session -t "$session_name"
