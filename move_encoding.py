# Various conversions between move formats. 
# For performance, internally moves are encoded into 32bit unsigned integers, containing source, destination, and move type information
import numpy as np
from numpy import uint32 as u32,uint64 as u64

import bb_utils
from chess_enums import *
from board import Board

#Given two pieces and move info, encodes the move into uint32 format
def encode(source: Piece, destination: Piece, special:Special)->u32:
    encoded_move = np.uint32(0)
    offset = 0
    encoded_move |= _encode_piece(source)
    offset += source.bit_size
    encoded_move |= _encode_piece(destination) << offset
    offset += destination.bit_size
    encoded_move |= _encode_special(special) << offset
    return encoded_move

#Decodes the source and destination square information from uint32 format
def decode_from_to(encoded_move:u32):
    source = _decode_piece(encoded_move,True)
    dest = _decode_piece(encoded_move,False)
    return (source,dest)

#Decodes the whole move information from uint32 format
def decode_move(encoded_move:u32):
    locations = decode_from_to(encoded_move)
    special = _decode_special(encoded_move)
    move = Move(locations[0],locations[1],special)
    return move

#Converts the player given move to uint32 format
def encode_string(board:Board, move_string:str)->u32:
    '''Encodes the human-friendly string into a move code
    
    Format
    ---------
    'file+rank file+rank'
    '''
    parts = move_string.split(' ')
    source = parts[0]
    dest = parts[1]
    source_index = square_str_to_index(source)
    dest_index = square_str_to_index(dest)
    s_piece = bb_utils.get_piece_from_square(board.position,source_index)
    d_piece = bb_utils.get_piece_from_square(board.position,dest_index)
    special = Special(MoveType.QUIET,CheckFlags.NONE)
    encoded_move = encode(s_piece,d_piece,special)
    return encoded_move

#Decodes the uint32 move into detailed information to print for the user
def decode_to_string_verbose(encoded_move:u32)->str:
    '''Decodes the move into a human-friendly formatted string with move details'''
    decoded_move = decode_move(encoded_move)
    source = decoded_move.source
    dest = decoded_move.destination
    move_type = decoded_move.info.move_type
    source_square_name = square_index_to_str(source.square_index)
    dest_square_name = square_index_to_str(dest.square_index)
    action = "moves to"
    if move_type == MoveType.CAPTURE:
        action = "captures"
    elif move_type in [MoveType.KING_CASTLE,MoveType.QUEEN_CASTLE]:
        action = "castles on"
    target = ""
    if dest.p_type != PieceType.EMPTY:
        target = f"{dest.p_type.name} on "
    target += dest_square_name
    return f"{source.p_type.name} on {source_square_name} {action} {target}"

#Decodes the uint32 move into less detailed information for the user
def decode_to_string_simple(encoded_move:u32)->str:
    '''Decodes to a human-friendly string with source info'''
    decoded_move = decode_move(encoded_move)
    source = decoded_move.source
    dest = decoded_move.destination
    source_square_name = square_index_to_str(source.square_index)
    dest_square_name = square_index_to_str(dest.square_index)
    target = dest_square_name
    return f"{source.p_type.name} {source_square_name} to {target}"

#Decodes the square index to traditional square name
def square_index_to_str(square_index:int)->str:
    files = ['a','b','c','d','e','f','g','h']
    r = str(int((square_index/8) + 1))
    f = files[7-(square_index%8)]
    return f+r

#Encodes the traditional square name into the square index
def square_str_to_index(square_string:str)->int:
    files = ['a','b','c','d','e','f','g','h']
    try:
        f = 7 - files.index(square_string[0])
        r = (int(square_string[1])-1)*8
        return f+r
    except:
        print("INVALID SQUARE")
        return 64

