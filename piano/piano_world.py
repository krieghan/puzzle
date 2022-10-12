from game_common import (
        graph,
        interfaces,
        statemachine)
from game_common.twodee.geometry import intersect
from OpenGL import GLUT
from zope.interface import (
    implementer,
    verify)

from piano import (
    board,
    world_states)

@implementer(interfaces.IWorld, interfaces.Observable)
class PianoWorld(object):
    def __init__(self):
        self.tile_height = 100
        self.tile_width = 100
        self.width_tiles = 4
        self.height_tiles = 5
        self.width = self.width_tiles * self.tile_width
        self.height = self.height_tiles * self.tile_height
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
            name='world')

    def getObservers(self):
        return []

    def set_canvas(self, canvas):
        self.canvas = canvas

    def getHeightWidth(self):
        return (self.height, self.width)

    def getMaxLeftRightBottomTop(self):
        return (self.max_left,
                self.max_right,
                self.max_bottom,
                self.max_top)

    def add_canvas_element(self, element):
        verify.verifyObject(
                interfaces.Renderable,
                element)
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
        for blank in self.board.blanks:
            blank.init_renderable()

        self.canvas.render()
        self.state_machine.start()
        self.traversal.discover_all_winning_states()
        # self.paths = self.traversal.get_all_winning_paths()
        # self.current_path = self.paths[0]
        # self.current_step = -1
        # self.ready_for_next = True

    def handle_mouse_click(self, button, state, x, y):
        if button == 0 and state == 1:
            transformed_x, transformed_y = self.canvas.transform_click(x, y)
            self.state_machine.current_state.handle_click(
                owner=self,
                x=transformed_x,
                y=transformed_y)


    def handle_keyboard(self, key, *args, **kwargs):
        if key == ' ':
            self.interactive = not self.interactive

        if key in (GLUT.GLUT_KEY_UP,
                   GLUT.GLUT_KEY_DOWN,
                   GLUT.GLUT_KEY_LEFT,
                   GLUT.GLUT_KEY_RIGHT):
            self.state_machine.current_state.handle_keyboard_direction(
                owner=self,
                key=key)

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
        
        if direction is board.Direction.UP:
            move = (-1, 0)
        elif direction is board.Direction.DOWN:
            move = (1, 0)
        elif direction is board.Direction.LEFT:
            move = (0, -1)
        elif direction is board.Direction.RIGHT:
            move = (0, 1)

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
    
    def getAllCanvasElements(self):
        return self.canvasElements

verify.verifyClass(interfaces.IWorld, PianoWorld)
