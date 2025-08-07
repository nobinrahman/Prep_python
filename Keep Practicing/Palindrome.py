# 125. Valid Palindrome
# A phrase is a palindrome if, after converting all uppercase letters into lowercase letters and removing all non-alphanumeric characters, it reads the same forward and backward. Alphanumeric characters include letters and numbers.

# Given a string s, return true if it is a palindrome, or false otherwise.

 

# Example 1:

# Input: s = "A man, a plan, a canal: Panama"
# Output: true
# Explanation: "amanaplanacanalpanama" is a palindrome.
# Example 2:

# Input: s = "race a car"
# Output: false
# Explanation: "raceacar" is not a palindrome.
# Example 3:

# Input: s = " "
# Output: true
# Explanation: s is an empty string "" after removing non-alphanumeric characters.
# Since an empty string reads the same forward and backward, it is a palindrome.

############################### Normal Method ##########################
def palindrome(s):
    cleaned_string = []
    string = ''
    for char in s.lower():
        if char.isalnum():
            cleaned_string.append(char)
    if not cleaned_string:
        return ("This is palindorme")
    
    for cleaned_char in cleaned_string:
    	string = string + cleaned_char
    if string == string[::-1]:
        return("This is palindorme")
    else:
        return("This is not palindrome")

s = ' .,'
x = palindrome(s)
print(x)

############################### Two Pointer Method ##########################

def palindrome(s):
	cleaned_string = []
	for char in s.lower():
		if char.isalnum():
			cleaned_string.append(char)
	if not cleaned_string:
		return ("This is palindrome")

	left = 0 
	right = len(cleaned_string) - 1

	while left<right:
		if cleaned_string[left]!=cleaned_string[right]:
			return ("This is not palindrome")
		left += 1
		right -= 1
	return ("This is palindrome")

s = 'nobin'
x = palindrome(s)
print(x)



# 680. Valid Palindrome II
# Given a string s, return true if the s can be palindrome after deleting at most one character from it.

 

# Example 1:

# Input: s = "aba"
# Output: true
# Example 2:

# Input: s = "abca"
# Output: true
# Explanation: You could delete the character 'c'.
# Example 3:

# Input: s = "abc"
# Output: false 

def valid_palindrome(s):
    left = 0
    right = len(s) - 1

    while left < right:
        if s[left] != s[right]:
            # Try removing the left character
            skip_left = s[left+1:right+1]
            is_skip_left_palindrome = skip_left == skip_left[::-1]

            # Try removing the right character
            skip_right = s[left:right]
            is_skip_right_palindrome = skip_right == skip_right[::-1]

            # Return True if either option is a palindrome
            return is_skip_left_palindrome or is_skip_right_palindrome

        left += 1
        right -= 1

    return True

s = "abc"
x = valid_palindrome(s)
print(x)
