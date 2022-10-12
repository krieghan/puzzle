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
    def handle_mode_switch(cls, owner):
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
            owner.state_machine.change_state(
                AutoAnimate)

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
                owner.piece_to_move = piece
                owner.animation_move = moves[0]

                owner.state_machine.change_state(
                    AnimateUserMove)

                return
            elif len(moves) > 1:
                owner.piece_to_move = piece
                owner.state_machine.change_state(
                    WaitForMoveSelection)
                return


@implementer(statemachine.IState)
class WaitForMoveSelection(PianoState):
    @classmethod
    def enter(cls,
              owner):
        owner.swapped_color = owner.piece_to_move.color
        owner.piece_to_move.color = (1, 1, 1)
        
    @classmethod
    def exit(cls,
             owner):
        owner.piece_to_move.color = owner.swapped_color
        
    @classmethod
    def execute(cls,
                owner):
        if not owner.interactive:
            owner.piece_to_move = None
            owner.state_machine.change_state(
                AutoAnimate)

    @classmethod
    def handle_click(cls, owner, x, y):
        blank = owner.board.select_game_piece(
            x,
            y,
            piece_type='blanks')
        if blank is not None:
            moves = owner.board.find_moves().get(owner.piece_to_move)
            for move in moves:
                matched_blanks = move[2]
                if blank in matched_blanks:
                    owner.animation_move = move
                    owner.state_machine.change_state(
                        AnimateUserMove)
                    return
        else:
            piece = owner.board.select_game_piece(
                x,
                y)
            if piece is owner.piece_to_move:
                owner.state_machine.change_state(
                    WaitForPieceSelection)

    @classmethod
    def handle_keyboard_direction(cls, owner, key):
        direction = board.Direction.direction_by_key[key]
        moves = owner.board.find_moves().get(owner.piece_to_move)
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
        owner.animate_start = owner.current_time
        owner.animate_end = owner.current_time + cls.transition_time
        direction = owner.animation_move[4]
        if direction is board.Direction.UP:
            move = (-1, 0)
        elif direction is board.Direction.DOWN:
            move = (1, 0)
        elif direction is board.Direction.LEFT:
            move = (0, -1)
        elif direction is board.Direction.RIGHT:
            move = (0, 1)
        visual_move = (
            move[1] * owner.tile_width,
            -move[0] * owner.tile_height)
        owner.piece_to_move.start_animation(
            move=move,
            visual_move=visual_move,
            animate_start=owner.animate_start,
            animate_end=owner.animate_end,
            transition_time=cls.transition_time,
            move_data=owner.animation_move)
        
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


@implementer(statemachine.IState)
class AutoAnimate(PianoState):
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
        pass

    @classmethod
    def handle_click(cls, owner, x, y):
        return

