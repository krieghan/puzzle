import zope.interface 
import zope.interface.verify

from game_common import (
        graph,
        interfaces)
from game_common.twodee.geometry import intersect
import board

@zope.interface.implementer(interfaces.IWorld)
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

        self.traversal = board.Traversal()
        self.canvasElements = set()

        self.current_time = 0

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
        zope.interface.verify.verifyObject(
                interfaces.Renderable,
                element)
        self.canvasElements.add(element)

    def remove_canvas_element(self, element):
        self.canvasElements.remove(element)

    def start(self):
        self.board = board.Board.from_initial_state()
        for piece in self.board.pieces:
            piece.init_renderable()
            self.add_canvas_element(piece)
        self.canvas.render()
        self.paths = self.traversal.get_all_winning_paths()
        self.current_path = self.paths[0]
        self.current_step = -1
        self.ready_for_next = True

    def update(self,
               currentTime):
        if self.ready_for_next:
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
            print()
            board.BoardState(self.board).print_self()
            print()
            for piece in self.board.pieces_by_type[piece_type]:
                if piece_from == (piece.row, piece.column):
                    piece_to_move = piece
                    break
            if piece_to_move is None:
                breakpoint()
                raise Exception()
            print('Move {} from {} to {}'.format(
                piece_type,
                piece_from,
                piece_to))
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

        '''
        if not self.current_time:
            self.current_time = currentTime
        timeElapsed = (currentTime - self.current_time)
        self.current_time = currentTime
        for canvasElement in list(self.getAllCanvasElements()):
            if not canvasElement.getActive():
                continue
            canvasElement.update(timeElapsed=timeElapsed)
        '''

    def render(self):
        for element in self.getAllCanvasElements():
            element.draw()
    
    def getAllCanvasElements(self):
        return self.canvasElements

zope.interface.verify.verifyClass(interfaces.IWorld, PianoWorld)
