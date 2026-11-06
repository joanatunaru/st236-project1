import csv
from copy import deepcopy

groupNumber = 14
groupName = {'Isaac' : 'Person 1 Username',\
             'Jasper' : 'Person 2 Username',\
             'Joana' : 'Person 3 Username',\
             'Siddarth' : 'Person 4 Username'}

class OutOfBoundsError(Exception):
    """
    Raised when a correctly formatted position refers to a cube that is not on the 5x5x5 board.

    The board's valid co-ordinates are columns 'A'-'E', rows 'a'-'e' and levels '1'-'5'.
    This error means the input was well-formed but at least one co-ordinate lies outside
    these ranges ('E0a', '3Gb') or that an object would extend beyond the board's edge.
    """
    pass

class InvalidInputFormat(Exception):
    """
    Raised when an input is not in the expected format, regardless of the values it contains.

    For a position, this means it isn't a string, it is not exactly 3 characters long, or does not consist
    of exactly one uppercase letter, exactly one lowercase letter and exactly one digit (in any order).
    examples: 123, 'Ab', 'BdA2', 'AB1'

    Also used within placeSubs(board, name, pos) when pos is given in an invalid format.
    """
    pass

class SubmarineOverlapError(Exception):
    """
    Raised within placeSubs(board, name, pos) when a cell we attempt to place a new sub within already contains
    another placed sub.
    """
    pass
class MoveNotMade(Exception):
    ''' 
    '''
    pass
def emptyBoard():
    """
    Creates a new, empty 5x5x5 board.

    Input:
        None.

    Output:
        (list) a 5x5x5 nested list accessed as board[level][row][col],
        with every cell 0. Every level and row is a separate list.

    Exceptions:
        None raised.
    """
    return [[[0] * 5 for _ in range(5)] for _ in range(5)]

def newEmptyGame(p1, p2, ShowSubs = []):
    """
    Creates a new, empty game.

    Inputs:
        p1: (str) name of Player 1
        p2: (str) name of Player 2
        ShowSubs: (list, optional) one of [], [1], [2], [1,2]; default []. A copy is stored.

    Output:
        (dict) a game dictionary with keys:
            `Player 1`: the name of the Player 1
            `Player 2`: the name of the Player 2
            `Who`: an integer, 1 or 2, representing whose turn is next. Always initialised to 1 so Player 1 is first.
            `ShowSubs`: list of ints ([], [1], [2], [1,2]) that says which player's subs should be printed.
                [] = neither, [1] = Player 1 only, [2] = Player 2 only, [1,2] = both.
            `Player 1 Board`: 3D list representing the board showing Player 1's submarines & a record of Player 2's shots.
                Indexed 5x5x5 & accessed as board[level][row][col], every cell 0.
            `Player 2 Board`: Same as above but shows Player 2's submarines & a record of Player 1's shots.

    Exceptions:
        None raised
    """
    game = {'Player 1': p1,
            'Player 2': p2,
            'Who': 1,
            'ShowSubs': list(ShowSubs),  # copy, so the shared mutable default isn't stored or modified
            'Player 1 Board': emptyBoard(),
            'Player 2 Board': emptyBoard()}

    return game

