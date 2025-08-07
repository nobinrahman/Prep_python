# Anagram


# Group Anagram
# Leet code problem 49

# Given an array of strings strs, group the anagrams together. You can return the answer in any order.

# An Anagram is a word or phrase formed by rearranging the letters of a different word or phrase, typically using all the original letters exactly once.

# Example 1:
# Input: strs = ["eat","tea","tan","ate","nat","bat"]
# Output: [["bat"],["nat","tan"],["ate","eat","tea"]]

# Example 2:
# Input: strs = [""]
# Output: [[""]]

# Example 3:
# Input: strs = ["a"]
# Output: [["a"]]

def groupAnagrams(strs):
    anagrams = {}
    
    for word in strs:
        # Sort the word to create a key
        sorted_word = ''.join(sorted(word))
        # print(sorted_word)
        # Use the sorted word as the key in the dictionary
        if sorted_word in anagrams:
            anagrams[sorted_word].append(word)
        else:
            anagrams[sorted_word] = [word]
        # print(anagrams)
    # Convert the dictionary values to a list of lists
    return list(anagrams.values())[::-1]

# Example usage
strs = ["ate", "nat", "bat", "eat", "tea", "tan"]
result = groupAnagrams(strs)
print(result)





# typically using all the original letters exactly once.

 

# Example 1:

# Input: s = "anagram", t = "nagaram"
# Output: true
# Example 2:

# Input: s = "rat", t = "car"
# Output: false


s = "anagram" 
t = "nagaram"

if len(s) != len(t):
    result = False

else:

    count_s={}
    count_t={}

    for char in s:
        count_s[char] = count_s.get(char, 0) + 1
    print(count_s)

    for char in t:
        count_t[char] = count_t.get(char, 0) + 1

    #result = count_s[char] == count_t[char]
    if count_s != count_t:
        print('this is not an Anagram')
    else:
        print('This is Anagram')
