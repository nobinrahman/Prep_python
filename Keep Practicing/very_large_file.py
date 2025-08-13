# You are given a very large file to read. The newline character for the file is % 
# We want to read a specific line of the file. Provide a solution in O(N) + 1    [NOTE: O(N) + O(K) is not acceptable]
# Hint: we need to use python seek / tell/ read() functions.


def fileread(line_num):
    fp = open('testfile.txt', 'r')       # Open the file in read mode
    lineptr = []                         # List to store positions of line delimiters ('%')
    filesize = 0                         # Variable to keep track of total file size read

    while True:
        char = fp.read(1)                  # Read one character at a time
        if char == '':                    # If empty string returned, EOF reached, break loop
            break
        filesize += 1                   # Increment filesize counter by 1 for each character read
        if char == '%':                   # If character is the custom newline delimiter '%'
            lineptr.append(fp.tell())   # Append current file cursor position (after '%') to lineptr

    lineptr = [0] + lineptr             # Add 0 at the beginning to mark start of first line
    
    # Check if requested line number is beyond total lines available
    if line_num > len(lineptr) - 1:
        print("No such line")           # Print error message if line does not exist
        return                         # Exit the function
    
    # Move file cursor to the start position of the requested line (0-based index)
    fp.seek(lineptr[line_num - 1])     
    # Read the content of the requested line
    # Length to read is difference between start of current line and next line minus 1 (exclude '%')
    print(fp.read(lineptr[line_num] - lineptr[line_num - 1] - 1))

def main():
    fileread(1)    # Read line 1
    fileread(2)    # Read line 2
    fileread(3)    # Read line 3
    fileread(4)    # Read line 4
    fileread(5)    # Read line 5
    fileread(7)    # Read line 7
    fileread(8)    # Read line 8
    fileread(9)    # Read line 9

if __name__ == '__main__':
    main()



# read() : Reads content from a file.
# tell() : Returns the current position of the file cursor.
# seek(offset, whence=0) : Moves the file cursor to a new position.
