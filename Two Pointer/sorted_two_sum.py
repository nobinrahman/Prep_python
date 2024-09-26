# Given a sorted array of unique integers 
# and a target integer, return true if there 
# exists a pair of numbers that sum to target, 
# false otherwise.


nums = [1, 2, 4, 6, 8, 9, 14, 15]

target = 13


# def two_sum(nums,target):
# 	for i in range(len(nums)):
# 		for j in range(len(nums)):
# 			if nums[i] + nums[j] == target:
# 				return([i,j])


# Efficient Method . You can use this method only if the list is sorted

def two_sum(nums,target):
	left = 0
	right = len(nums) - 1

	while left < right:
		currsum = nums[left] + nums[right]
		if currsum < target:
			left += 1
		if currsum > target:
			right -= 1
		if currsum == target:
			return ([left,right])



x = two_sum(nums,target)
print(x)