def posToIndex(place):
    """
    Takes a string place and returns a list of three integers [i, j, k], representing the
    position of a cube using the co-ordinate system compatible with the board.

    Input:
        place (str): a position on the board, written as exactly 3 characters:
            one uppercase letter giving the column (A-E)
            one lowercase letter giving the row (a-e)
            one digit giving the level (1-5)
            in any order, 'Aa1', '1aA' and 'a1A' all refer to the same cube within the board
            Any other input raises an exception

    Output:
        (list of int) [i, j, k], each integer from 0 to 4, where
            i is the column index (A-E -> 0-4),
            j is the row index (a-e -> 0-4),
            k is the level index (1-5 -> 0-4),
            so the cube at place is board[k][j][i]
            example: 'Aa1' -> [0, 0, 0], 'cE3' -> [4, 2, 2]

    Exceptions:
        InvalidInputFormat is raised in any of these cases.
            place is not a string
            place is not 3 characters long
            place doesn't contain exactly one uppercase letter, exactly one lowercase letter and exactly one digit, in any order

        OutOfBoundsError is raised when:
            place is a valid input format (all 3 rules above are met), but refers to a cube not in the board,
            i.e. the uppercase letter is not in A-E, the lowercase letter is not in a-e, or the digit is not
            in 1-5. 'D0a', '2Fa'

        Format gets checked before bounds, so an input that is both malformed and out of range ('FG9') raises InvalidInputFormat
    """
    if not isinstance(place, str):
        raise InvalidInputFormat('Invalid input format. Place should be a string.')
    if len(place) != 3:
        raise InvalidInputFormat('Invalid input format. Place should be 3 characters long.')

    axisLabels = {"Upper",
                  "Lower",
                  "Number"}

    for c in place:
        if c.isupper():
            axisLabels.discard("Upper")
            upperLetter = c
        elif c.islower():
            axisLabels.discard("Lower")
            lowerLetter = c
        elif c.isdigit():
            axisLabels.discard("Number")
            digit = c

    if axisLabels:
        raise InvalidInputFormat("Invalid input format. Place should be a lowercase letter, an uppercase letter and a digit.")

    # By now, we know 'place' is a 3 character long string, with one lowercase letter, one uppercase letter and one digit.
    # Any error in 'place' from now must imply an OutOfBoundsError. We must verify that our positions now fall within the 5x5x5 board.

    i = 'ABCDE'.find(upperLetter)
    j = 'abcde'.find(lowerLetter)
    k = '12345'.find(digit)

    if -1 in [i, j, k]:
        raise OutOfBoundsError("Place code contains valid syntax but an invalid placement (index not in [0-4] for col, row or level)")
    return [i, j, k]

# 'up' / 'down': level 1 -> 5 / level 5 -> 1
# 'right' / 'left': column A -> E / column E -> A
# 'forwards' / 'backwards': row a -> e / row e -> a
STEPS = {'up': [0, 0, 1],
         'down': [0, 0, -1],
         'left': [-1, 0, 0],
         'right': [1, 0, 0],
         'forwards': [0, 1, 0],
         'backwards': [0, -1, 0]}  # Dict to indicate which axis a string direction refers to. Used to construct co-ordinates for what cells a sub should be placed in.


def placeSubs(board, name, pos):
    """
    Places a submarine on a board, modifying the board in place. Validates all input before changing board.

    Inputs:
        board (list): a 5x5x5 board (created by emptyBoard), accessed as board[level][row][col]. Modified directly.
        name (str): the submarine's name, one of 'S1' to 'S5' which we assume as valid. Written into every cube the sub occupies.
        pos (dict): the submarine's placement, with keys:
            'anchor' (str): the cube at one end of the submarine, parsed in any format accepted by posToIndex
            'direction' (str): the direction the submarine extends in, one of:
                'up' / 'down': level 1 -> 5 / level 5 -> 1
                'right' / 'left': column A -> E / column E -> A
                'forwards' / 'backwards': row a -> e / row e -> a
            'length' (int): the number of cubes the submarine occupies, including the anchor. Must be a positive integer.
            example: pos = {'anchor': 'aE1', 'direction': 'up', 'length': 5}

    Output:
        None, board modified directly.

    Exceptions:
        InvalidInputFormat: raised if:
            pos is not a dict containing the keys 'anchor', 'direction' and 'length'
            if the direction isn't one of the six listed above
            if the anchor isn't in a valid format
            if the length isn't a positive integer
        OutOfBoundsError: raised if the anchor is not on the board, or if the submarine would extend beyond the scope of the board (even partially)
        SubmarineOverlapError: raised if any cube the submarine would cover is already occupied by another submarine

        All checks get completed before the board is modified, so if any exception is raised the board will be left unchanged
    """
    if not isinstance(pos, dict) or not {'anchor', 'direction', 'length'} <= pos.keys():
        raise InvalidInputFormat("pos must be a dict with keys 'anchor', 'direction', 'length'.")
    if not isinstance(pos['direction'], str) or pos['direction'] not in STEPS:
        raise InvalidInputFormat("Direction must be one of " + ', '.join(STEPS.keys()) + ".")

    anchor_i, anchor_j, anchor_k = posToIndex(pos['anchor'])  #anchor must be a valid on-board cube, otherwise posToIndex has already raised an exception
    length = pos['length']

    if not isinstance(length, int) or length <= 0:
        raise InvalidInputFormat("Length must be a positive integer, instead got " + str(length) + ".")

    di, dj, dk = STEPS[pos['direction']]
    cells = [[anchor_i + n * di, anchor_j + n * dj, anchor_k + n * dk] for n in range(length)]

    #have our cells and a valid anchor point, we validate that our sub is on the board and that we have no overlap between subs

    if not all(0 <= v <= 4 for v in cells[-1]):
        raise OutOfBoundsError("Attempt to place sub " + name + " in an out of bounds cube rejected.")
    if any(board[k][j][i] != 0 for i, j, k in cells):
        raise SubmarineOverlapError(
            "Attempt to place sub " + name + ", rejected due to overlap with another submarine.")
    for i, j, k in cells:
        board[k][j][i] = name

