#Core of the chess engine, contains the main board state and a search function to select a move

from board import Board
from search import Search
from numpy import uint32 as u32
from typing import Tuple
import move_encoding
import bb_utils
from chess_enums import *
import copy

class GameEngine():
    def __init__(self) -> None:
        self.board = Board()
        self.search = Search()
        super().__init__()

    def set_position(self,board:Board):
        self.board.position = copy.deepcopy(board.position)

    #Searches for the best move, then plays it and returns the move
    def make_engine_move(self)->u32:
        move = self._search_best_move()
        if move == 0:
            print("NO VALID MOVES")
        else:
            self.board.make_move(move)
        return move
    
    #Prints the list of valid moves and the engine's evaluation for each one
    def display_engine_moves(self)->None:
        moves = self.search.get_move_list(self.board)
        move_codes = [x[0] for x in moves]
        evaluations = [x[1] for x in moves]

        print("-"*35)
        print("MOVES")
        print("-"*35)
        for i in range(len(move_codes)):
           self._display_engine_move_info(move_codes[i],evaluations[i])

    #Helper function that displays verbose information about the given move code
    def _display_engine_move_info(self, move_code:u32, eval:float)->None:
        file_names = ['a','b','c','d','e','f','g','h']
        print(f"Move Code: {move_encoding.decode_to_string_verbose(move_code)}")
        print(f"Evaluation: {eval}")
        decoded = move_encoding.decode_move(move_code)
        match decoded.info.check_flags:
            case move_encoding.CheckFlags.NONE:
                check = ""
            case move_encoding.CheckFlags.CHECK:
                check = "+"
            case move_encoding.CheckFlags.CHECKMATE:
                check = "#"
        print(f"Move Type: {decoded.info.move_type.name}{check}")
        print("-"*35)

    #Makes an externally chosen move to update the board state, either from another engine or the human player
    #Also verifies that it is a valid move.
    def make_manual_move(self, move_code:u32)->u32:
        corrected_code = self.validate_and_correct_move_code(move_code)
        if corrected_code != 0:
            self.board.make_move(corrected_code)
        return corrected_code

    #Validates the move code, and updates the move with more information if valid
    def validate_and_correct_move_code(self, move_code:u32)->u32:
        '''Validates if the source and destination are valid
        
        Overwrites move info with correct values'''
        move = move_encoding.decode_move(move_code)
        source_piece = move.source
        piece_square = source_piece.square_index
        piece_type = source_piece.p_type
        piece_color = source_piece.p_color
        destination_mask = bb_utils.u64_from_index(move.destination.square_index)
        move_mask = self.search.move_generator.get_mask_for_square(self.board,piece_square)
        valid = (move_mask&destination_mask != 0)
        if valid:
            new_code = self._populate_move_type(move_code)
            return new_code
        else:
            return u32(0)

    #Determines the type of move based on the source and destination squares
    def _populate_move_type(self,move:u32)->u32:
        decoded = move_encoding.decode_move(move)
        source = decoded.source
        dest = decoded.destination
        m_type = decoded.info.move_type
        if source.p_type == PieceType.PAWN and dest.p_type == PieceType.EMPTY:
            m_type = MoveType.PAWN_MOVE
        elif dest.p_type == PieceType.EMPTY:
            m_type = MoveType.CAPTURE

        #Castle moves
        elif source.p_type == PieceType.KING:
            if source.p_color == Color.WHITE:
                if source.square_index == 3:
                    if dest.square_index == 1:
                        m_type = MoveType.KING_CASTLE
                    elif dest.square_index == 5:
                        m_type = MoveType.QUEEN_CASTLE
            else:
                if source.square_index == 59:
                    if dest.square_index == 57:
                        m_type = MoveType.KING_CASTLE
                    elif dest.square_index == 61:
                        m_type = MoveType.QUEEN_CASTLE
        new_special = Special(m_type,decoded.info.check_flags)
        new_code = move_encoding.encode(source,dest,new_special)
        return new_code

    #Returns the best move determined by the search algorithm,
    def _search_best_move(self)->Tuple[u32,float]:
        return self.search.get_new_best_move(self.board)