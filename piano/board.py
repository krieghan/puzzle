from game_common import (
        interfaces)
from game_common.twodee.geometry import (
    calculate,
    intersect)
from OpenGL import (GL, GLUT)
import zope.interface


class Board:
    def __init__(self, pieces_by_type):
        self.pieces_by_type = pieces_by_type
        self.piano = pieces_by_type['piano'][0]
        self.blanks = pieces_by_type['blank']
        self.pieces = []
        self.moves_by_piece = None
        for piece_type, pieces_for_type in pieces_by_type.items():
            for piece in pieces_for_type:
                piece.set_board(self)
            if piece_type == 'blank':
                continue
            self.pieces.extend(pieces_for_type)

    def copy(self):
        pieces_by_type = {
            key: [x.copy() for x in value] 
            for (key, value) in self.pieces_by_type.items()}
        return Board(pieces_by_type)

    def finish_move(self):
        self.moves_by_piece = None

    def update_blanks_from_move(self, move):
        (_,
         _,
         displaced_blanks,
         new_blank_cells,
         _) = move
        for blank_index in range(len(displaced_blanks)):
            blank = displaced_blanks[blank_index]
            blank.row, blank.column = new_blank_cells[blank_index]
            blank.update_position_from_grid()

    @classmethod
    def from_initial_state(cls):
        piano = create_piano(0, 1)
        chairs = [create_chair(2, 0),
                  create_chair(2, 1),
                  create_chair(2, 2),
                  create_chair(2, 3)]
        sofas = [create_sofa(0, 0),
                 create_sofa(0, 3),
                 create_sofa(3, 0),
                 create_sofa(3, 3)]
        bench = create_bench(3, 1)
        blanks = [create_blank(4, 1),
                  create_blank(4, 2)]
        pieces_by_type = {
            'piano': [piano],
            'chair': chairs,
            'sofa': sofas,
            'bench': [bench],
            'blank': blanks}
        return Board(pieces_by_type)

    def select_game_piece(self, x, y, piece_type='pieces'):
        if piece_type == 'pieces':
            pieces = self.pieces
        elif piece_type == 'blanks':
            pieces = self.blanks
        for piece in pieces:
            if intersect.point_in_rectangle(
                    (x, y),
                    piece.get_display_vertices()):
                return piece

    def find_moves(self):
        if self.moves_by_piece is None:
            blank_cells = [
                (blank.row, blank.column) 
                for blank in self.blanks]
            moves_by_piece = self.moves_by_piece = {}
            for piece in self.pieces:
                moves_for_piece = piece.find_moves(self.blanks, blank_cells)
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
    board_height = 500
    border = 5

    def __init__(self, row, column, height, width, piece_type):
        self.column = column
        self.row = row
        self.height = height
        self.width = width
        self.piece_type = piece_type
        self.board = None
        if piece_type == 'piano':
            self.symbol = 'P'
        elif piece_type == 'bench':
            self.symbol = 'B'
        elif piece_type == 'sofa':
            self.symbol = 'S'
        elif piece_type == 'chair':
            self.symbol = 'C'
        elif piece_type == 'blank':
            self.symbol = ' '

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

    def check_up(self, blanks, blank_cells):
        if self.row - 1 < 0:
            return False
        up_row = [(self.row - 1, self.column + x) for x in range(self.width)]
        matched_blanks = []
        for cell in up_row:
            if cell in blank_cells:
                matched_blanks.append(self._get_blank_by_cell(cell, blanks))
            else:
                return False
        new_blanks = [(self.row + (self.height - 1), self.column + x) for x in range(self.width)]
        new_base = (self.row - 1, self.column)
        return (
            new_base,
            up_row,
            matched_blanks,
            new_blanks,
            Direction.UP)

    def check_down(self, blanks, blank_cells):
        if self.row + self.height > 4:
            return False
        down_row = [(self.row + self.height, self.column + x) for x in range(self.width)]
        matched_blanks = []
        for cell in down_row:
            if cell in blank_cells:
                matched_blanks.append(self._get_blank_by_cell(cell, blanks))
            else:
                return False
        new_blanks = [(self.row, self.column + x) for x in range(self.width)]
        new_base = (self.row + 1, self.column)
        return (
            new_base,
            down_row,
            matched_blanks,
            new_blanks,
            Direction.DOWN)

    def check_left(self, blanks, blank_cells):
        if self.column - 1 < 0:
            return False
        left_column = [(self.row + x, self.column - 1) for x in range(self.height)]
        matched_blanks = []
        for cell in left_column:
            if cell in blank_cells:
                matched_blanks.append(self._get_blank_by_cell(cell, blanks))
            else:
                return False
        new_blanks = [(self.row + x, self.column + (self.width - 1)) for x in range(self.height)]
        new_base = (self.row, self.column - 1)
        return (
            new_base,
            left_column,
            matched_blanks,
            new_blanks,
            Direction.LEFT)

    def check_right(self, blanks, blank_cells):
        if self.column + self.width > 3:
            return False
        right_column = [(self.row + x, self.column + self.width) for x in range(self.height)]
        matched_blanks = []
        for cell in right_column:
            if cell in blank_cells:
                matched_blanks.append(self._get_blank_by_cell(cell, blanks))
            else:
                return False

        new_blanks = [(self.row + x, self.column) for x in range(self.height)]
        new_base = (self.row, self.column + 1)

        return (
            new_base,
            right_column,
            matched_blanks,
            new_blanks,
            Direction.RIGHT)

    def _get_blank_by_cell(self, cell, blanks):
        for blank in blanks:
            if (blank.row, blank.column) == cell:
                return blank

    def find_moves(self, blanks, blank_cells):
        up = self.check_up(blanks, blank_cells)
        down = self.check_down(blanks, blank_cells)
        left = self.check_left(blanks, blank_cells)
        right = self.check_right(blanks, blank_cells)
        moves = []
        if up:
            moves.append(up)
        if down:
            moves.append(down)
        if left:
            moves.append(left)
        if right:
            moves.append(right)
        return moves

    # Renderable

    def init_renderable(self):
        self.renderable_height = self.height * self.cell_height
        self.renderable_width = self.width * self.cell_width
        self.update_position_from_grid()
        if self.piece_type == 'piano':
            self.color = (1, 0, 0)
        elif self.piece_type == 'bench':
            self.color = (0, 1, 0)
        elif self.piece_type == 'sofa':
            self.color = (0, 0, 1)
        elif self.piece_type == 'chair':
            self.color = (0, 1, 1)
        else:
            self.color = (0, 0, 0)

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
        y = self.board_height - (self.row * self.cell_height + (self.renderable_height / 2))
        self.position = (x, y)

    def start_animation(
            self,
            move,
            visual_move,
            animate_start,
            animate_end,
            transition_time,
            move_data):
        self.move = move
        self.visual_move = visual_move
        self.animation_start_position = self.position
        self.animate_start = animate_start
        self.animate_end = animate_end
        self.transition_time = transition_time
        self.move_data = move_data

    def end_animation(self):
        self.row += self.move[0]
        self.column += self.move[1]
        self.board.update_blanks_from_move(self.move_data)
        self.board.finish_move()
        self.animation_start_position = None
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
        GL.glBegin(GL.GL_POLYGON)

        for vertex in display_vertices:
            GL.glVertex2f(*vertex)

        GL.glEnd()
        GL.glPopMatrix()

