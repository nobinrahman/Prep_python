# Problem#2:
# ========
# Facebook logo stickers cost $2 each from the company store. I have an idea.
# I want to cut up the stickers, and use the letters to make other words/phrases.
# A Facebook logo sticker contains only the word 'facebook', in all lower-case letters.
#
# Write a function that, given a string consisting of a word or words made up # of letters from the word 'facebook', outputs an integer with the number of # stickers I will need to buy.
#
# get_num_stickers('coffee kebab') -> 3
# get_num_stickers('book') -> 1
# get_num_stickers('ffacebook') -> 2
#
# You can assume the input you are passed is valid, that is, does not contain # any non-'facebook' letters, and the only potential non-letter characters # in the string are spaces.

def get_num_stickers(phrase):
    phrase = phrase.replace(" ", "")
    
    # Count letters needed
    needed_count = {}
    for ch in phrase:
        if ch in needed_count:
        	needed_count[ch] += 1
        else:
            needed_count[ch] = 1
    print(needed_count)

    # Count letters in one 'facebook' sticker
    sticker_count = {}
    for ch in 'facebook':
        if ch in sticker_count:
            sticker_count[ch] += 1
        else:
            sticker_count[ch] = 1
    print(sticker_count)

    # Figure out how many stickers needed
    max_stickers = 0
    for ch in needed_count:
        needed = needed_count[ch]
        if ch in sticker_count:
            available = sticker_count[ch]
            # ceiling division without math.ceil
            stickers = (needed + available - 1) // available
            if stickers > max_stickers:
                max_stickers = stickers
        else:
            # technically won't happen due to problem constraints
            return -1

    return max_stickers

print(get_num_stickers('coffee kebab'))  # ➝ 3
# print(get_num_stickers('book'))          # ➝ 1
# print(get_num_stickers('ffacebook'))     # ➝ 2

