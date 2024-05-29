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


##### 3 #####

# Given an integer array nums, move all 0's to the end of it while maintaining the relative order of the non-zero elements.

# Note that you must do this in-place without making a copy of the array.

 

# Example 1:

# Input: nums = [0,1,0,3,12]
# Output: [1,3,12,0,0]
# Example 2:

# Input: nums = [0]
# Output: [0]

def moving_zero_to_right(nums):
	count = 0 
	for i in range(len(nums)):
		if nums[i] != 0:
			nums[count],nums[i] = nums[i],nums[count]
			count = count + 1
	return nums
nums = [0, 1, 0, 3, 12]
x = moving_zeros_to_right(nums)
print(x)

# Input: nums = [0,1,0,3,12]
# Output: [0,0,1,3,12]

def moving_zero_to_left(nums):
	count = 0 
	for i in range(len(nums)-1, -1, -1):
		if nums[i] != 0:
			nums[count],nums[i] = nums[i],nums[count]
			count = count - 1
	return nums
nums = [0, 1, 0, 3, 12]
x = moving_zeros_to_left(nums)
print(x)

# Input: nums = [0,1,0,3,12]
# Output: [0,0,1,3,12]

def moving_zero_and_sorted(nums):
	non_zero = []
	for num in nums:
		if num = != 0
		non_zero.append(num)
	non_zero.sorted()
	zero_count = nums.count(0)
	sorted_nums = non_zero + [0] * zero_count
	return sorted_nums
nums = [5,2,0,3,0,1,6,0]
x = moving_zeros_to_left(nums)
print(x)


