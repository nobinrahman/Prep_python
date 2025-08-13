#Take a paragraph as Input and output the top three most repeated words

# Input paragraph
paragraph = "This is a sample paragraph. This paragraph contains some sample words for testing. Sample words are repeated to test this word count exercise."

def top_three_most_repeated_word(paragraph):
	"""
	This function will find the top three repeated words

	"""
	paragraph_lower = paragraph.lower()
	words = paragraph_lower.split()
	word_count = {}

	for word in words:
		if word in word_count:
			word_count[word] += 1
		else:
			word_count[word] = 1
	top_words = []

	for k,v in word_count.items():
		top_words.append((k,v))


	top_words.sort(key=lambda x:x[1], reverse=True)
	top_three = []

	for i in top_words[:3]:
		top_three.append(i[0])
	return top_three



x = top_three_most_repeated_word(paragraph)
print(x)

