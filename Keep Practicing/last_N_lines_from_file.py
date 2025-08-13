from collections import deque

def tail(filepath, n):
    last_lines = deque(maxlen= n)
    with open(filepath, 'r') as file:
        for line in file:
            last_lines.append(line.rstrip())
    for line in last_lines:
        print(line)

# Usage
filepath = "/Users/krahman/Documents/Cisco/Documents/Personal/Interview Prep/Automation/Meta Question/paragraph.txt"
n = 3
tail(filepath, n)

# Time Complexity: O(L)

# L = total number of lines in the file

# Space Complexity: O(n)

# n = number of lines to keep in memory (last n lines)


import random 

def random_line(filepath):
	lines = []
	with open(filepath) as f:
		for line in f:
			lines.append(line.strip())
	if lines:
		random_line = random.choice(lines)
		print(random_line)

filepath = "/Users/krahman/Documents/Cisco/Documents/Personal/Interview Prep/Automation/Meta Question/paragraph.txt"
random_line(filepath)