# Task 4

'''
converts 1 row of 5 board cells into a string for display, each cell is represented by two character positions, followed by a vertical
separator. This keeps the columns aligned when the board is printed
inputs:
row (list): A list containing the 5 cells in one board row, each cell is expected to be 0 (empty), "M" (a missed shot), "S1" to "S5"
(an unhit submarine) or "H1" to "H5" (a hit sub).
showSubs (boolean): controls if unhit submarine parts are visible.
False hides "S1" to "S5", True displays them
showSubNum (boolean): controls if the submarine number is displayed.
False displays only the letter "S" or "H", True displays the full cell value, such as "S2" or "H2".

Return value:
(str) A representation of the row. The input row is not modified.
Exceptions:
No custom exceptions are raised. The function assumes that row contains valid board cell values and that the two display options are booleans.
Invalid input may cause a built-in exception (for example, TypeError).
'''
def boardRowText(row, showSubs, showSubNum):    
    result = ''
    for cell in row:
        if cell == 0:
            text = '  '
        elif cell == 'M':
            text = 'M '
        elif cell[0] == 'S' and showSubs == False:
            text = '  '
        elif showSubNum == False:
            text = cell[0] + ' '
        else:
            text = cell
        result = result + text + '|'
    return result



'''
Creates a printable string showing all 5, 5x5 layers of a 5x5x5 board
The layers are displayed next to one another. Each layer has columns A-E and rows a-e, so that a player can identify a cube by its coordinates.

Inputs:
board (list): A 5x5x5 nested list, accessed as board[level][row][column]
It is expected to contain valid board cell values.

showSubs (boolean, optional): if unhit submarine segments should be visible - defaults to false

showSubNum (boolean, optional): if submarine and hit segment numbers should be visible - defaults to false

Return value:
(str) The complete formatted board. The board itself is not modified, the function returns the string - it does not print it on the screen

Exceptions:
No custom exceptions are raised. The function assumes board has 5 layers, each containing 5 rows of 5 valid cells
Invalid board dimensions or values might cause a built-in exception such as IndexError or TypeError.
'''
def printBoard(board, showSubs=False, showSubNum=False):
    result = ''
    for k in range(5):
        result = result + 'Layer ' + str(k + 1) + '             '
    result = result + '\n'
    result = result + ' |A |B |C |D |E |   ' * 5 + '\n'

    row = 'abcde'
    for j in range(5):
        for k in range(5):
            result = result + row[j] + '|'
            result = result + boardRowText(board[k][j], showSubs, showSubNum)
            result = result + '   '
        result = result + '\n'
    return result

# Task 5
class IndexOutOfRange(Exception):
    pass
'''
Purpose:
Converts a list of numerical board indices into the right coordinate string - reverse operation of posToIndex()

Inputs:
ind (list): A list of exactly 3 integers in the order [column_index, row_index, level_index]
Each integer must be between 0 and 4
for example [0, 0, 0] identifies Aa1.

Return value:
(str) A 3-character coordinate in the format uppercase column letter lowercase row letter, digit level. For example, [4, 2, 2] returns "Ec3".
The input list is not modified.

Exceptions:
IndexOutOfRange: raised if ind is not a list of 3 three elements, or if any element is not an integer from 0 to 4 inclusive.
'''
def indexToPos(ind):
    if type(ind) != list or len(ind) != 3:
        raise IndexOutOfRange
    for number in ind:
        if type(number) != int or number < 0 or number > 4:
            raise IndexOutOfRange

    col = 'ABCDE'
    row = 'abcde'
    num = '12345'
    return col[ind[0]] + row[ind[1]] + num[ind[2]]

