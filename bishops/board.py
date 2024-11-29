import collections
import copy
import math
import time

from game_common import (
    interfaces)
from game_common.twodee.geometry import (
    calculate,
    intersect)
from OpenGL import (GL, GLUT)
import zope.interface

Move = collections.namedtuple(
    'Move',
    ['piece_type',
     'piece_from',
     'piece_to',
     'direction'])

class Board:
    def __init__(self, pieces_by_type, world):
        self.pieces_by_type = pieces_by_type
        self.pieces = []
        self.moves_by_piece = None
        self.world = world
        for piece_type, pieces_for_type in pieces_by_type.items():
            for piece in pieces_for_type:
                piece.set_board(self)
            self.pieces.extend(pieces_for_type)

    def copy(self):
        pieces_by_type = {
            key: [x.copy() for x in value] 
            for (key, value) in self.pieces_by_type.items()}
        return Board(pieces_by_type, world=self.world)

    def finish_move(self):
        self.moves_by_piece = None

    def get_piece(self, piece_type, piece_base):
        for piece in self.pieces_by_type[piece_type]:
            if (piece.row, piece.column) == piece_base:
                return piece

        return None
        
    @classmethod
    def from_initial_state(cls, world):
        white_bishops = [
            create_white_bishop(0, 4),
            create_white_bishop(1, 4),
            create_white_bishop(2, 4),
            create_white_bishop(3, 4)
        ]

        red_bishops = [
            create_red_bishop(0, 0),
            create_red_bishop(1, 0),
            create_red_bishop(2, 0),
            create_red_bishop(3, 0)
        ]

        pieces_by_type = {
            'white': white_bishops,
            'red': red_bishops
        }
        return Board(pieces_by_type, world=world)

    def get_cell_by_position(self, x, y):
        column_number = int(x / self.world.tile_width)
        row_number = int((self.world.height - y) / self.world.tile_height)
        return row_number, column_number

    def get_piece_by_indices(self, row_number, column_number):
        current_state = BoardState(self)
        for piece in self.pieces:
            if piece.row == row_number and piece.column == column_number:
                return piece

    def select_game_piece(self, x, y):
        row_number, column_number = self.get_cell_by_position(x, y)
        return self.get_piece_by_indices(row_number, column_number)

    def find_moves(self, current_state=None):
        if current_state is None:
            current_state = BoardState(self)
        if self.moves_by_piece is None:
            moves_by_piece = self.moves_by_piece = {}
            for piece in self.pieces:
                moves_for_piece = piece.find_moves(current_state)
                if moves_for_piece:
                    moves_by_piece[piece] = moves_for_piece
        return self.moves_by_piece

    def update_pieces_from_board(self, board):
        self.moves_by_piece = None
        for piece_type, pieces in self.pieces_by_type.items():
            for piece_index in range(len(pieces)):
                pieces[piece_index].update_from_piece(
                    board.pieces_by_type[piece_type][piece_index])

    def update_pieces_from_state(self, state):
        self.moves_by_piece = None
        for piece_type, pieces in self.pieces_by_type.items():
            state_pieces_for_type = state.pieces_by_type[piece_type]
            for piece_index in range(len(pieces)):
                piece = pieces[piece_index]
                piece.row, piece.column = state_pieces_for_type[piece_index]


