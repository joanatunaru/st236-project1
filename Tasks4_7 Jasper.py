# Task 4
import csv
#Return text for a valid board row using the two display options.Leaves the row unchanged; no custom errors.
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


#Return a string for a valid 5x5x5 board without changing it.showSubs shows ships; showSubNum shows ship and hit numbers.Both default to False. No custom errors.
def printBoard(board, showSubs=False, showSubNum=False):
    result = ''
    for k in range(5):
        result = result + 'Layer ' + str(k + 1) + '             '
    result = result + '\n'
    result = result + ' |A |B |C |D |E |   ' * 5 + '\n'

    rows = 'abcde'
    for j in range(5):
        for k in range(5):
            result = result + rows[j] + '|'
            result = result + boardRowText(board[k][j], showSubs, showSubNum)
            result = result + '   '
        result = result + '\n'
    return result

# Task 5
class IndexOutOfRange(Exception):
    pass

#Convert [column, row, level] to a string such as 'Aa1'.Input must be a list of three integers from 0 to 4; it is unchanged.Raise IndexOutOfRange for invalid input.
def indexToPos(ind):
    if type(ind) != list or len(ind) != 3:
        raise IndexOutOfRange
    for number in ind:
        if type(number) != int or number < 0 or number > 4:
            raise IndexOutOfRange

    columns = 'ABCDE'
    rows = 'abcde'
    levels = '12345'
    return columns[ind[0]] + rows[ind[1]] + levels[ind[2]]

# Task 6
#Write a valid board with a CSV writer; return None.Leaves the board unchanged. File errors pass to the caller.
def writeBoard(writer, board):
    for layer in board:
        for row in layer:
            writer.writerow(row)


#Save a valid game to fname, overwriting it; return None.Leaves game unchanged. File errors pass to the caller.
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
#Return a new board from 25 CSV rows starting at start.Converts '0' to 0 without changing data. Assumes valid CSV data;missing rows may raise IndexError.
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

#Return a new game from a valid coursework CSV file, fname.Who, ShowSubs entries and empty cells become integers.File errors pass to the caller; bad data may raise IndexError or ValueError.
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
