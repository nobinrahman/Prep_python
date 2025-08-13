#Write a function to sort a list of integers that looks like this [5,2,0,3,0,1,6,0] to [1,2,3,5,6,0,0,0] in the most efficient way.

nums = [5,2,0,3,0,1,6,0]
# print(sorted(nums))


def move_zero_right(nums):

	count = 0 
	for i in range(len(nums)):
		if nums[i] != 0:
			#nums[count],nums[i] = nums[i],nums[count]
			nums[i],nums[count] = nums[count],nums[i]
			count = count + 1

	return nums


# Time Complexity: O(n)
# Space Complexity: O(1)



nums = [5,2,0,3,0,1,6,0]
x = move_zero_right(nums)
print((x))


# Move Zeros to left 

nums = [5,0,4,8,0,1,-2]

class Solution:
	def __init__(self,nums):
		self.num = nums
	def move_zeros_left(self):
		count = 0
		for i in range(len(nums)):
			if nums[i] == 0:
				nums[i],nums[count] = nums[count],nums[i]
				count = count + 1
		return nums
solver = Solution(nums)
result = solver.move_zeros_left()
print(result)





