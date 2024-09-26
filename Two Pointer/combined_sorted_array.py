# Given two sorted integer arrays arr1 and arr2, 
# return a new array that combines both of them 
# and is also sorted.


arr1 = [1,4,7,20]

arr2 = [3,4,6]



# def combined_array(arr1,arr2):
# 	arr = sorted(arr1 + arr2)
# 	return arr


# Efficinet Method. Since the arrays are sorted Two pointers Algorithm can be used



def combined_array(arr1,arr2):
	i = j = 0
	ans = []
	while i < len(arr1) and j < len(arr2):
		if arr1[i] < arr2[j]:
			ans.append(arr1[i])
			i = i + 1
		else:
			ans.append(arr2[j])
			j = j + 1

	# Now one of the list will be exhausted. so we need to make sure 
	# we exhaust the other list. Thats why we have to put extra code 
	# for bot the list as we dont know which one will be exhausted first 

	while i < len(arr1):
		ans.append(arr1[i])
		i += 1

	while j < len(arr2):
		ans.append(arr2[j])
		j += 1
	return ans



x = combined_array(arr1,arr2)
print(x)