#Generates the FEN for the given board position
def generate_FEN(board:Board)->str:
        def _FEN_helper(fen:str, bb:u64, piece:str)->str:
            bits_str = "{:064b}".format(bb,'b')
            for i in range(len(bits_str)):
                if bits_str[i] == '1':
                    fen[i] = piece
            return fen
        piece_masks = board.position.piece_masks
        color_masks = board.position.color_masks
        position = board.position
        fen = ["."]*64
        #pawns
        fen = _FEN_helper(fen,color_masks[Color.BLACK.value] & piece_masks[PieceType.PAWN.value],'p')
        fen = _FEN_helper(fen,color_masks[Color.WHITE.value] & piece_masks[PieceType.PAWN.value],'P')
        fen = _FEN_helper(fen,color_masks[Color.BLACK.value] & piece_masks[PieceType.ROOK.value],'r')
        fen = _FEN_helper(fen,color_masks[Color.WHITE.value] & piece_masks[PieceType.ROOK.value],'R')
        fen = _FEN_helper(fen,color_masks[Color.BLACK.value] & piece_masks[PieceType.KNIGHT.value],'n')
        fen = _FEN_helper(fen,color_masks[Color.WHITE.value] & piece_masks[PieceType.KNIGHT.value],'N')
        fen = _FEN_helper(fen,color_masks[Color.BLACK.value] & piece_masks[PieceType.BISHOP.value],'b')
        fen = _FEN_helper(fen,color_masks[Color.WHITE.value] & piece_masks[PieceType.BISHOP.value],'B')
        fen = _FEN_helper(fen,color_masks[Color.BLACK.value] & piece_masks[PieceType.QUEEN.value],'q')
        fen = _FEN_helper(fen,color_masks[Color.WHITE.value] & piece_masks[PieceType.QUEEN.value],'Q')
        fen = _FEN_helper(fen,color_masks[Color.BLACK.value] & piece_masks[PieceType.KING.value],'k')
        fen = _FEN_helper(fen,color_masks[Color.WHITE.value] & piece_masks[PieceType.KING.value],'K')
        res = "".join(fen)
        full_str = '/'.join(res[x:x+8] for x in range(0,len(res),8))
        position_str = ""
        empty_count = 0
        for c in range(len(full_str)):
            if full_str[c] == '.':
                empty_count += 1
            else:
                if empty_count > 0:
                    position_str += str(empty_count)
                    empty_count = 0
                position_str += full_str[c]
        if empty_count > 0:
            position_str += str(empty_count)

        to_move = 'w' if position.w_to_move else 'b'
        castle_rights = ""
        castle_rights += "K" if position.w_k_castle else ""
        castle_rights += "Q" if position.w_q_castle else ""
        castle_rights += "k" if position.b_k_castle else ""
        castle_rights += "q" if position.b_q_castle else ""
        castle_rights = "-" if len(castle_rights) == 0 else castle_rights

        en_pass_str = square_index_to_str(position.en_passant_target_index) if position.en_passant_target_index != 64 else '-'
        halfmoves = str(position.half_move_clock)
        fullmoves = str(position.full_move_counter)

        return f"{position_str} {to_move} {castle_rights} {en_pass_str} {halfmoves} {fullmoves}"

#Helper funtions for encoding and decoding parts of the uint32 format

def _encode_piece(piece:Piece)->u32:
    encoded = u32(piece.square_index)
    encoded |= (piece.p_type.value << 6)
    encoded |= (piece.p_color.value << 9)
    return encoded

def _encode_special(special:Special):
    encoded = special.move_type.value
    encoded |= (special.check_flags.value << 4)
    return encoded

def _decode_piece(encoded_piece:u32, is_source:bool):
    if is_source == False:
        encoded_piece >>= 10
    square_index = encoded_piece & u32(0x3f)
    p_type = PieceType((encoded_piece&u32(0x1c0)) >> 6)
    color = Color.WHITE if (encoded_piece & u32(0x200)) >> 9 == 0 else Color.BLACK
    result = Piece(color,p_type,square_index)
    return result

def _decode_special(encoded_move:u32):
    encoded_move >>= 20
    move_type = MoveType(encoded_move & u32(0xf))
    check_type = CheckFlags((encoded_move & u32(0x30)) >> 4)
    special = Special(move_type,check_type)
    return special
