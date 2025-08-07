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

nums = [5,2,0,3,0,1,6,0]
x = move_zero_right(nums)
print((x))


# Move Zeros to left 

num = [5,0,4,8,0,1,-2]

class Solution:
	def __init__(self,num):
		self.num = num
	def move_zeros_left(self):
		count = len(num) - 1
		for i in range(len(num) -1, -1, -1):
			if num[i] != 0:
				num[count],num[i] = num[i],num[count]
				count = count - 1
		return num
solver = Solution(num)
result = solver.move_zeros_left()
print(result)


# def move_zero(nums):
# 	non_zero = []
# 	for num in nums:
# 		if num != 0:
# 			non_zero.append(num)
# 	non_zero.sort()
# 	#print (non_zero)
# 	zero_count = nums.count(0)
# 	#print (zero_count)
	
# 	sorted_nums = non_zero + [0] * zero_count

# 	return sorted_nums

# nums = [0, 1, 0, 3, 12]
# x = move_zero(nums)
# print((x))


