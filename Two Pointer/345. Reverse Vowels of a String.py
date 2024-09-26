# 345. Reverse Vowels of a String
# Given a string s, reverse only all the vowels in the string and return it.

# The vowels are 'a', 'e', 'i', 'o', and 'u', and they can appear in both lower and upper cases, more than once.

 

# Example 1:

# Input: s = "IceCreAm"

# Output: "AceCreIm"

# Explanation:

# The vowels in s are ['I', 'e', 'e', 'A']. On reversing the vowels, s becomes "AceCreIm".

# Example 2:

# Input: s = "leetcode"

# Output: "leotcede"


# This is the best way to solve this problem 

s = "leetcode"

vowels = 'aeiouAEIOU'

s= list(s)

left = 0
right = len(s) - 1

while left < right:
    if s[left] not in vowels:
        left += 1
    elif s[right] not in vowels:
        right -= 1
    else:
        s[left],s[right] = s[right],s[left]
        left += 1
        right -= 1
 
print(s)        
print(''.join(s))






