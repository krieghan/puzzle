import threading

from game_common import (
    graph,
    interfaces,
    statemachine)
from game_common.twodee.geometry import intersect
from OpenGL import GL, GLUT
from zope.interface import (
    implementer,
    verify)

from bishops import (
    board,
    world_states)

@implementer(interfaces.IWorld, interfaces.Observable)
class BishopsWorld(object):
    animation_transition_time = 1000

    def __init__(self):
        self.tile_height = 100
        self.tile_width = 100
        self.width_tiles = 5
        self.height_tiles = 4
        self.border = 0
        self.width = (self.width_tiles * self.tile_width) + (self.border * 2)
        self.height = (self.height_tiles * self.tile_height) + (self.border * 2)
        self.max_left = 0
        self.max_right = self.width
        self.max_bottom = 0
        self.max_top = self.height
        self.interactive = True

        self.traversal = board.Traversal()
        self.canvasElements = set()

        self.current_time = 0
        self.state_machine = statemachine.StateMachine(
            owner=self,
            current_state=world_states.WaitForPieceSelection,
            name='world'
        )

    def getObservers(self):
        return []

    def set_canvas(self, canvas):
        self.canvas = canvas

    def getHeightWidth(self):
        return (self.height, self.width)

    def getMaxLeftRightBottomTop(self):
        return (
            self.max_left,
            self.max_right,
            self.max_bottom,
            self.max_top
        )

    def add_canvas_element(self, element):
        verify.verifyObject(
            interfaces.Renderable,
            element
        )
        self.canvasElements.add(element)

    def remove_canvas_element(self, element):
        self.canvasElements.remove(element)

    def start(self):
        GLUT.glutMouseFunc(self.handle_mouse_click)
        GLUT.glutKeyboardFunc(self.handle_keyboard)
        GLUT.glutSpecialUpFunc(self.handle_keyboard)
        self.board = board.Board.from_initial_state()
        for piece in self.board.pieces:
            piece.init_renderable()
            self.add_canvas_element(piece)

        self.canvas.render()
        self.state_machine.start()
        self.compute_thread = threading.Thread(
            target=self.traversal.build_map)
        self.compute_thread.start()
        # self.traversal.discover_all_winning_states()
        # self.paths = self.traversal.get_all_winning_paths()
        # self.current_path = self.paths[0]
        # self.current_step = -1
        # self.ready_for_next = True
        
    def start_animation(self, move):
        piece_to_move = None
        if self.selected_piece is None:
            for piece in self.board.pieces_by_type[move.piece_type]:
                if move.piece_from == (piece.row, piece.column):
                    piece_to_move = piece
                    break
        else:
            piece_to_move = self.selected_piece

        assert piece_to_move is not None

        self.piece_to_move = piece_to_move

        board_offset = (
            (move.piece_to[0] - move.piece_from[0]),
            (move.piece_to[1] - move.piece_from[1])
        )
        move_distance = abs(board_offset[0])
        print(move)
        print(move_distance)
        self.animate_start = self.current_time
        transition_time = self.animation_transition_time * move_distance
        self.animate_end = (
            self.current_time + transition_time 
        )
        visual_move = (
            board_offset[1] * self.tile_width,
            -board_offset[0] * self.tile_height)
        piece_to_move.start_animation(
            board_offset=board_offset,
            visual_move=visual_move,
            animate_start=self.animate_start,
            animate_end=self.animate_end,
            transition_time=transition_time,
            move=move
        )

    def handle_mouse_click(self, button, state, x, y):
        if button == 0 and state == 1:
            transformed_x, transformed_y = self.canvas.transform_click(x, y)
            self.state_machine.current_state.handle_click(
                owner=self,
                x=transformed_x,
                y=transformed_y)

    def handle_keyboard(self, key, *args, **kwargs):
        if key == b' ':
            self.interactive = not self.interactive

        if key in (GLUT.GLUT_KEY_UP,
                   GLUT.GLUT_KEY_DOWN,
                   GLUT.GLUT_KEY_LEFT,
                   GLUT.GLUT_KEY_RIGHT):
            self.state_machine.current_state.handle_keyboard_direction(
                owner=self,
                key=key)

    def initiate_auto_move(self):
        current_state_string = board.BoardState(self.board).get_state_string()
        current_state = self.traversal.discovered_states.get(
            current_state_string)
        self.path = self.traversal.get_shortest_winning_path(
            current_state)
        self.selected_piece = None
        self.selected_move = None
        self.piece_to_move = None
        self.state_machine.change_state(world_states.AutoAnimate)
        

    def update(self,
               current_time):
        self.current_time = current_time
        self.state_machine.update()
        return

        if self.current_step == len(self.current_path) - 1:
            return
        self.current_step += 1
        (self.current_state,
         current_move) = self.current_path[self.current_step]
        if current_move is None:
            return
        self.ready_for_next = False
        (piece_type,
         piece_from,
         piece_to,
         direction) = current_move
        piece_to_move = None
        for piece in self.board.pieces_by_type[piece_type]:
            if piece_from == (piece.row, piece.column):
                piece_to_move = piece
                break
        if piece_to_move is None:
            raise Exception()
        self.piece_to_move = piece_to_move

        transition_time = 1000
        animate_start = currentTime
        self.animate_end = currentTime + transition_time
        
        move = board.Direction.get_offset(direction)

        visual_move = (
            move[1] * self.tile_width,
            -move[0] * self.tile_height)

        self.piece_to_move.start_animation(
            move,
            visual_move,
            animate_start,
            self.animate_end,
            transition_time)
                
        self.piece_to_move.update_animation(currentTime)
        if currentTime > self.animate_end:
            self.ready_for_next = True
            self.piece_to_move.end_animation()


    def render(self):
        for element in self.getAllCanvasElements():
            element.draw()

        # Draw tile grid
        GL.glColor3f(.5, .5, .5)
        GL.glBegin(GL.GL_LINES)
        for i in range(self.width_tiles + 1):
            x = i * self.tile_width + self.border
            GL.glVertex2f(x, self.border)
            GL.glVertex2f(x, self.height - self.border)

        for i in range(self.height_tiles + 1):
            y = i * self.tile_height + self.border
            GL.glVertex2f(self.border, y)
            GL.glVertex2f(self.width - self.border, y)

        GL.glEnd()

    
    def getAllCanvasElements(self):
        return self.canvasElements

verify.verifyClass(interfaces.IWorld, BishopsWorld)
