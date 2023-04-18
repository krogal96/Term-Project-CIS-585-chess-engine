#File containing Enums representing various board objects and the data classes containing them

from enum import Enum

class PieceType(Enum):
    EMPTY = 0
    PAWN = 1
    KNIGHT = 2
    BISHOP = 3
    ROOK = 4
    QUEEN = 5
    KING = 6

class Color(Enum):
    WHITE = 0
    BLACK = 1    

class CastleType(Enum):
    NONE = 0
    KING = 1
    QUEEN = 2

class MoveType(Enum):
    QUIET = 0
    CAPTURE = 1
    QUEEN_PROMOTION = 4
    ROOK_PROMOTION = 5
    BISHOP_PROMOTION = 6
    KNIGHT_PROMOTION = 7
    KING_CASTLE = 8
    QUEEN_CASTLE = 9
    PAWN_MOVE = 10

class CheckFlags(Enum):
    NONE = 0
    CHECK = 1
    CHECKMATE = 3

class GameState(Enum):
    IN_PROGRESS = 0
    DRAW = 1
    W_WINS = 2
    B_WINS = 3

class Piece():
    def __init__(self,color,piece_type,index) -> None:
        self.p_color: Color = color
        self.p_type: PieceType = piece_type
        self.square_index: int = index
        self.bit_size:int = 10

#Contains various other information about the move
class Special():
    def __init__(self,move_t,check) -> None:
        self.move_type:MoveType = move_t # 4 bits
        self.check_flags:CheckFlags = check # 2 bits
        self.reserved:int = 0 # 6 bits
        self.bit_size:int = 12

class Move():
    def __init__(self,source_piece:Piece,dest_piece:Piece,special:Special):
        self.source = source_piece
        self.destination = dest_piece
        self.info = special