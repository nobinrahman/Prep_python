# 392. Is Subsequence

# Given two strings s and t, return true if s is a subsequence of t, 
# or false otherwise.

# A subsequence of a string is a new string that is formed 
# from the original string by deleting some (can be none) of 
# the characters without disturbing the relative positions of 
# the remaining characters. (i.e., "ace" is a subsequence of 
# "abcde" while "aec" is not).

 

# Example 1:

# Input: s = "abc", t = "ahbgdc"
# Output: true
# Example 2:

# Input: s = "axc", t = "ahbgdc"
# Output: false


# def isSubsequence(s,t):

# 	t_new = ''
# 	t_index = 0

# 	for i in range(len(s)):
# 		for j in range(len(t)):
# 			if s[i] == t[j]:
# 				t_new += t[j]
# 				t_index = j + 1
# 				break
# 	if s == t_new:
# 		return True
# 	else:
# 		return False

# Efficient Method is to use two pointer method
def isSubsequence(s,t):
	i = j = 0
	while i < len(s) and j < len(t):
		if s[i] == t[j]:
			i = i + 1
		j = j + 1

	if i == len(s):
		return True
	else:
		return False

	#return i == len(s) # after the while loop if total value of i is same as len(s) 
					   # then return true



s = "abc"
t = "ahbgdc"
x = isSubsequence(s,t)
print(x)
