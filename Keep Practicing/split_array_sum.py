# Given an integer array nums, return true if you can partition the array into two subsets such that 
# the sum of the elements in both subsets is equal or false otherwise.

# Example 1:
# Input: nums = [1,5,11,5]
# Output: true
# Explanation: The array can be partitioned as [1, 5, 5] and [11].

# Example 2:
# Input: nums = [1,2,3,5]
# Output: false
# Explanation: The array cannot be partitioned into equal sum subsets.



def canPartition(nums):
    total = sum(nums)
    if total % 2 != 0:
        return False
    
    target = total // 2
    # n = len(nums)
    dp = [False] * (target + 1)
    dp[0] = True
    
    for num in nums:
        for i in range(target, num - 1, -1):
            dp[i] = dp[i] or dp[i - num]
    
    return dp[target]

print(canPartition([1,5,11,5]))
print(canPartition([1,2,3,5]))

print(canPartition([8,6,2]))

# Time Complexity: O(n · target)
# Space Complexity: O(target)


# If total sum is odd, return False — you can’t split odd into two equal parts.

# Use DP to check if a subset exists with sum = total // 2.

# dp[i] means: Can we make sum i using some elements?

# Start with dp[0] = True (zero sum is always possible).

# For each number, update dp[i] = True if dp[i - num] was already possible.

# At the end, return dp[target].