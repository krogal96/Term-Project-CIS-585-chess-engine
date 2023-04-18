#Contains the board representation for a given point in the game wrapped with some common operations
import copy
from typing import Dict
from numpy import uint32 as u32, uint64 as u64
import collections

import bb_utils
import move_encoding
from position import Position
from chess_enums import GameState,Color,PieceType,Piece

class Board:
    def __init__(self,position: Position = Position())->None:
        if position != None:
            self.position = copy.deepcopy(position)
        else:
            self.position = copy.deepcopy(Position())

    #Used to get a deep copy of the board to allow for move search and validation
    def deep_copy(self)->'Board':
        return copy.deepcopy(Board(copy.deepcopy(self.position)))

    def get_empty(self)->u64:
        '''Returns a mask of unoccupied squares'''
        return ~(self.position.color_masks[Color.WHITE.value] | self.position.color_masks[Color.BLACK.value])
    
    def get_occupied(self)->u64:
        '''Returns a mask of squares occupied by any piece'''
        return self.position.color_masks[Color.WHITE.value] | self.position.color_masks[Color.BLACK.value]

    #Updates the position using the given move
    #This step does not validate the move! It is expected to already by validated by this point.
    def _update_position(self, move: u32)->None:
        decoded_move = move_encoding.decode_from_to(move)
        source_index = decoded_move[0].square_index
        dest_index = decoded_move[1].square_index
        source_mask = bb_utils.u64_from_index(source_index)
        dest_mask = bb_utils.u64_from_index(dest_index)
        friendly_update_mask = source_mask|dest_mask
        source_type = decoded_move[0].p_type
        source_color = decoded_move[0].p_color
        #Toggles the starting and ending positions for piece and color masks
        self.position.piece_masks[source_type.value] ^= friendly_update_mask
        self.position.color_masks[source_color.value] ^= friendly_update_mask

        #If a piece is captured, toggle opponent color and piece masks as well
        if decoded_move[1].p_type != PieceType.EMPTY:
            self.position.piece_masks[decoded_move[1].p_type.value] ^= (dest_mask)
            self.position.color_masks[decoded_move[1].p_color.value] ^= (dest_mask)
    
    #Returns a copy of the position updated by a given move
    def _copy_updated_masks(self, old_color_masks:Dict[Color,u64], old_piece_masks:Dict[PieceType,u64], move: u32)->Position:
        color_masks = copy.deepcopy(old_color_masks)
        piece_masks = copy.deepcopy(old_piece_masks)
        decoded_move = move_encoding.decode_from_to(move)
        source_index = decoded_move[0].square_index
        dest_index = decoded_move[1].square_index
        source_mask = bb_utils.u64_from_index(source_index)
        dest_mask = bb_utils.u64_from_index(dest_index)
        friendly_update_mask = source_mask|dest_mask
        #Toggles the starting and ending positions for piece and color masks
        piece_masks[decoded_move[0].p_type.value] ^= friendly_update_mask
        color_masks[decoded_move[0].p_color.value] ^= friendly_update_mask

        #If a piece is captured, toggle opponent color and piece masks as well
        if decoded_move[1].p_type != PieceType.EMPTY:
            piece_masks[decoded_move[1].p_type.value] ^= (dest_mask)
            color_masks[decoded_move[1].p_color.value] ^= (dest_mask)

        #Builds a tuple of the position's mask copies and returns it
        Masks = collections.namedtuple('Masks', ['color','piece'])
        return Masks(color_masks,piece_masks)
    
    #Updates the current position by the specified move, also updating game state information
    def make_move(self, move_code: u32)->None:
        '''Updates the current board state for the given move code'''
        move_info = move_encoding.decode_move(move_code)
        source_piece:Piece = move_info.source
        dest_piece:Piece = move_info.destination
        move_type = move_info.info.move_type
        self._update_position(move_code)

        #Clear En passant target square
        self.position.en_passant_target_index = 64

        #After black makes a move, increment the full move counter
        if not self.position.w_to_move:
            self.position.full_move_counter += 1

        #Reset the halfmove clock if the move was not a pawn move or a capture, otherwise increment it
        if move_type in [move_encoding.MoveType.PAWN_MOVE,move_encoding.MoveType.CAPTURE]:
            self.position.half_move_clock = 0
            #If the pawn move was a double push, update the En Passant target square
            if move_type in [move_encoding.MoveType.PAWN_MOVE] and abs(dest_piece.square_index-source_piece.square_index) == 16:
                if source_piece.p_color == Color.WHITE:
                    self.position.en_passant_target_index = source_piece.square_index+8
                else:
                    self.position.en_passant_target_index = source_piece.square_index-8
        else:
            self.position.half_move_clock += 1

        #End the game via the 50 move rule if the halfmove clock reaches 50
        if self.position.half_move_clock >= 50:
            self.position.game_state = GameState.DRAW

        #Update appropriate castle rights
        #Rook moves lose their castle right
        if source_piece.p_type == PieceType.ROOK:
            if self.position.w_to_move:
                if self.position.w_k_castle and source_piece.square_index == 0:
                    self.position.w_k_castle = False
                elif self.position.w_q_castle and source_piece.square_index == 7:
                    self.position.w_q_castle = False
            else:
                if self.position.b_k_castle and source_piece.square_index == 56:
                    self.position.b_k_castle = False
                elif self.position.b_q_castle and source_piece.square_index == 63:
                    self.position.b_q_castle = False
        #King moves lose all castle rights
        elif source_piece.p_type == PieceType.KING:
            if self.position.w_to_move and source_piece.square_index == 3:
                if self.position.w_k_castle:
                    self.position.w_k_castle = False
                elif self.position.w_q_castle:
                    self.position.w_q_castle = False
            elif source_piece.square_index == 59:
                if self.position.b_k_castle:
                    self.position.b_k_castle = False
                elif self.position.b_q_castle:
                    self.position.b_q_castle = False

        #If the player castled, manually update the board to reflect it
        if move_type in [move_encoding.MoveType.QUEEN_CASTLE,move_encoding.MoveType.KING_CASTLE]:
            if dest_piece.square_index == 1:
                toggle_mask = u64(0x5)
            elif dest_piece.square_index == 5:
                toggle_mask = u64(0x90)
            elif dest_piece.square_index == 57:
                toggle_mask = u64(0x500000000000000)
            elif dest_piece.square_index == 61:
                toggle_mask = u64(0x9000000000000000)
            else:
                print("CASTLE MOVE INCORRECT")
            self.position.piece_masks[PieceType.ROOK.value] ^= toggle_mask
            self.position.color_masks[source_piece.p_color.value] ^= toggle_mask
        
        #Update side to move
        self.position.w_to_move = not self.position.w_to_move

    #Returns a copy of the current position if it were updated by the given move
    def make_move_copy(self, move_code: u32)->'Board':
        '''Returns a copy of the current board update with the given move code.
        
        Does NOT alter the current board state.'''
        new_board = copy.deepcopy(self)
        move_info = move_encoding.decode_move(move_code)
        source_piece:Piece = move_info.source
        dest_piece:Piece = move_info.destination
        move_type = move_info.info.move_type
        masks = self._copy_updated_masks(self.position.color_masks,self.position.piece_masks,move_code)
        new_board.position.color_masks = masks[0]
        new_board.position.piece_masks = masks[1]

                #Clear En passant target square
        self.position.en_passant_target_index = 64

        #After black makes a move, increment the full move counter
        if not new_board.position.w_to_move:
            new_board.position.full_move_counter += 1

        #Reset the halfmove clock if the move was not a pawn move or a capture, otherwise increment it
        if move_type in [move_encoding.MoveType.PAWN_MOVE,move_encoding.MoveType.CAPTURE]:
            new_board.position.half_move_clock = 0
            #If the pawn move was a double push, update the En Passant target square
            if move_type in [move_encoding.MoveType.PAWN_MOVE] and abs(dest_piece.square_index-source_piece.square_index) == 16:
                if source_piece.p_color == Color.WHITE:
                    new_board.position.en_passant_target_index = source_piece.square_index+8
                else:
                    new_board.position.en_passant_target_index = source_piece.square_index-8
        else:
            new_board.position.half_move_clock += 1

        #End the game via the 50 move rule if the halfmove clock reaches 50
        if new_board.position.half_move_clock >= 50:
            new_board.position.game_state = GameState.DRAW

        #Update appropriate castle rights
        #Rook moves lose their castle right
        if source_piece.p_type == PieceType.ROOK:
            if new_board.position.w_to_move:
                if new_board.position.w_k_castle and source_piece.square_index == 0:
                    new_board.position.w_k_castle = False
                elif new_board.position.w_q_castle and source_piece.square_index == 7:
                    new_board.position.w_q_castle = False
            else:
                if new_board.position.b_k_castle and source_piece.square_index == 56:
                    new_board.position.b_k_castle = False
                elif new_board.position.b_q_castle and source_piece.square_index == 63:
                    new_board.position.b_q_castle = False
        #King moves lose all castle rights
        elif source_piece.p_type == PieceType.KING:
            if new_board.position.w_to_move and source_piece.square_index == 3:
                if new_board.position.w_k_castle:
                    new_board.position.w_k_castle = False
                elif new_board.position.w_q_castle:
                    new_board.position.w_q_castle = False
            elif source_piece.square_index == 59:
                if new_board.position.b_k_castle:
                    new_board.position.b_k_castle = False
                elif new_board.position.b_q_castle:
                    new_board.position.b_q_castle = False

        #If the player castled, manually update the board to reflect it
        if move_type in [move_encoding.MoveType.QUEEN_CASTLE,move_encoding.MoveType.KING_CASTLE]:
            if dest_piece.square_index == 1:
                toggle_mask = u64(0x5)
            elif dest_piece.square_index == 5:
                toggle_mask = u64(0x90)
            elif dest_piece.square_index == 57:
                toggle_mask = u64(0x500000000000000)
            elif dest_piece.square_index == 61:
                toggle_mask = u64(0x9000000000000000)
            else:
                print("CASTLE MOVE INCORRECT")
            new_board.position.piece_masks[PieceType.ROOK.value] ^= toggle_mask
            new_board.position.color_masks[source_piece.p_color.value] ^= toggle_mask
        
        #Update side to move
        new_board.position.w_to_move = not new_board.position.w_to_move

        return new_board
    
    #Returns the internal board's in check flag, must be updated first
    def self_in_check(self)->bool:
        '''Returns the state of check in the position.
    
        Does not check the board state.'''
        result = self.position.w_in_check if self.position.w_to_move else self.position.b_in_check
        return result
    
    #Returns the current position
    def get_game_state(self)->GameState:
        return self.position.game_state

