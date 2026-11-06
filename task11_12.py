
###############################################################################
# Task 11

def suggestMove(board):
    validMoves = findValidMoves(board)
    return validMoves[0]

###############################################################################
# Task 12

def askForPos(length):
    '''
    asks for the position of the submarine
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
    if name1 == "load":
        while True: #load existing game
            try:
                print("Enter file name: ") 
                thisGame = loadGame(input())
                break
            except:
                print("There is no file with this name. Try again")
    else:
        print("Enter Player 2 Name: ")
        name2 = input()
        thisGame = newEmptyGame(name1, name2, ShowSubs = [])
        length = [5,4,3,3,2]
        if name2 == "C":
            computerSubs(thisGame.get("Player 2 Board"))
        if name1 == "C":
            computerSubs(thisGame.get("Player 1 Board"))
        for j in range(1,3): #placeSubs logic for real player
            player = thisGame.get("Player 1") if j == 1 else thisGame.get("Player 2")
            if player == "C":
                continue
            board = "Player 1 Board" if j == 1 else "Player 2 Board"
            print(f"for {player}")
            for i in range(1,6):
                print(f"For Submarine {i}")
                name = "S" + str(i)
                pos = askForPos(length[i-1])
                while True:
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
    flag = [flag1, flag2]
    boards = ["Player 1 Board", "Player 2 Board"]
    while isWinner(thisGame) == 0: #playing the  game
        who = thisGame.get("Who")
        player = thisGame.get("Player 1") if who == 1 else thisGame.get("Player 2")
        otherPlayer = 2 if who == 1 else 1 
        if flag[who-1] == 0:
            print(f"make your move {player}")
            while True:
                try:
                    thisGame = makeMove(thisGame, input())
                    break
                except MoveNotMade:
                    print("You have entered an illegal move. Try again: ")
                except:
                    print("There was an unknown error. Try again: ")
        else:
            thisGame = makeMove(thisGame, suggestMove(thisGame.get(boards[otherPlayer - 1])))
        print(printBoard(thisGame.get(boards[otherPlayer-1]), showSubs = False, showSubNum = False))
    winner = thisGame.get("Player 1") if isWinner(thisGame) == 1 else thisGame.get("Player 2")
    print(f"The game has ended. The winner is {winner}")