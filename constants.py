#Contains various constants related to bitboards and common FEN strings

from numpy import uint64 as u64
from dataclasses import dataclass
from enum import Enum

@dataclass
class Board:
    EMPTY = u64(0)
    FULL = u64(0xffffffffffffffff)

    DEFAULT_W = u64(0x000000000000ffff)
    DEFAULT_B = u64(0xffff000000000000)

    DEFAULT_PAWN = u64(0x00ff00000000ff00)
    DEFAULT_ROOK = u64(0x8100000000000081)
    DEFAULT_KNIGHT = u64(0x4200000000000042)
    DEFAULT_BISHOP = u64(0x2400000000000024)
    DEFAULT_QUEEN = u64(0x1000000000000010)
    DEFAULT_KING = u64(0x0800000000000008)

    FILE_A = u64(0x8080808080808080)
    FILE_B = u64(0x4040404040404040)
    FILE_C = u64(0x2020202020202020)
    FILE_D = u64(0x1010101010101010)
    FILE_E = u64(0x0808080808080808)
    FILE_F = u64(0x0404040404040404)
    FILE_G = u64(0x0202020202020202)
    FILE_H = u64(0x0101010101010101)

    RANK_1 = u64(0x00000000000000ff)
    RANK_2 = u64(0x000000000000ff00)
    RANK_3 = u64(0x0000000000ff0000)
    RANK_4 = u64(0x00000000ff000000)
    RANK_5 = u64(0x000000ff00000000)
    RANK_6 = u64(0x0000ff0000000000)
    RANK_7 = u64(0x00ff000000000000)
    RANK_8 = u64(0xff00000000000000)

    DIAG_A8_A8 = u64(0x8000000000000000)
    DIAG_A7_B8 = u64(0x4080000000000000)
    DIAG_A6_C8 = u64(0x2040800000000000)
    DIAG_A5_D8 = u64(0x1020408000000000)
    DIAG_A4_E8 = u64(0x0810204080000000)
    DIAG_A3_F8 = u64(0x0408102040800000)
    DIAG_A2_G8 = u64(0x0204081020408000)
    DIAG_A1_H8 = u64(0x0102040810204080)
    DIAG_B1_H7 = u64(0x0001020408102040)
    DIAG_C1_H6 = u64(0x0000010204081020)
    DIAG_D1_H5 = u64(0x0000000102040810)
    DIAG_E1_H4 = u64(0x0000000001020408)
    DIAG_F1_H3 = u64(0x0000000000010204)
    DIAG_G1_H2 = u64(0x0000000000000102)
    DIAG_H1_H1 = u64(0x0000000000000001)

    ADIAG_A1_A1 = u64(0x0000000000000080)
    ADIAG_B1_A2 = u64(0x0000000000008040)
    ADIAG_C1_A3 = u64(0x0000000000804020)
    ADIAG_D1_A4 = u64(0x0000000080402010)
    ADIAG_E1_A5 = u64(0x0000008040201008)
    ADIAG_F1_A6 = u64(0x0000804020100804)
    ADIAG_G1_A7 = u64(0x0080402010080402)
    ADIAG_H1_A8 = u64(0x8040201008040201)
    ADIAG_H2_B8 = u64(0x4020100804020100)
    ADIAG_H3_C8 = u64(0x2010080402010000)
    ADIAG_H4_D8 = u64(0x1008040201000000)
    ADIAG_H5_E8 = u64(0x0804020100000000)
    ADIAG_H6_F8 = u64(0x0402010000000000)
    ADIAG_H7_G8 = u64(0x0201000000000000)
    ADIAG_H8_H8 = u64(0x0100000000000000)

    #The squares which must be empty for a castle
    W_KING_CASTLE_MASK = u64(0x6)
    W_QUEEN_CASTLE_MASK = u64(0x70)
    B_KING_CASTLE_MASK = u64(0x600000000000000)
    B_QUEEN_CASTLE_MASK = u64(0x7000000000000000)

    #The squares where the castle can occur
    W_KING_CASTLE_SQUARE = u64(0x2)
    W_QUEEN_CASTLE_SQUARE = u64(0x20)
    B_KING_CASTLE_SQUARE = u64(0x200000000000000)
    B_QUEEN_CASTLE_SQUARE = u64(0x2000000000000000)

    PERIMETER = u64(0xff018101810181ff)
    CORNERS = u64(0x8100000000000081)

    CENTER = u64(0x0000001818000000)
    EXTENDED_CENTER = u64(0x00003c3c3c3c0000)

    SQUARES_BY_INDEX = ['h1','g1','f1','e1','d1','c1','b1','a1',
                        'h2','g2','f2','e2','d2','c2','b2','a2',
                        'h3','g3','f3','e3','d3','c3','b3','a3',
                        'h4','g4','f4','e4','d4','c4','b4','a4',
                        'h5','g5','f5','e5','d5','c5','b5','a5',
                        'h6','g6','f6','e6','d6','c6','b6','a6',
                        'h7','g7','f7','e7','d7','c7','b7','a7',
                        'h8','g8','f8','e8','d8','c8','b8','a8' ]
    
    INDEX_BY_SQUARE = { 'h1':0,'g1':1,'f1':2,'e1':3,'d1':4,'c1':5,'b1':6,'a1':7,
                        'h2':8,'g2':9,'f2':10,'e2':11,'d2':12,'c2':13,'b2':14,'a2':15,
                        'h3':16,'g3':17,'f3':18,'e3':19,'d3':20,'c3':21,'b3':22,'a3':23,
                        'h4':24,'g4':25,'f4':26,'e4':27,'d4':28,'c4':29,'b4':30,'a4':31,
                        'h5':32,'g5':33,'f5':34,'e5':35,'d5':36,'c5':37,'b5':38,'a5':39,
                        'h6':40,'g6':41,'f6':42,'e6':43,'d6':44,'c6':45,'b6':46,'a6':47,
                        'h7':48,'g7':49,'f7':50,'e7':51,'d7':52,'c7':53,'b7':54,'a7':55,
                        'h8':56,'g8':57,'f8':58,'e8':59,'d8':60,'c8':61,'b8':62,'a8':63  }

#Amounts to shift bitboards by to move in a certain direction, here for convience and readability.
@dataclass
class Direction(Enum):
    NW = -9
    N = -8
    NE = -7
    W = -1
    E = 1
    SW = 7
    S = 8
    SE = 9

@dataclass
class Pieces(Enum):
    EMPTY = 0
    p = 1
    r = 2
    n = 3
    b = 4
    q = 5
    k = 6
    P = 7
    R = 8
    N = 9
    B = 10
    Q = 11
    K = 12

@dataclass
class FENStrings:
    START_POS = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    START_POS_ROTATE_180 = "RNBKQBNR/PPPPPPPP/8/8/8/8/pppppppp/rnbkqbnr w KQkq - 0 1"
    PAWN_TEST_POS = "k7/ppp5/1PPP4/8/6p1/6P1/8/K7 w - - 0 50"