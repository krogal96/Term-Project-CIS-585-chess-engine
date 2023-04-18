#Contains the interface to the engine for the main.py file
#Allows for either Engine vs Engine games or Engine vs Human games

import re
from typing import List
import numpy as np
from numpy import uint32 as u32, uint64 as u64

import move_encoding
from game_engine import GameEngine
from position import Position
from board import Board
from chess_enums import GameState,Color,PieceType


class GameInterface:
    def __init__(self):
        self.engine = GameEngine()
        self.board = Board()
        self.valid_moves = []
        self.moves_up_to_date = False

    #Starts a Human vs Engine game
    def start_game(self, w_is_player=True, starting_state = None)->None:
        '''Starts the game against a human player'''
        self.board = Board()
        if starting_state != None:
            try:
                self.load_FEN(starting_state)
                GameEngine.set_position(self.board)
            except:
                print("Failed to load FEN, please check input")

        self.display_board_simple()

        #Main game loop, ends once the game state reaches a win or draw
        while(self.board.get_game_state() == GameState.IN_PROGRESS):
            if self.check_for_valid_moves():

                #Player turn
                if w_is_player == self.board.position.w_to_move:
                    self._ask_player_for_move()

                #Engine turn
                else:
                    move_played = self._make_engine_move()
                    if move_played != 0:
                        print(f"Engine played {move_encoding.decode_to_string_verbose(move_played)}")
                    else:
                        print("No valid moves!")
            #If out of moves and not a draw, override the game state
            elif self.board.get_game_state() != GameState.DRAW:
                if self.board.position.w_to_move:
                    self.board.position.game_state = GameState.B_WINS
                else:
                    self.board.position.game_state = GameState.W_WINS
            self.display_board_simple()
        print(self.board.get_game_state())

    #Starts Engine vs Engine game, deterministic if no noise is added to the evaluation
    def start_self_game(self,starting_state = None)->GameState:
        if starting_state == None:
            self.board = Board()
        else:
            try:
                self.board = self.load_FEN(starting_state)
            except:
                print("Failed to load FEN, please check input")

        self.display_board_simple()
        #Main game loop
        while(self.board.get_game_state() == GameState.IN_PROGRESS):
            if self.check_for_valid_moves():
                move_played = self._make_engine_move()
                if move_played != 0:
                    print(f"Engine played {move_encoding.decode_to_string_verbose(move_played)}")
                else:
                    print("No valid moves!")
            elif self.board.get_game_state() != GameState.DRAW:
                if self.board.position.w_to_move:
                    self.board.position.game_state = GameState.B_WINS
                else:
                    self.board.position.game_state = GameState.W_WINS
            self.display_board_simple()
        print(self.board.get_game_state())

    #Helper funtion which handles obtaining input from the player and attempting to update the engine with the move
    def _ask_player_for_move(self)->None:
        valid = False
        while not valid:
            print("Please enter a move:")
            move_string = input()
            move = move_encoding.encode_string(self.board,move_string)
            valid = True
            if move == None:
                valid = False
                print("Incorrect move format! Use notation: '<source> to <dest>")
                continue
            #updates engine's board if valid, returns False if not
            valid = self._make_player_move(move)
            if not valid:
                print("INVALID MOVE, TRY AGAIN")

    #Returns a list of moves valid in the current position
    def get_valid_moves(self)->List[u32]:
        if not self.moves_up_to_date:
            self._update_moves()
        return self.valid_moves
    
    def _update_moves(self)->None:
        self.valid_moves.clear()
        self.valid_moves = self.engine.search.move_generator.generate_moves(self.board)
        self.moves_up_to_date = True

    def _make_engine_move(self)->u32:
        self.engine.display_engine_moves()
        move = self.engine.make_engine_move()
        if move != 0:
            self.board.make_move(move)
        self.valid_moves.clear()
        self.moves_up_to_date = False
        return move

    #Returns False if there are no valid moves in the current position
    def check_for_valid_moves(self)->bool:
        moves = self.engine.search.move_generator.generate_moves(self.board)
        #If no valid moves
        if moves == 0:
            if self.engine.search.move_generator._get_self_in_check(self.board):
                self.board.position.game_state = GameState.B_WINS if self.board.position.w_to_move else GameState.W_WINS
            else:
                self.board.position.game_state = GameState.DRAW
            return False
        return True

    def _make_player_move(self, move_code:u32)->bool:
        #updates the player move code with move details
        corrected_code = self.engine.make_manual_move(move_code)
        if corrected_code != 0:
            self.board.make_move(corrected_code)
            self.valid_moves.clear()
            self.moves_up_to_date = False
        return (corrected_code != 0)

    #Updates the current position to the given FEN string, used for testing
    def load_FEN(self, fen_str:str)->None:
        def _FEN2board_helper(pattern: str, fen: str):
            bit_list = ['0']*64
            for m in [match.start() for match in re.finditer(pattern,fen)]:
                bit_list[m] = '1'
            return np.uint64(int(''.join(bit_list),2))

        fen_components = fen_str.split(" ")

        uniform_position = ""
        for i in fen_components[0]:
            if i.isdigit():
                uniform_position += '0'*int(i)
            elif i.isalpha():
                uniform_position += i

        pos = Position()
        pos.piece_masks[PieceType.PAWN.value] = _FEN2board_helper(r"[Pp]",uniform_position)
        pos.piece_masks[PieceType.ROOK.value] = _FEN2board_helper(r"[Rr]",uniform_position)
        pos.piece_masks[PieceType.BISHOP.value] = _FEN2board_helper(r"[Bb]",uniform_position)
        pos.piece_masks[PieceType.KNIGHT.value] = _FEN2board_helper(r"[Nn]",uniform_position)
        pos.piece_masks[PieceType.QUEEN.value] = _FEN2board_helper(r"[Qq]",uniform_position)
        pos.piece_masks[PieceType.KING.value] = _FEN2board_helper(r"[Kk]",uniform_position)
        pos.color_masks[Color.WHITE.value] = _FEN2board_helper(r"[A-Z]",uniform_position)
        pos.color_masks[Color.BLACK.value] = _FEN2board_helper(r"[a-z]",uniform_position)

        pos.w_to_move = (fen_components[1] == "w")
        pos.w_k_castle = False
        pos.w_q_castle = False
        pos.b_k_castle = False
        pos.b_q_castle = False
        if fen_components[2]  != '-':
            for c in fen_components[2]:
                match c:
                    case "K":
                        pos.w_k_castle = True
                    case "Q":
                        pos.w_q_castle = True
                    case "k":
                        pos.b_k_castle = True
                    case "q":
                        pos.b_q_castle = True
        if fen_components[3] != '-':
            pos.en_passant_target_index = move_encoding.square_str_to_index(fen_components[3])
        pos.half_move_clock = int(fen_components[4])
        pos.full_move_counter = int(fen_components[5])

        self.board.position = pos

    #Prints a human friendly representation of the current board state
    def display_board_simple(self)->None:
        print("_____"*15+"\n")
        print(" BOARD")
        print("_____"*15)
        fen = move_encoding.generate_FEN(self.board)
        print(f"FEN: {fen}\n")
        parts = fen.split(' ')
        rows = parts[0].split('/')
        ranks = ['8','7','6','5','4','3','2','1']
        files = ["A","B","C","D","E","F","G","H"]
        files_label = " "
        for i in range(len(files)):
            files_label += " "*1 + files[i]
        print(files_label)
        print(" "+("------"*3))
        for i in range(len(rows)):
            row_str = f"{ranks[i]}|"
            for c in rows[i]:
                if c.isdigit():
                    for j in range(int(c)):
                        row_str += f'<>'
                else:
                    row_str += f"{self._fen_2_unicode(c)} "
            print(row_str+f"|{ranks[i]}")
        print(" "+("------"*3))
        print(files_label)

    #Used to convert FEN piece characters to the unicode chess pieces
    def _fen_2_unicode(self,char:str)->str:
        uni = {'K':u'\u2654',
               'Q':u'\u2655',
               'R':u'\u2656',
               'B':u'\u2657',
               'N':u'\u2658',
               'P':u'\u2659',
               'k':u'\u265A',
               'q':u'\u265B',
               'r':u'\u265C',
               'b':u'\u265D',
               'n':u'\u265E',
               'p':u'\u265F'}
        return uni[char]