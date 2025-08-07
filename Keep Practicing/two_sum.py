def twoSum(nums, target):
	for i in range(len(nums)):
		for j in range(i+1, len(nums)):
			if nums[i] + nums[j] == target:
				return [i,j]

nums=[2, 7, 11, 15]
target=9
result = twoSum(nums, target)
print (result)



def TwoSum(nums,target):
	left = 0 
	right = len(nums) - 1

	while left < right:
		current_sum = nums[left] + nums[right]
		if current_sum == target:
			return (left, right)
		if current_sum < target:
			left += 1
		else:
			right -= 1

nums=[2, 7, 11, 15]
target = 9 
x =TwoSum(nums,target)
print(x)



#When the list is not sorted

def twoSum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        diff = target - num
        if diff in seen:
            return [seen[diff], i]
        seen[num] = i


