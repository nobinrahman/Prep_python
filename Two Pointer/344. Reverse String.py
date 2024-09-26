# 344. Reverse String

# Write a function that reverses a string. The input string is given as an array of characters s.

# You must do this by modifying the input array in-place with O(1) extra memory.

 

# Example 1:

# Input: s = ["h","e","l","l","o"]
# Output: ["o","l","l","e","h"]
# Example 2:

# Input: s = ["H","a","n","n","a","h"]
# Output: ["h","a","n","n","a","H"]



# SOLUTION 1

# def reverse_string(s):
# 	return (s[::-1])


# s = ["h","e","l","l","o"]

# x = reverse_string(s)

# print(x)

# SOLUTION 2

# def reverse_string(s):
# 	new_s = ''
# 	for i in range(len(s) -1, -1,-1):
# 		new_s += s[i]
# 	return (list(new_s))

# s = ["h","e","l","l","o"]

# x = reverse_string(s)

# print(x)

# SOLUTION 3: Two pointer technique

def reverse_string(s):
	left = 0
	right = len(s) - 1
	while left < right:
		s[left], s[right] = s[right], s[left]
		left += 1
		right -= 1
	return s
s = ["h","e","l","l","o"]
x = reverse_string(s)
print(x)


