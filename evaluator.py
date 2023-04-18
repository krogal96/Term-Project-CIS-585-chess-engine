#Evaluates the given board position, contains a static material evaluator or the evaluation Neural Network

from board import Board
from chess_enums import *
import bb_utils
import random
from nn import data_prep
import move_encoding

class Evaluator():
    def __init__(self) -> None:
        self.rand = random.Random()
        #Neural Network Model
        self.model = data_prep.get_model()

    #Either returns the material evaluation, or inputs the board state into the evaluation network to and returns the result
    #Neural network result is the range -10 to +10, shifted to be non-negative, then compressed to between 0 and 1
    #To get point evaluation, multiply the result by 20, then subtract 10.
    def eval_board(self, board:Board, use_nn:bool = False):
        eval = 0.0
        if not use_nn:
            eval += self.static_material_eval(board)
        else:
            self.model.eval()
            eval = self.model(data_prep.fen_to_input(move_encoding.generate_FEN(board)))[0]
            eval = (eval*20) - 10
        return eval
    
    #Simple evaluation by summing piece values
    def static_material_eval(self, board:Board)->float:
        w_sum = 0.0
        b_sum = 0.0
        point_value = {PieceType.PAWN.value:1.0,PieceType.BISHOP.value:3.0,PieceType.KNIGHT.value:3.0,
                       PieceType.ROOK.value:5.0,PieceType.QUEEN.value:9.0,PieceType.KING.value:100.0}
        for key in point_value.keys():
            mask = board.position.piece_masks[key]
            w_mask = mask & board.position.color_masks[Color.WHITE.value]
            b_mask = mask & board.position.color_masks[Color.BLACK.value]
            w_sum += point_value[key] * bb_utils.pop_count(w_mask)
            b_sum += point_value[key] * bb_utils.pop_count(b_mask)
        return w_sum - b_sum