# Task 6
'''
Writes the contents of a 5x5x5 board to an already-open CSV 
Each board row is written as one CSV row. The order is level first, then row, matching the board[level][row][column] structure.

Inputs:
writer: A CSV normally created using csv.writer(file) It must provide a writerow() method
board (list): A 5x5x5 nested list containing the board's cell values.

Return value:
None - the function writes to the supplied CSV writer and does not modify the board.

Exceptions:
No custom exceptions are raised. Errors from writer.writerow(), such as errors caused by an invalid writer or an underlying file problem
are allowed to pass to the caller.
'''
def writeBoard(writer, board):
    for layer in board:
        for row in layer:
            writer.writerow(row)

'''
Purpose:
Saves a game dictionary to a CSV file
The file is opened in write mode, so an existing file with the same name will be overwritten.

Inputs:
game (dict): A game dictionary containing the keys "Player 1", "Player 2", "Who", "ShowSubs", "Player 1 Board" and "Player 2 Board"
The two board values must each be 5x5x5 nested lists
fname (str or path-like): The filename or path where the CSV file should be written

Return value:
None - the game dictionary and its boards are not modified.

Exceptions:
No custom exceptions are raised. File-related exceptions, such as FileNotFoundError, PermissionError or other OSError subclasses, may be raised by open() 
and are passed to the caller. Invalid game data may cause a built-in exception such as KeyError or TypeError
'''

