# Given an m x n matrix board where each cell is a battleship 'X' or empty '.', return the 
# number of the battleships on board.

# Battleships can only be placed horizontally or vertically on board. 
# In other words, they can only be made of the shape 1 x k (1 row, k columns) 
# or k x 1 (k rows, 1 column), where k can be of any size. 
# At least one horizontal or vertical cell separates between two battleships (i.e., there are no adjacent battleships).

# Example 1:

# Input: board = [
# ["X",".",".","X"],
# [".",".",".","X"],
# [".",".",".","X"]
# ]
# Output: 2
# Example 2:

# Input: board = [["."]]
# Output: 0

def countBattleships(board):
    m, n,count  = len(board), len(board[0]), 0

    
    for i in range(m):
        for j in range(n):
            if board[i][j] == 'X':
                if i > 0 and board[i-1][j] == 'X':
                    continue  # part of a vertical battleship
                if j > 0 and board[i][j-1] == 'X':
                    continue  # part of a horizontal battleship
                count += 1
    return count

print(countBattleships([["X",".",".","X"],[".",".",".","X"],[".",".",".","X"]]))

print(countBattleships([["."]]))


# Time Complexity: O(m · n)
# Space Complexity: O(1)


# 🧠 What Is the Problem?
# You are given a grid like this:

# board = [
#     ['X', '.', '.', 'X'],
#     ['.', '.', '.', 'X'],
#     ['.', '.', '.', 'X']
# ]
# Think of this grid as a sea map.

# 'X' = part of a battleship

# '.' = empty water

# You need to count how many battleships there are.

# 🛳 What Makes a Battleship?
# A battleship is 1 row or 1 column of 'X's

# It must be:

# Vertical like:


# X
# X
# X
# or Horizontal like:


# X X X
# Battleships do not touch each other (no touching sides or corners)

# 🔍 Visual of the Grid:
# Let’s look at this:


# Row 0:  X  .  .  X
# Row 1:  .  .  .  X
# Row 2:  .  .  .  X
# We can see:

# One ship is a single 'X' at (0,0)

# Another ship is vertical, made of 'X' at:

# (0,3)

# (1,3)

# (2,3)

# So total ships = 2

# 💡 How Do We Count Just 2 Ships?
# Instead of counting every 'X', we only count a 'X' if it is the first cell of a ship.

# ❓ How do we know it’s the first cell?
# We ask:

# Is there an 'X' above it? → then it's part of a vertical ship, so skip it

# Is there an 'X' to the left? → then it's part of a horizontal ship, so skip it

# If there’s no 'X' above or to the left, it means:
# ✅ This is the start of a new ship → we count it.

# 🔁 Let’s Trace the Code with the Example

# board = [
#     ['X', '.', '.', 'X'],
#     ['.', '.', '.', 'X'],
#     ['.', '.', '.', 'X']
# ]
# Step-by-step loop:
# i=0, j=0 → cell is 'X'
# No cell above or to the left
# ✅ Count it → count = 1

# i=0, j=1 → cell is '.' → skip
# i=0, j=2 → cell is '.' → skip
# i=0, j=3 → cell is 'X'
# No 'X' above or left
# ✅ Count it → count = 2

# i=1, j=3 → cell is 'X'
# 'X' above at (0,3) → same vertical ship
# ❌ Skip

# i=2, j=3 → cell is 'X'
# 'X' above at (1,3) → same ship
# ❌ Skip

# 🎯 Final count: 2 ships

