# You are given a CSV file containing Instagram post data with the following 
# columns: username, post_id, likes, comments, and shares. Compute an engagement 
# score for each post using the formula: engagementScore = (likes^1.2 + comments^1.3 + shares^1.4) / 3 
# Then, determine the top 10 posts with the highest scores and output these posts 
# by displaying their post_id along with the computed engagement score, sorted in descending order.



import csv
import math



def top_ten_post(file_path):
	ig_post = []
	with open(file_path, mode='r', encoding='utf-8-sig') as file:
		content= csv.DictReader(file)
		for row in content:
			username = row['username']
			post_id = (row['post_id'])
			likes = int(row['likes'])
			comments = int(row['comments'])
			shares = int(row['shares'])
			# engagementScore = (likes^1.2 + comments^1.3 + shares^1.4) / 3 
			score = (math.pow(likes, 1.2) + math.pow(comments, 1.3) + math.pow(shares, 1.4)) / 3
			ig_post.append((post_id,score))

	ig_post.sort(key=lambda x:x[1], reverse=True)
	return ig_post[:10]

file_path = "/Users/krahman/Documents/Cisco/Documents/Personal/Interview Prep/Automation/Meta Question/Instagram_post.csv"
x = top_ten_post(file_path)
for post, score in x:
    print("Post ID:", post, "Score:", score)


for i in x:
	print(i[0],i[1])