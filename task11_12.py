
###############################################################################
# Task 11

def suggestMove(board):
    '''
    suggests a move from the list of valid moves
    '''
    validMoves = findValidMoves(board) #Uses Task 8 find valid moves to suggest a move
    return validMoves[0]

###############################################################################
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
