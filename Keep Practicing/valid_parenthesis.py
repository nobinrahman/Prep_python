# 20. Valid Parentheses
# Solved
# Easy
# Topics
# conpanies icon
# Companies
# Hint
# Given a string s containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid.

# An input string is valid if:

# Open brackets must be closed by the same type of brackets.
# Open brackets must be closed in the correct order.
# Every close bracket has a corresponding open bracket of the same type.
 

# Example 1:

# Input: s = "()"

# Output: true

# Example 2:

# Input: s = "()[]{}"

# Output: true

# Example 3:

# Input: s = "(]"

# Output: false

# Example 4:

# Input: s = "([])"

# Output: true

# Example 5:

# Input: s = "([)]"

# Output: false



def validparenthesis(s):
	stack = []
	mapping = {')': '(','}': '{', ']': '['}

	for char in s:
		if char in mapping:
			# Pop the top of the stack if it's not empty, else use a dummy value
			if stack:
				top = stack.pop()
			else: '#'
			if mapping[char] != top:
				return False
		else:
			stack.append(char)
	return not stack

print(validparenthesis("([)]"))

print(validparenthesis("(){}[]"))









