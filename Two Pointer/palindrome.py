# Given a string s, return true if it is a palindrome, 
# false otherwise.

# s = raceacar
# True

# s= nobin
# False



def palindrome(s):
	left = 0
	right = len(s) - 1

	while left < right:
		if s[left] != s[right]:
			return False
		left += 1
		right -= 1
	return True


s = 'malayalam'

x = palindrome(s)
print(x)