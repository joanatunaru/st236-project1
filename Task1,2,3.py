class OutOfBoundsError(Exception):
    """
    Raised when a correctly formatted position refers to a cube that is not on the 5x5x5 board.

    The board's valid co-ordinates are columns 'A'-'E', rows 'a'-'e' and levels '1'-'5'.
    This error means the input was well-formed but at least one co-ordinate lies outside
    these ranges (e.g. 'E0a', '3Gb'), or that an object would extend beyond the board's edge.
    """
    pass

class InvalidInputFormat(Exception):
    """
    Raised when an input is not in the expected format, regardless of the values it contains.

    For a position, this means it isn't a string, it is not exactly 3 characters long, or does not consist
    of exactly one uppercase letter, exactly one lowercase letter and exactly one digit (in any order).
    e.g. 123, 'Ab', 'BdA2', 'AB1'

    Also used within placeSubs(board, name, pos) when pos is given in an invalid format.
    """
    pass

class SubmarineOverlapError(Exception):
    """
    Raised within placeSubs(board, name, pos) when a cell we attempt to place a new sub within already contains
    another placed sub.
    """
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
            in any order, so e.g. 'Aa1', '1aA' and 'a1A' all refer to the same cube within the board
            Any other input raises an exception

    Output:
        (list of int) [i, j, k], each integer from 0 to 4, where
            i is the column index (A-E -> 0-4),
            j is the row index (a-e -> 0-4),
            k is the level index (1-5 -> 0-4),
            so the cube at place is board[k][j][i]
            e.g. 'Aa1' -> [0, 0, 0], 'cE3' -> [4, 2, 2]

    Exceptions:
        InvalidInputFormat is raised in any of these cases.
            place is not a string
            place is not 3 characters long
            place doesn't contain exactly one uppercase letter, exactly one lowercase letter and exactly one digit, in any order

        OutOfBoundsError is raised when:
            place is a valid input format (all 3 rules above are met), but refers to a cube not in the board,
            i.e. the uppercase letter is not in A-E, the lowercase letter is not in a-e, or the digit is not
            in 1-5. e.g. 'D0a', '2Fa'

        Format gets checked before bounds, so an input that is both malformed and out of range (e.g. 'FG9') raises InvalidInputFormat
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
            e.g. pos = {'anchor': 'aE1', 'direction': 'up', 'length': 5}

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

        All checks get completed before the board is modified, so if any exception is raised the board will be left unchanged.
    """
    if not isinstance(pos, dict) or not {'anchor', 'direction', 'length'} <= pos.keys():
        raise InvalidInputFormat("pos must be a dict with keys 'anchor', 'direction', 'length'.")
    if not isinstance(pos['direction'], str) or pos['direction'] not in STEPS:
        raise InvalidInputFormat("Direction must be one of " + ', '.join(STEPS.keys()) + ".")

    anchor_i, anchor_j, anchor_k = posToIndex(pos['anchor'])  # note the anchor must be a valid on-board cube, otherwise posToIndex has already raised an exception
    length = pos['length']

    if not isinstance(length, int) or length <= 0:
        raise InvalidInputFormat("Length must be a positive integer, instead got " + str(length) + ".")

    di, dj, dk = STEPS[pos['direction']]
    cells = [[anchor_i + n * di, anchor_j + n * dj, anchor_k + n * dk] for n in range(length)]

    # Now we have our cells and a valid anchor point, we validate that our sub is on the board and that we have no overlap between subs.

    if not all(0 <= v <= 4 for v in cells[-1]):
        raise OutOfBoundsError("Attempt to place sub " + name + " in an out of bounds cube rejected.")
    if any(board[k][j][i] != 0 for i, j, k in cells):
        raise SubmarineOverlapError(
            "Attempt to place sub " + name + ", rejected due to overlap with another submarine.")
    for i, j, k in cells:
        board[k][j][i] = name
