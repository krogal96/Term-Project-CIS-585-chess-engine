# File with helper funtions related to bitboard operations

import numpy as np
from numpy import uint64 as u64
from typing import List

from position import Position
from constants import Direction as DIR,Board as BD
from chess_enums import *

#Not the fastest way to do so, but fast enough for this application
def pop_count(bb:u64)->int:
    '''Returns the number of "1" bits in the bitboard'''
    return bin(bb).count('1')

#Used to find the square index of a single piece
def bitscan_fwd(bb:u64)->int:
    '''Returns the number of trailing "0" bits in the bitboard'''
    if bb == 0:
        return 64
    index = 0
    while ((bb >> u64(index)) & u64(1)) == 0:
        index += 1
    return index

#Isolates each active bit into its own mask, useful for separating bitboards by pieces
def get_piecewise_bits(bb:u64)->List[u64]:
    '''Returns a mask for each active bit in the bitboard'''
    piece_indexes = []
    res = 0
    while res != 64:
        res = bitscan_fwd(u64(bb))
        if res != 64:
            piece_indexes.append(res)
            bb -= u64(1)<<u64(res)
    return piece_indexes

#Turns a square index into its corresponding mask
def u64_from_index(square_index: int)->u64:
    '''Converts a square index to a mask of that square'''
    return u64(1) << u64(square_index)

#Looks up information about the occupancy of a square
def get_piece_from_square(position:Position, square_index:int)->Piece:
    '''Returns Piece for the given square index'''    
    square_mask = u64_from_index(square_index)
    piece_types = [ PieceType.PAWN,PieceType.KNIGHT,PieceType.BISHOP,
                    PieceType.ROOK,PieceType.QUEEN,PieceType.KING]
    empty_mask = ~(position.color_masks[Color.WHITE.value]|position.color_masks[Color.BLACK.value])
    #returns empty if it is not an occupied square
    if square_mask & empty_mask != 0:
        return Piece(Color.WHITE,PieceType.EMPTY,square_index)
    color = Color.WHITE if square_mask & position.color_masks[Color.WHITE.value] else Color.BLACK

    for piece in piece_types:
        if position.piece_masks[piece.value] & square_mask != 0:
            return Piece(color,piece,square_index)

#Returns a mask with all active bits shifted in the given direction without allowing wrapping around board edges  
def move(board: u64, direction: DIR)->u64:
    '''Returns a bitboard shifted in the given compass direction without edge wrapping'''
    if direction.value in [DIR.N.value, DIR.S.value]:
        mask = np.iinfo(u64).max
    #East without wrap
    elif direction.value in [DIR.E.value, DIR.NE.value, DIR.SE.value]:
        mask = ~BD.FILE_A
    #West without wrap
    else:
        mask = ~BD.FILE_H
    
    #Determines which bitshift to use
    if direction.value < 0:
        return (board << u64(-direction.value)) & mask
    else:
        return (board >> u64(direction.value)) & mask

#Used to get combinations of blockers from a mask, used in magic tables to make sure all combinations are stored in the table
def generate_blocker_combo_from_index(mask_index:int,blocker_mask: u64)->u64:
    '''Returns a mask containing a unique combination of blockers from the provided blocker mask'''
    subset = blocker_mask
    bit_index = 0
    for i in range(64):
        if blocker_mask&(u64(1)<<u64(i)) > 0:
            if u64(mask_index) & (u64(1)<<u64(bit_index)) == 0:
                subset &= ~(u64(1)<<u64(i))
            bit_index += 1
    return subset

#Calculates rook moves step by step for use in populating the magic tables
def calc_rook_moves(square_index:int, occ:u64)->u64:
    '''Returns calculated rook moves for the given square index and blocker mask'''
    result = u64(0)
    rank = int(square_index/8)
    file = square_index%8
    for r in range(rank+1,8):
        north = u64(1) << u64(file+r*8)
        result |= north
        if occ&north != 0:
            break
    for r in range(rank-1,-1,-1):
        south = u64(1) << u64(file+r*8)
        result |= south
        if occ&south != 0:
            break
    for f in range(file+1,8):
        east = u64(1) << u64(f+rank*8)
        result |= east
        if occ&east != 0:
            break
    for f in range(file-1,-1,-1):
        west = u64(1) << u64(f+rank*8)
        result |= west
        if occ&west != 0:
            break
    return result

#Calculates bishop moves step by step for use in populating the magic tables
def calc_bishop_moves(square_index:int, occ:u64)->u64:
    '''Returns calculated bishop moves for the given square index and blocker mask'''
    result = u64(0)
    rank = int(square_index/8)
    file = square_index%8

    r = rank + 1
    f = file + 1
    while r <= 7 and f <= 7:
        res = u64(1) << u64(f+r*8)
        result |= res
        if occ&res != 0:
            break
        r += 1
        f += 1

    r = rank + 1
    f = file - 1
    while r <= 7 and f >= 0:
        south = u64(1) << u64(f+r*8)
        result |= south
        if occ&south != 0:
            break
        r += 1
        f -= 1

    r = rank - 1
    f = file + 1
    while r >= 0 and f <= 7:
        east = u64(1) << u64(f+r*8)
        result |= east
        if occ&east != 0:
            break
        r -= 1
        f += 1

    r = rank - 1
    f = file - 1
    while r >= 0 and f >= 0:
        west = u64(1) << u64(f+r*8)
        result |= west
        if occ&west != 0:
            break
        r -= 1
        f -= 1

    return result