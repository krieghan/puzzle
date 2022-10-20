from game_common import (
    statemachine)
from zope.interface import (
    implementer,
    verify)

from piano import (
    board)

class PianoState(object):
    @classmethod
    def handle_click(cls, owner, x, y):
        pass

    @classmethod
    def handle_keyboard_direction(cls, owner, key):
        pass


@implementer(statemachine.IState)
class WaitForPieceSelection(PianoState):
    @classmethod
    def enter(cls,
              owner):
        pass
        
    @classmethod
    def exit(cls,
             owner):
        pass
        
    @classmethod
    def execute(cls,
                owner):
        if not owner.interactive:
            owner.initiate_auto_move()

    @classmethod
    def handle_click(cls, owner, x, y):
        piece = owner.board.select_game_piece(
            x,
            y)
        if piece is not None:
            moves = owner.board.find_moves().get(piece)
            if moves is None or len(moves) == 0:
                return
            elif len(moves) == 1:
                owner.selected_piece = piece
                owner.selected_move = moves[0]

                owner.state_machine.change_state(
                    AnimateUserMove)

                return
            elif len(moves) > 1:
                owner.selected_piece = piece
                owner.state_machine.change_state(
                    WaitForMoveSelection)
                return


@implementer(statemachine.IState)
class WaitForMoveSelection(PianoState):
    @classmethod
    def enter(cls,
              owner):
        owner.swapped_color = owner.selected_piece.color
        owner.selected_piece.color = (1, 1, 1)
        
    @classmethod
    def exit(cls,
             owner):
        owner.selected_piece.color = owner.swapped_color
        
    @classmethod
    def execute(cls,
                owner):
        if not owner.interactive:
            owner.initiate_auto_move()

    @classmethod
    def handle_click(cls, owner, x, y):
        blank = owner.board.select_game_piece(
            x,
            y,
            piece_type='blanks')
        if blank is not None:
            moves = owner.board.find_moves().get(owner.selected_piece)
            for move in moves:
                if blank in move.displaced_blanks:
                    owner.selected_move = move
                    owner.state_machine.change_state(
                        AnimateUserMove)
                    return
        else:
            piece = owner.board.select_game_piece(
                x,
                y)
            if piece is owner.selected_piece:
                owner.state_machine.change_state(
                    WaitForPieceSelection)

    @classmethod
    def handle_keyboard_direction(cls, owner, key):
        direction = board.Direction.direction_by_key[key]
        moves = owner.board.find_moves().get(owner.selected_piece)
        for move in moves:
            if move[4] == direction:
                owner.animation_move = move
                owner.state_machine.change_state(
                    AnimateUserMove)
                return
        owner.state_machine.change_state(
            WaitForPieceSelection)


@implementer(statemachine.IState)
class AnimateUserMove(PianoState):
    transition_time = 1000

    @classmethod
    def enter(cls,
              owner):
        owner.start_animation(owner.selected_move)
        
    @classmethod
    def exit(cls,
             owner):
        owner.piece_to_move.end_animation()
        owner.selected_piece = None
        owner.piece_to_move = None

        
    @classmethod
    def execute(cls,
                owner):
        owner.piece_to_move.update_animation(owner.current_time)
        if owner.current_time > owner.animate_end:
            if owner.interactive:
                owner.state_machine.change_state(WaitForPieceSelection)
            else:
                owner.initiate_auto_move()


@implementer(statemachine.IState)
class AutoAnimate(PianoState):
    @classmethod
    def enter(cls,
              owner):
        (next_state, move) = next(owner.path)
        owner.start_animation(move)
        
    @classmethod
    def exit(cls,
             owner):
        owner.piece_to_move.end_animation()
        owner.piece_to_move = None
        
    @classmethod
    def execute(cls,
                owner):
        owner.piece_to_move.update_animation(owner.current_time)
        if owner.current_time > owner.animate_end:
            if owner.interactive:
                owner.state_machine.change_state(WaitForPieceSelection)
            else:
                owner.state_machine.change_state(AutoAnimate)