@zope.interface.implementer(interfaces.Renderable)
class BoardPiece:
    cell_height = 100
    cell_width = 100
    board_height = 400
    border = 5

    def __init__(self, row, column, height, width, piece_type):
        self.column = column
        self.row = row
        self.height = height
        self.width = width
        self.piece_type = piece_type
        self.board = None
        if piece_type == 'white':
            self.symbol = 'W'
        elif piece_type == 'red':
            self.symbol = 'R'

    def copy(self):
        return BoardPiece(
            row=self.row,
            column=self.column,
            height=self.height,
            width=self.width,
            piece_type=self.piece_type)

    def set_board(self, board):
        self.board = board

    def update_from_piece(self, piece):
        self.column = piece.column
        self.row = piece.row
        self.board.finish_move()

    def find_moves(self, current_state):
        if self.piece_type == 'white':
            checks = current_state.white_checks
        elif self.piece_type == 'red':
            checks = current_state.red_checks
        else:
            raise NotImplementedError()

        moves = []
        for row_offset in (-1, 1):
            for column_offset in (-1, 1):
                current_row = self.row + row_offset
                current_column = self.column + column_offset
                while (current_row >= 0 and 
                       current_row < self.board.world.height_tiles and
                       current_column >= 0 and 
                       current_column < self.board.world.width_tiles):
                    space = checks[current_row][current_column]
                    if space == ' ':
                        moves.append(
                            Move(
                                piece_type=self.piece_type,
                                piece_from=(self.row, self.column),
                                piece_to=(current_row, current_column),
                                direction=Direction.get_by_offsets(
                                    row_offset,
                                    column_offset
                                )
                            )
                        )
                    elif space != 'C':
                        # If another piece is in this space, the rest
                        # of the diagonal is blocked for this piece.
                        break

                    current_row += row_offset
                    current_column += column_offset

        return moves

    # Renderable

    def init_renderable(self):
        self.renderable_height = self.height * self.cell_height
        self.renderable_width = self.width * self.cell_width
        self.update_position_from_grid()
        if self.piece_type == 'white':
            self.color = (1, 1, 1)
        elif self.piece_type == 'red':
            self.color = (1, 0, 0)
        else:
            raise NotImplementedError()

    def getActive(self):
        return True

    def getPosition(self):
        return self.position

    def getLength(self):
        return self.height * self.cell_height

    def getWidth(self):
        return self.width * self.cell_width

    def update(self, timeElapsed):
        pass

    def update_position_from_grid(self):
        x = self.column * self.cell_width + (self.renderable_width / 2)
        y = self.board_height - (
            self.row * self.cell_height + (self.renderable_height / 2)
        )
        self.position = (x, y)

    def start_animation(
            self,
            board_offset,
            visual_move,
            animate_start,
            animate_end,
            transition_time,
            move):
        self.board_offset = board_offset
        self.visual_move = visual_move
        self.animation_start_position = self.position
        self.animate_start = animate_start
        self.animate_end = animate_end
        self.transition_time = transition_time
        self.move = move

    def end_animation(self):
        self.row += self.board_offset[0]
        self.column += self.board_offset[1]
        self.board.finish_move()
        self.animation_start_position = None
        self.board_offset = None
        self.move = None
        self.visual_move = None
        self.animate_start = None
        self.animate_end = None
        self.transition_time = None

    def update_animation(self, currentTime):
        progress = (
            (min(currentTime, self.animate_end) - self.animate_start) / 
            self.transition_time)
        offset = calculate.multiplyVectorAndScalar(
            self.visual_move,
            progress)
        new_position = calculate.addPointAndVector(
            self.animation_start_position,
            offset)
        self.position = new_position

    def get_display_dimensions(self):
        half_width = .5 * (self.getWidth() - (self.border * 2))
        half_height = .5 * (self.getLength() - (self.border * 2))
        return (half_width, half_height)

    def get_display_vertices(self, x=None, y=None):
        pos_x, pos_y = self.getPosition()
        if x is None:
            x = pos_x
        if y is None:
            y = pos_y
        
        half_width, half_height = self.get_display_dimensions()
        return (
            (x - half_width, y + half_height),
            (x + half_width, y + half_height),
            (x + half_width, y - half_height),
            (x - half_width, y - half_height))

    def draw(self):
        x, y = self.getPosition()
        # get vertices in local coordinates system
        display_vertices = self.get_display_vertices(x=0, y=0)
        
        color = self.color
        GL.glPushMatrix()
        GL.glTranslate(x, y, 0)
        GL.glColor3f(*color)
        half_width, half_height = self.get_display_dimensions()
        draw_circle(radius=half_width, number_of_triangles=20)
        GL.glPopMatrix()


def draw_circle(radius, number_of_triangles):
    GL.glBegin(GL.GL_TRIANGLE_FAN)
    twice_pi = 2.0 * math.pi
    GL.glVertex2f(0, 0)

    for i in range(number_of_triangles + 1):
        GL.glVertex2f(
            radius * math.cos(i * twice_pi / number_of_triangles),
            radius * math.sin(i * twice_pi / number_of_triangles))
    GL.glEnd()





def create_white_bishop(row, column):
    return BoardPiece(row, column, height=1, width=1, piece_type='white')


def create_red_bishop(row, column):
    return BoardPiece(row, column, height=1, width=1, piece_type='red')


