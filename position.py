#Contains all board state information needed to represent a position

from constants import Board as BD
from chess_enums import GameState, PieceType, Color

class Position:
    def __init__(self) -> None:
        self.color_masks = {Color.BLACK.value:BD.DEFAULT_B, Color.WHITE.value:BD.DEFAULT_W}
        self.piece_masks = {PieceType.PAWN.value:BD.DEFAULT_PAWN, PieceType.ROOK.value:BD.DEFAULT_ROOK, 
                    PieceType.KNIGHT.value:BD.DEFAULT_KNIGHT, PieceType.BISHOP.value:BD.DEFAULT_BISHOP, 
                    PieceType.QUEEN.value:BD.DEFAULT_QUEEN, PieceType.KING.value:BD.DEFAULT_KING}

        self.w_to_move:bool = True
        self.w_q_castle:bool = True
        self.w_k_castle:bool = True
        self.b_q_castle:bool = True
        self.b_k_castle:bool = True
        self.en_passant_target_index:int = 64
        self.half_move_clock:int = 0
        self.full_move_counter:int = 1

        self.checks_up_to_date:bool = False
        self.w_in_check:bool = False
        self.b_in_check:bool = False

        self.game_state:GameState = GameState.IN_PROGRESS