def saveGame(game, fname):
    with open(fname, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        for key in ['Player 1', 'Player 2', 'Who']:
            writer.writerow([key, game[key]])
        writer.writerow(['ShowSubs'] + game['ShowSubs'])

        for key in ['Player 1 Board', 'Player 2 Board']:
            writer.writerow([key])
            writeBoard(writer, game[key])

# Task 7

'''
Purpose:
Reconstructs 1 5x5x5 board from 25 consecutive rows of CSV data.
The first 5 CSV rows form level 1, the next 5 form level 2, and so on until all 5 levels have been reconstructed.

Inputs:
data (list): The complete CSV data, usually produced by list(csv.reader(file)). Each element is a CSV row (a list of strings).
start (int): The index in data at which the 25 board rows begin.

Return value:
(list) A new 5x5x5 board in the format board[level][row][column]. CSV text "0" is converted to integer 0 - all other cell values remain strings. 
The original data is not modified.

Exceptions:
No custom exceptions are raised. IndexError may occur if data does not contain all 25 rows from start onwards. The function assumes each CSV row contains exactly five cells
'''
def readBoard(data, start):
    board = []
    layer = []
    for position in range(start, start + 25):
        row = []
        for cell in data[position]:
            if cell == '0':
                row.append(0)
            else:
                row.append(cell)
        layer.append(row)
        if len(layer) == 5:
            board.append(layer)
            layer = []
    return board

def loadGame(fname):
    with open(fname, 'r', newline='', encoding='utf-8') as file:
        data = list(csv.reader(file))

    game = {}
    game['Player 1'] = data[0][1]
    game['Player 2'] = data[1][1]
    game['Who'] = int(data[2][1])
    game['ShowSubs'] = []
    for i in range(1, len(data[3])):
        game['ShowSubs'].append(int(data[3][i]))

    game['Player 1 Board'] = readBoard(data, 5)
    game['Player 2 Board'] = readBoard(data, 31)
    return game

#task 8
'''
function to find every cube on a player's board that has not been fired at yet
an empty cell (0) and an unhit submarine ("S1" to "S5") are valid targets
miss ("M") or hit ("H1" to "H5") is not a valid target

Inputs:
board (list): A 5x5x5 board accessed as board[level][row][column]
each cell is expected to contain a valid board value

Return value:
(list of str) A list of coordinate strings, each in the format uppercase column, lowercase row, level digit ("Aa1")
the coordinates are returned in level, row, column traversal order
the input board is not modified
an empty list is returned if there are no valid moves

Exceptions:
No custom exceptions are raised
'''
col = "ABCDE"
row = "abcde"
num = "12345"
valid = ["S1", "S2", "S3", "S4", "S5"]
def findValidMoves(board):
    moves = []
    for k in range(5):
        for j in range(5):
            for i in range(5):
                if board[k][j][i] == 0 or board[k][j][i] in valid:
                    place = col[i] + row[j] + str(k+1)
                    moves.append(place)
    return moves

#task 9
'''
Purpose:
applies one shot to the opponent's board and returns the updated game
- player 1 fires at player 2's board
- player 2 fires at player 1's board

build a separate dictionary so that the original game is not changed
the board lists need to be copied at every level: copying only the outer list would leave the inner rows shared with the original game

a shot at an empty cell is recorded as a miss ("M")
a shot at a submarine changes its value from "Sx" to "Hx", where x is the submarine number
the turn is then passed to the other player

Inputs:
game (dict): a valid game dictionary containing "Who", "Player 1 Board", "Player 2 Board", "Player 1", "Player 2" and "ShowSubs"
"Who" = 1 or 2
each board must be a 5x5x5 nested list

move (str): a coordinate identifying the cube to fire at, it must be exactly 3 characters: one uppercase column A-E, one lowercase
row a-e and one level digit 1-5, in any order accepted by posToIndex()

Return value:
(dict) a new game dictionary containing the result of the shot and the updated turn
the original game dictionary, its boards and its ShowSubs list are not modified

Exceptions:
MoveNotMade: raised if Who is not 1 or 2, if move has an invalid format or refers to a position outside the board, if the selected cell has
already been fired at (M or H1-H5), or if the selected cell contains a value other than 0 or S1-S5
Other built-in exceptions may occur if game is missing required keys or its boards do not have the expected 5x5x5 structure

'''

hit = ["H1", "H2", "H3", "H4", "H5"]

def makeMove(game, move):
    new = deepcopy(game)
    if game["Who"] == 1:
        boardName = "Player 2 Board"
    else:
        boardName = "Player 1 Board"
    
    #convert the coordinate string into indices
    #posToIndex raises InvalidInputFormat or OutOfBoundsError for bad input
    try:
        i, j, k = posToIndex(move)
    except Exception:
        raise MoveNotMade

    value = new[boardName][k][j][i]

    if value == "M" or value in hit:
        raise MoveNotMade

    elif value == 0:
        new[boardName][k][j][i] = "M"

    elif value in valid:
        new[boardName][k][j][i] = "H" + value[1]

    #only two players so 3 - Who changes 1 to 2 and 2 to 1
    new["Who"] = 3 - game["Who"]
    return new


#task10
'''
we check whether either player has won by counting the hit submarines on each player's board
each player has 17 submarine parts in total
a player wins when all 17 parts on their own board have been hit by the opponent

Inputs:
game (dict): a valid game dictionary containing "Player 1 Board" and "Player 2 Board"
each board must be a 5x5x5 nested list whose cells use the values 0, S1-S5, H1-H5 or M

Return value:
(int):
1 if Player 1 has won (all 17 on Player 2's board are hit)
2 if Player 2 has won (all 17 on Player 1's board are hit)
0 if neither player has won
the game dictionary and both boards are not modified

Exceptions:
no custom exceptions are raised
the function assumes both board keys exist and each board has the expected 5x5x5 structure
missing keys cld ause KeyError and incorrectly shaped boards may cause IndexError.
'''


def isWinner(game):
    board1 = game["Player 1 Board"]
    board2 = game["Player 2 Board"]
    count1 = 0
    count2 = 0

    for k in range(5):
        for j in range(5):
            for i in range(5):
                if board1[k][j][i] in hit:
                    count1 += 1
                if board2[k][j][i] in hit:
                    count2 += 1

    if count1 == 17:
        return 2
    elif count2 == 17:
        return 1
    else:
        return 0


# Task 11

def suggestMove(board):
    '''
    suggests a move from the list of valid moves
    '''
    validMoves = findValidMoves(board) #Uses Task 8 find valid moves to suggest a move
    return validMoves[0]


# Task 12

def askForPos(length):
    '''
    asks for the position of the submarine. Created a new function to make the code concise
    '''
    anchor = input("Enter anchor: ")
    direction = input("Enter direction: ") 
    return {"anchor": anchor, "direction": direction, "length": length}

def computerSubs(board):
    '''
    hardcoded locations for the computer submarines
    '''
    pos = [{'anchor': 'aA1', 'direction': 'up', 'length': 5}, {'anchor': 'aB1', 'direction': 'up', 'length': 4}, 
           {'anchor': 'aC1', 'direction': 'up', 'length': 3}, {'anchor': 'aD1', 'direction': 'up', 'length': 3}, 
           {'anchor': 'aE1', 'direction': 'up', 'length': 2}]
    for i in range(1,6):
        name = "S" + str(i)
        placeSubs(board, name, pos[i-1])

def playGame():
    '''
    Loads an existing game or initialises a new one then plays it.
    '''
    print("Enter Player 1 Name: ")
    name1 = input()
    if name1 == "load": #checks if the players want to start a new game or load an existing game
        while True: #load existing game, check if the file exists
            try:
                print("Enter file name: ") 
                thisGame = loadGame(input())
                break
            except:
                print("There is no file with this name. Try again")
    else: #asks for player information and submarine positions for the new game
        print("Enter Player 2 Name: ") 
        name2 = input()
        thisGame = newEmptyGame(name1, name2, ShowSubs = [])
        length = [5,4,3,3,2] #list of submarine lengths. I use indexing to loop through submarine lengths
        if name2 == "C":
            computerSubs(thisGame.get("Player 2 Board")) #places submarines using hardcoded function
        if name1 == "C":
            computerSubs(thisGame.get("Player 1 Board"))
        for j in range(1,3): #placeSubs logic for real player
            player = thisGame.get("Player 1") if j == 1 else thisGame.get("Player 2")
            if player == "C": #skips placing submarines if player is computer
                continue
            board = "Player 1 Board" if j == 1 else "Player 2 Board"
            print(f"for {player}")
            for i in range(1,6): #loop to place submarines
                print(f"For Submarine {i}")
                name = "S" + str(i)
                pos = askForPos(length[i-1]) #function call for inputs on submarine positions
                while True: #checks all errors and breaks when the function executes. If there is an error, the code asks for user input again at the end of the loop. 
                    try:
                        placeSubs(thisGame.get(board), name, pos)
                        break
                    except OutOfBoundsError:
                        print("You have tried to place the submarine outside the board. Try again ")
                    except InvalidInputFormat:
                        print("You have entered an incorrect anchor format. Try again ")
                    except SubmarineOverlapError:
                        print("This submarine overlaps with another. Try again ")
                    except:
                        print("There was an unknown error. Try again ")
                    pos = askForPos(length[i-1]) 

    flag1 = 1 if thisGame.get("Player 1")=="C" else 0
    flag2 = 1 if thisGame.get("Player 2")=="C" else 0
    flag = [flag1, flag2] #flag list for computer players. I use loop index to call the correct flag
    boards = ["Player 1 Board", "Player 2 Board"]
    while isWinner(thisGame) == 0: #playing the game
        who = thisGame.get("Who") #player who plays the move in this step
        player = thisGame.get("Player 1") if who == 1 else thisGame.get("Player 2") #name of the player
        otherPlayer = 2 if who == 1 else 1 
        if flag[who-1] == 0: #if the player is not a computer, take an input for the move
            print(f"make your move {player}")
            while True: #loop to check errors
                try:
                    thisGame = makeMove(thisGame, input())
                    break
                except MoveNotMade:
                    print("You have entered an illegal move. Try again: ")
                except:
                    print("There was an unknown error. Try again: ")
        else:
            #case if the player is a computer. suggestMove always suggests a valid move, so error cases are not needed here. 
            #The list returned by validMoves cannot be empty since isWinner would have triggered by then
            thisGame = makeMove(thisGame, suggestMove(thisGame.get(boards[otherPlayer - 1])))
        print(printBoard(thisGame.get(boards[otherPlayer-1]), showSubs = False, showSubNum = False)) #prints other players board after making the move
    winner = thisGame.get("Player 1") if isWinner(thisGame) == 1 else thisGame.get("Player 2") #Since this is outside the loop, there is a winner
    print(f"The game has ended. The winner is {winner}")


def testFunctionCalls():
    '''
    Input:  [none]
    
    Output: [none]
    
    You can use this function to test if your function names are correct.
    To call the function: "testFunctionCalls()"
    '''
    c = input('The following function will test whether your code can be \
successfully called, i.e. you have used the correct name. \
This function does not test whether the outputs of the functions \
are of the correct type, so passing this function does not \
guarentee that your code will successfully run and you should \
still perform your own checks. \n\nIf you accept these limitations \
type "y" to proceed: ')
    if c == 'y':
        print('You have chosen to proceed.\n\n')
        try:
            newEmptyGame.__doc__
            print('Task 1: Call to "newEmptyGame" successful.\n')
        except:
            print('Task 1: Call to "newEmptyGame" UNSUCCESSFUL.\n')
        
        try:
            posToIndex.__doc__
            print('Task 2: Call to "posToIndex" successful.\n')
        except:
            print('Task 2: Call to "posToIndex" UNSUCCESSFUL.\n')
            
        try:
             OutOfBoundsError()
             print('Task 2: "OutOfBoundsError" found.\n')
        except:
             print('Task 2: "OutOfBoundsError" NOT FOUND.\n')  
            
        try:
             InvalidInputFormat()
             print('Task 2: "InvalidInputFormat" found.\n')
        except:
             print('Task 2: "InvalidInputFormat" NOT FOUND.\n')
            
        try:
            placeSubs.__doc__
            print('Task 3: Call to "placeSubs" successful.')
        except:
            print('Task 3: Call to "placeSubs" UNSUCCESSFUL.')
         
        try:
            SubmarineOverlapError()
            print('Task 3: "SubmarineOverlapError" found.\n')
        except:
            print('Task 3: "SubmarineOverlapError" NOT FOUND.\n')
         
        try:
            printBoard.__doc__
            print('Task 4: Call to "printBoard" successful.')
        except:
            print('Task 4: Call to "printBoard" UNSUCCESSFUL.')
        
        try:
            IndexOutOfRange()
            print('Task 5: "IndexOutOfRange" found.\n')
        except:
            print('Task 5: "IndexOutOfRange" NOT FOUND.\n')
        
        try:
            indexToPos.__doc__
            print('Task 5: Call to "indexToPos" successful.\n')
        except:
            print('Task 5: Call to "indexToPos" UNSUCCESSFUL.\n')
            
        try:
            saveGame.__doc__
            print('Task 6: Call to "saveGame" successful.\n')
        except:
            print('Task 6: Call to "saveGame" UNSUCCESSFUL.\n')
            
        try:
            loadGame.__doc__
            print('Task 7: Call to "loadGame" successful.\n')
        except:
            print('Task 7: Call to "loadGame" UNSUCCESSFUL.\n')
            
        try:
            findValidMoves.__doc__
            print('Task 8: Call to "findValidMoves" successful.')
        except:
            print('Task 8: Call to "findValidMoves" UNSUCCESSFUL.')
        
        try:
            MoveNotMade()
            print('Task 9: "MoveNotMade" found.\n')
        except:
            print('Task 9: "MoveNotMade" NOT FOUND.\n')
        
        try:
            makeMove.__doc__
            print('Task 9: Call to "makeMove" successful.\n')
        except:
            print('Task 9: Call to "makeMove" UNSUCCESSFUL.\n')
            
        try:
            isWinner.__doc__
            print('Task 10: Call to "isWinner" successful.')
        except:
            print('Task 10: Call to "isWinner" UNSUCCESSFUL.')
            
        try:
            suggestMove.__doc__
            print('Task 11: "suggestMove" found.\n')
        except:
            print('Task 11: "suggestMove" NOT FOUND.\n')
            
        try:
            playGame.__doc__
            print('Task 12: Call to "playGame" successful.\n')
        except:
            print('Task 12: Call to "playGame" UNSUCCESSFUL.\n')
    else:
         print('You have chosen not to proceed.')



print(testFunctionCalls())