import re

filepath ="/Users/krahman/Documents/Cisco/Documents/Personal/Interview Prep/Automation/Meta Question/email_sample.txt"

email_count = {}
email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9.-]+'
with open(filepath, mode='r') as file:
	for line in file:
		# print (line)
		matches = re.findall(email_pattern, line)
		# print(matches)
		for email in matches:
			if email in email_count:
				email_count[email]+=1
			else:
				email_count[email]=1
print(f"{email_count=}")



# r'...' – Raw String
# The r before the string tells Python not to treat backslashes (\) as escape characters.

# ✅ [a-zA-Z0-9+_.-]+ – Username part (before @)
# This matches the local part of the email (like john.doe in john.doe@example.com):

# [...] is a character class, meaning it matches any one character inside it.

# a-zA-Z matches letters (lowercase and uppercase)

# 0-9 matches digits

# +_.- allows these characters, which are commonly allowed in email usernames

# The + outside the [] means: one or more of these characters

# ✅ Example matches:
# john123, john.doe, sales_team, user+tag


# ✅ @ – The "at" symbol
# Just a literal @ symbol separating the local part from the domain part.


# ✅ [a-zA-Z0-9-]+ – Domain name (before the dot)
# This matches the domain name like example in example.com:

# Letters, numbers, and hyphens are allowed

# Again, + means one or more characters

# ✅ Example matches:
# example, my-company, mail2server


# ✅ \. – Literal dot
# Matches a dot (.), which separates domain and top-level domain (TLD)

# ✅ [a-zA-Z0-9-.]+ – Top-level domain (TLD)
# This matches the part after the dot, like com, org, co.uk, etc.

# Allows multiple letters, numbers, dots (.), or hyphens (-)

# The + means one or more of those characters

# ✅ Example matches:
# com, org, co.uk, company-name.info


import re

filepath = "/Users/krahman/Documents/Cisco/Documents/Personal/Interview Prep/Automation/Meta Question/email_sample.txt"

ipv4_count = {}

ipv4_pattern = r'\b(' \
               r'(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\.' \
               r'(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\.' \
               r'(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\.' \
               r'(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])' \
               r')\b'

with open(filepath, 'r') as file:
    for line in file:
        matches = re.findall(ipv4_pattern, line)
        for ip in matches:
            if ip in ipv4_count:
                ipv4_count[ip] += 1
            else:
                ipv4_count[ip] = 1

print(ipv4_count)


