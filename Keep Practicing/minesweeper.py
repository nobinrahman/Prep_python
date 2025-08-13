#minesweeper


# Explanation:
# Define Grid Dimensions:

# m is the number of rows.
# n is the number of columns.
# k is the number of mines to place on the grid.
# Initialize the Grid:

# Create a 2D list (list of lists) called grid filled with zeros to represent the grid without any mines.
# Place the Mines:

# Use a while loop to place k mines. The loop continues until mines_placed equals k.
# Randomly select a cell using random.randint for both the row (i) and the column (j).
# Check if the selected cell already has a mine (grid[i][j] == 0). If not, place a mine there (grid[i][j] = 1) and increment mines_placed.
# Print the Grid:

# Iterate over each row in the grid and print it to display the final grid with mines.
# This code should be simple and easy for a beginner to follow and understand how to randomly place mines on a grid.

import random  # Importing the random module to use the random.choice function

# Define the dimensions of the grid
# m = 5  # Number of rows
# n = 4  # Number of columns
# k = 6  # Number of mines
m,n,k = 5,4,6
# Initialize the grid with zeros
grid = []
for i in range(m):
    row = []
    for j in range(n):
        row.append(0)
    grid.append(row)

# print(grid)

# Place the mines randomly on the grid
mines_placed = 0
while mines_placed < k:
    # Randomly choose a cell
    i = random.randint(0, m - 1)
    j = random.randint(0, n - 1)
    # If the cell does not already have a mine, place one
    if grid[i][j] == 0:
        grid[i][j] = 1
        mines_placed += 1
# Print the grid
for row in grid:
    print(row)

# Time Complexity: O(k) on average (k = number of mines)
# Space Complexity: O(m · n)