def create_piano(row, column):
    return BoardPiece(row, column, height=2, width=2, piece_type='piano')

def create_chair(row, column):
    return BoardPiece(row, column, height=1, width=1, piece_type='chair')

def create_sofa(row, column):
    return BoardPiece(row, column, height=2, width=1, piece_type='sofa')

def create_bench(row, column):
    return BoardPiece(row, column, height=1, width=2, piece_type='bench')

def create_blank(row, column):
    return BoardPiece(row, column, height=1, width=1, piece_type='blank')

class BoardState:
    def __init__(self, board, move=0):
        self.initialize_rows()
        self.pieces_by_type = {
            'piano': [],
            'sofa': [],
            'chair': [],
            'bench': [],
            'blank': []}
        self.plot_pieces(board)
        self.state_string = self.get_state_string()
        self.adjacent_states = {}
        self.move = move

    def initialize_rows(self):
        self.rows = [
            self._create_row(),
            self._create_row(),
            self._create_row(),
            self._create_row(),
            self._create_row()]
        
    def _create_row(self):
        return [' ', ' ', ' ', ' ']

    def plot_pieces(self, board):
        for piece_type, pieces in board.pieces_by_type.items():
            for piece in pieces:
                self.pieces_by_type[piece_type].append((piece.row, piece.column))
                for column_offset in range(piece.width):
                    for row_offset in range(piece.height):
                        self.rows[piece.row + row_offset][piece.column + column_offset] = piece.symbol

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