class BoardState:
    def __init__(self, board, move=0):
        self.initialize_rows()
        self.pieces_by_type = {
            'white': [],
            'red': []
        }
        self.board = board
        self.plot_pieces(board)
        self.white_checks = self.fill_checks('red')
        self.red_checks = self.fill_checks('white')
        self.state_string = self.get_state_string()
        self.adjacent_states = {}
        self.move = move
        self.moves_from_winning_states = []

    def fill_checks(self, piece_type):
        if piece_type == 'red':
            symbol = 'R'
        elif piece_type == 'white':
            symbol = 'W'
        else:
            raise NotImplementedError()
        checks = copy.deepcopy(self.rows)
        board_height = len(self.rows)
        board_width = len(self.rows[0])
        for (piece_row, piece_column) in self.pieces_by_type[piece_type]:
            for row_offset in (-1, 1):
                for column_offset in (-1, 1):
                    scan_row = piece_row
                    scan_column = piece_column
                    while (scan_row >= 0 and scan_row < board_height and
                           scan_column >= 0 and scan_column < board_width):
                        if self.rows[scan_row][scan_column] == ' ':
                            checks[scan_row][scan_column] = 'C'
                        scan_row += row_offset
                        scan_column += column_offset

        return checks

    def get_checks_for_piece(self, piece):
        if piece.piece_type == 'red':
            return self.red_checks
        elif piece.piece_type == 'white':
            return self.white_checks
        else:
            raise NotImplementedError()

    def is_winning(self):
        return self.rows == [
            ['W', ' ', ' ', ' ', 'R'],
            ['W', ' ', ' ', ' ', 'R'],
            ['W', ' ', ' ', ' ', 'R'],
            ['W', ' ', ' ', ' ', 'R'],
        ]

    def initialize_rows(self):
        self.rows = [
            self._create_row(),
            self._create_row(),
            self._create_row(),
            self._create_row()
        ]
        
    def _create_row(self):
        return [' ', ' ', ' ', ' ', ' ']

    def plot_pieces(self, board):
        for piece_type, pieces in board.pieces_by_type.items():
            for piece in pieces:
                self.pieces_by_type[piece_type].append(
                    (piece.row, piece.column)
                )
                for column_offset in range(piece.width):
                    for row_offset in range(piece.height):
                        new_row = piece.row + row_offset
                        new_column = piece.column + column_offset
                        self.rows[new_row][new_column] = piece.symbol

    def print_self(self):
        for row in self.rows:
            print(''.join(row))

    def get_state_string(self):
        return ''.join([''.join(x) for x in self.rows])

    def connect(self, other_state, move_info):
        forward = move_info
        backward = reverse_move_info(forward)
        self.adjacent_states[other_state.state_string] = (other_state, forward)
        other_state.adjacent_states[self.state_string] = (self, backward)


def reverse_move_info(move):
    backward = Move(
        piece_type=move.piece_type,
        piece_from=move.piece_to,
        piece_to=move.piece_from,
        direction=Direction.opposite(move.direction))
    return backward

        
