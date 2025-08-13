# A group of animators all sign for facebook accounts at the same time. They immediately start sending each other friend requests, in accordance with the ancient rules.

# 1. An animator will only send a friend request to another animator if the recipient is atleast (x/2 + 7) of the senders age. 
# For example, a 200 year old centaur can only send friend requests to animators that are atleast 107 years old.
# 2. An animator will not send a friend request to another animator that is older than it is.
# 3. An animator over 100 years old will not send a friend request to a recipient under 100 years old.
# 4. If any of the conditions for sending the friend request is not met, no friend request will be sent.

# Write a function that, given an array of animator ages, returns an integer of the total number of friend requests that the group of animators will send to each other.
# Examples
# count_friend_requests([120,110]) => 1
# # friend requests        1, 0
# count_friend_requests([120,110,99]) => 1
# # friend requests        1, 0, 0
# count_friend_requests([120,45,230,400,88,300, 101]) => 4
# # friend requests        1, 0, 0, 2,   0, 1,   0


def friend_request(ages):
    total_request = 0

    for sender_age in ages:              # loop over each animator as sender
        for recipient_age in ages:       # loop over each animator as recipient
            if recipient_age == sender_age:
                continue                 # Skip if same animator (no friend request to self)
            
            if recipient_age < sender_age / 2 + 7:
                continue                 # Rule 1: recipient too young for sender
            
            if recipient_age > sender_age:
                continue                 # Rule 2: sender will not send to older animator
            
            if sender_age > 100 and recipient_age < 100:
                continue                 # Rule 3: sender over 100 will not send to recipient under 100
            
            total_request += 1          # If none of the above conditions were true, send friend request
            
    return total_request

print(friend_request([120,110]))


# Time Complexity   O(n²) 
# Space Complexity  O(1)  
