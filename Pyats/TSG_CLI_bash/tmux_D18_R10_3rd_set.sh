#!/bin/bash

cd /auto/tftp-gud/khrahman/urgent

session_name="mysession_$(date +%Y%m%d_%H%M%S)"

tmux new-session -d -s "$session_name" "./D18_R10_3rd_set.sh 172.25.124.50"

tmux split-window -h -l $(( (100 - 20) / 2 )) "./D18_R10_3rd_set.sh 172.25.124.50"

tmux select-layout even-horizontal
tmux attach-session -d

