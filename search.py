#Contains the code used to search the best move given the current position

from move_generator import MoveGenerator
from evaluator import Evaluator
from board import Board
from numpy import uint32 as u32
from typing import Tuple,List
import copy

class Search():
    def __init__(self) -> None:
        self.move_generator = MoveGenerator()
        self.evaluator = Evaluator()
        self.root_node = Board()
        self.moves_up_to_date = False
        self.move_list = []

    def update_root(self, board:Board):
        self.root_node = copy.deepcopy(board)
        self.moves_up_to_date = False

    def get_new_best_move(self, board:Board, search_depth:int = 1)->Tuple[u32,float]:
        '''searches to the specified depth and returns the next move towards the most favorable line'''
        self.update_root(board)
        self.moves_up_to_date = False
        next_move = u32(0)
        if not self.moves_up_to_date:
            self.generate_move_list(board)
        if len(self.move_list) > 0:
            if board.position.w_to_move:
                next_move = self.move_list[0][0]
            else:
                next_move = self.move_list[-1][0]
        else:
            print("NO VALID MOVES")
        return next_move
    
    def a_b_move_search(self,board:Board,depth:int=3)->u32:
        self.move_list.clear()
        moves = self.move_generator.generate_moves(board)
        for move in moves:
            new_board = board.make_move_copy(move)
            move_score = self.a_b_max(0,0,depth,new_board)
            self.move_list.append((move,move_score))
        self.move_list.sort(reverse=True, key=lambda x: x[1])
        self.moves_up_to_date = True

    def generate_move_list(self, board:Board)->List[Tuple[u32,float]]:
        moves = self.move_generator.generate_moves(board)
        self.move_list.clear()
        for m in moves:
            self.move_list.append((m,self.evaluator.eval_board(board.make_move_copy(m),True)))
        self.move_list.sort(reverse=True, key=lambda x: x[1])
        self.moves_up_to_date = True

    def get_move_list(self, board:Board=None):
        if not self.moves_up_to_date or board != None:
            if board != None:
                self.update_root(board)
            self.generate_move_list(self.root_node)
        return self.move_list

    def a_b_max(self,a:int,b:int,depth_countdown:int,board:Board)->float:
        moves = self.move_generator.generate_moves(board)
        if depth_countdown == 0:
            return self.evaluator.eval_board(board)
        for move in moves:
            new_board = board.make_move_copy(move)
            eval_score = self.a_b_min(a,b,depth_countdown-1,new_board)
            if eval_score >= b:
                return b
            elif eval_score > a:
                a = eval_score
        return a
    
    def a_b_min(self,a:int,b:int,depth_countdown:int,board:Board)->float:
        moves = self.move_generator.generate_moves(board)
        if depth_countdown == 0:
            return self.evaluator.eval_board(board)
        for move in moves:
            new_board = board.make_move_copy(move)
            eval_score = self.a_b_max(a,b,depth_countdown-1,new_board)
            if eval_score <= a:
                return a
            elif eval_score < b:
                b = eval_score
        return b
        

