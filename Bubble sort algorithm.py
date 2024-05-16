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

