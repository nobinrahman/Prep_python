s = 'hello, my name is nobin rahman, I am a software engineer in cisco systems'


def count_vowel(s):
	vowel ='aeiouAEIOU'
	vowel_count = {}
	for char in s:
		if char in vowel:
			if char in vowel_count:
				vowel_count[char] +=1
			else:
				vowel_count[char] = 1
	total_vowel = 0
	for v in vowel_count.values():
		total_vowel = total_vowel + v

	return vowel_count , total_vowel

x = count_vowel(s)
print(x)