def reverse_move_info(move_info):
    (piece_type,
     piece_from,
     piece_to,
     direction) = move_info
    backward = (
        piece_type,
        piece_to,
        piece_from,
        Direction.opposite(direction))
    return backward

        
class Traversal:
    def __init__(self):
        board = Board.from_initial_state()
        self.board = board
        self.next_board = board.copy()
        self.starting_state = BoardState(board=board)
        self.discovered_states = {
            self.starting_state.state_string: self.starting_state}
        self.state_queue = [self.starting_state]
        self.current_state = None

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

    def discover_all_winning_states(self):
        count = 0
        winning_states = []
        while self.state_queue:
            count += 1
            self.current_state = self.state_queue.pop(0)
            self.board.update_pieces_from_state(self.current_state)
            self.next_board.update_pieces_from_board(self.board)
            piano = self.board.piano
            if (piano.row, piano.column) == (3, 1):
                winning_states.append(self.current_state)
                self.current_state.print_self()
                continue

            moves_by_piece = self.next_board.find_moves()
            for (piece, moves_for_piece) in moves_by_piece.items():
                for move in moves_for_piece:
                    (new_base,
                     displaced_blank_cells,
                     displaced_blanks,
                     new_blank_cells,
                     direction) = move
                    piece_from = (piece.row, piece.column)
                    piece_to = new_base
                    piece.row, piece.column = new_base
                    for blank_index in range(len(displaced_blanks)):
                        blank = displaced_blanks[blank_index]
                        blank.row, blank.column = new_blank_cells[blank_index]
                    board_state_candidate =\
                        BoardState(
                            board=self.next_board,
                            move=self.current_state.move + 1)
                    existing_board_state =\
                        self.discovered_states.get(
                            board_state_candidate.state_string)
                    if existing_board_state:
                        board_state = existing_board_state
                    else:
                        board_state = board_state_candidate
                        self.discovered_states[board_state.state_string] =\
                            board_state
                        self.state_queue.append(board_state)

                    move_info = (
                        piece.piece_type,
                        piece_from,
                        piece_to,
                        direction)
                    self.current_state.connect(
                        board_state,
                        move_info)
                    self.next_board.update_pieces_from_board(self.board)
        self.winning_states = winning_states
        return winning_states


    def print_board(self):
        self.current_state.print_self()

class Direction:
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3

    keys = (
        GLUT.GLUT_KEY_UP,
        GLUT.GLUT_KEY_RIGHT,
        GLUT.GLUT_KEY_DOWN,
        GLUT.GLUT_KEY_LEFT)

    direction_by_key = {}
    key_by_direction = {}

    for i in range(4):
        direction_by_key[keys[i]] = i
        key_by_direction[i] = keys[i]

    @classmethod
    def opposite(cls, direction):
        return (direction + 2) % 4