class Traversal:
    def __init__(self, world):
        board = Board.from_initial_state(world=world)
        self.board = board
        self.next_board = board.copy()
        self.starting_state = BoardState(board=board)
        self.discovered_states = {
            self.starting_state.state_string: self.starting_state
        }
        self.current_state = None


    def get_shortest_winning_path(self, current_state):
        path_index = 0
        current_min = current_state.moves_from_winning_states[0]
        for i in range(len(current_state.moves_from_winning_states[1:])):
            moves = current_state.moves_from_winning_states[i]
            if moves < current_min:
                path_index = i
                current_min = moves

        moves = current_min

        while moves > 0:
            adjacent_states = current_state.adjacent_states
            for (adjacent_state, move) in adjacent_states.values():
                if adjacent_state.moves_from_winning_states[path_index] < moves:
                    current_state = adjacent_state
                    yield (current_state, move)
                    moves = current_state.moves_from_winning_states[path_index]
                    break


    def get_all_winning_paths(self, starting_state=None):
        if starting_state is None:
            starting_state = self.starting_state
        paths = []
        for winning_state in self.winning_states:
            current_state = winning_state
            path = [(current_state, None)]
            while current_state != starting_state:
                next_state = None
                backward_move = None
                adjacent_states = current_state.adjacent_states
                for (adjacent_state, backward) in adjacent_states.values():
                    if adjacent_state.move == current_state.move - 1:
                        next_state = adjacent_state
                        backward_move = backward
                        break
                if next_state is None:
                    raise Exception('Cannot build path back from {}'.format(
                        current_state))
                else:
                    current_state = next_state
                    path.insert(
                        0,
                        (current_state,
                         reverse_move_info(backward_move)))
            paths.append(path)
        return paths

    def build_map(self):
        print('Discovering winning states')
        winning_states = self.discover_all_winning_states()
        print('Winning states disccovered')
        path_index = 0
        for winning_state in winning_states:
            print('Mapping path {}'.format(path_index))
            moves = 0
            state_queue = [winning_state]
            mapped_states = {winning_state}
            winning_state.moves_from_winning_states.append(0)
            while state_queue:
                current_state = state_queue.pop(0)
                move_number =\
                    current_state.moves_from_winning_states[path_index] + 1
                adjacent_states = current_state.adjacent_states
                for (adjacent_state, _) in adjacent_states.values():
                    if adjacent_state in mapped_states:
                        continue
                    mapped_states.add(adjacent_state)
                    adjacent_state.moves_from_winning_states.append(move_number)
                    state_queue.append(adjacent_state)
            print('Finished map for path {}'.format(path_index))
            path_index += 1

    def discover_all_winning_states(self):
        count = 0
        winning_states = []
        state_queue = [self.starting_state]
        while state_queue:
            count += 1
            self.current_state = state_queue.pop(0)
            self.board.update_pieces_from_state(self.current_state)
            self.next_board.update_pieces_from_board(self.board)
            if self.current_state.is_winning():
                winning_states.append(self.current_state)
                # Only need 1, not all
                return winning_states
                #continue

            moves_by_piece = self.next_board.find_moves(self.current_state)
            for (piece, moves_for_piece) in moves_by_piece.items():
                for move in moves_for_piece:
                    piece.row, piece.column = move.piece_to
                    board_state_candidate =\
                        BoardState(
                            board=self.next_board,
                            move=self.current_state.move + 1
                        )
                    existing_board_state =\
                        self.discovered_states.get(
                            board_state_candidate.state_string
                        )
                    if existing_board_state:
                        board_state = existing_board_state
                    else:
                        board_state = board_state_candidate
                        self.discovered_states[board_state.state_string] =\
                            board_state
                        state_queue.append(board_state)

                    self.current_state.connect(
                        board_state,
                        move
                    )
                    self.next_board.update_pieces_from_board(self.board)
            time.sleep(.00001)
        self.winning_states = winning_states
        return winning_states


    def print_board(self):
        self.current_state.print_self()

def get_direction(row_offset, column_offset):
    if row_offset == 0 and column_offset == 1:
        return Direction.UP
    elif row_offset == 1 and column_offset == 0:
        return Direction.RIGHT
    elif row_offset == 0 and column_offset == -1:
        return Direction.DOWN
    elif row_offset == -1 and column_offset == 0:
        return Direction.LEFT
    elif row_offset == 1 and column_offset == 1:
        return Direction.UP_RIGHT
    elif row_offset == -1 and column_offset == 1:
        return Direction.UP_LEFT
    elif row_offset == 1 and column_offset == -1:
        return Direction.DOWN_RIGHT
    elif row_offset == -1 and column_offset == -1:
        return Direction.DOWN_LEFT
    else:
        raise NotImplementedError()

class Direction:
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3
    UP_RIGHT = 4
    UP_LEFT = 5
    DOWN_RIGHT = 6
    DOWN_LEFT = 7

    direction_by_offsets = {
        (0, 1): UP,
        (1, 0): RIGHT,
        (0, -1): DOWN,
        (-1, 0): LEFT,
        (1, 1): UP_RIGHT,
        (-1, 1): UP_LEFT,
        (1, -1): DOWN_RIGHT,
        (-1, -1): DOWN_LEFT
    }

    offsets_by_direction = {}

    for (k, v) in direction_by_offsets.items():
        offsets_by_direction[v] = k

    reverse_moves = {
        UP: DOWN,
        RIGHT: LEFT,
        UP_RIGHT: DOWN_LEFT,
        UP_LEFT: DOWN_RIGHT
    }

    for (k, v) in reverse_moves.copy().items():
        reverse_moves[v] = k

    keys = (
        GLUT.GLUT_KEY_UP,
        GLUT.GLUT_KEY_RIGHT,
        GLUT.GLUT_KEY_DOWN,
        GLUT.GLUT_KEY_LEFT
    )

    direction_by_key = {}
    key_by_direction = {}

    for i in range(4):
        direction_by_key[keys[i]] = i
        key_by_direction[i] = keys[i]

    @classmethod
    def opposite(cls, direction):
        return cls.reverse_moves[direction]

    @classmethod
    def get_by_offsets(cls, row_offset, column_offset):
        return cls.direction_by_offsets[(row_offset, column_offset)]

    @classmethod
    def get_offsets(cls, direction):
        return cls.offsets_by_direction[direction]

