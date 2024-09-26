# 283. Move Zeroes

# Given an integer array nums, move all 0's to the end of it while maintaining the relative order of the non-zero elements.

# Note that you must do this in-place without making a copy of the array.

 

# Example 1:

# Input: nums = [0,1,0,3,12]
# Output: [1,3,12,0,0]
# Example 2:

# Input: nums = [0]
# Output: [0]



def move_zeroes_to_right(nums):

	left = 0 
	
	for right in range(len(nums)):
		if nums[right] != 0 :
			nums[right], nums[left] = nums[left], nums[right]
			left = left + 1
	return nums


nums = [0,1,0,3,12]

x = move_zeroes_to_right(nums)

print(x)


def moving_zeros_to_left(nums):
    count = 0 
    for i in range(len(nums)-1,-1,-1):
        if nums[i] != 0:
            nums[count], nums[i] = nums[i], nums[count]
            count = count - 1
    return nums

nums = [0, 1, 0, 3, 12]
x = moving_zeros_to_left(nums)
print(x)















