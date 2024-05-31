###### 1 #####

# Bubble sort algorithm

# sort the below list in ascending order without using any built in function

# num = [5,4,8,0,1,2]

# num = [5,4,8,0,1,-2]
# #print(len(num))
# # num.sort()
# #print(len(num))

# for i in range (len(num)):
# 	#print(i)
# 	for j in range (len(num) - i -1):
# 		#print(j)
# 		if num[j] > num[j+1]:
# 			num[j],num[j+1] = num[j+1],num[j]


# print(num)

def bubble_sort(num):
	for i in range(len(num)):
		for j in range(len(num) - i -1):
			if num[j] > num[j+1]:
				num[j],num[j+1] = num[j+1],num[j]

	return num
num = [5,4,8,0,1,-2]
x = bubble_sort(num)
print(x)


##### 2 #####

def reverse_vowels(s):
    vowels = "aeiouAEIOU"
    vowel_positions = []
    vowel_chars = []

    # Collect the positions and characters of the vowels
    for i in range(len(s)):
        if s[i] in vowels:
            vowel_positions.append(i)
            vowel_chars.append(s[i])

    # Reverse the list of vowel characters
    reversed_vowel_chars = []
    for i in range(len(vowel_chars)-1, -1, -1):
        reversed_vowel_chars.append(vowel_chars[i])

    # Convert string to list to allow modification
    s_list = list(s)

    # Place the reversed vowels back into their original positions
    for i in range(len(vowel_positions)):
        s_list[vowel_positions[i]] = reversed_vowel_chars[i]

    # Convert list back to string
    reversed_s = ""
    for char in s_list:
        reversed_s += char

    return reversed_s

# Example usage
input_string = "education"
output_string = reverse_vowels(input_string)
print(output_string)  # Output: odicatuen


