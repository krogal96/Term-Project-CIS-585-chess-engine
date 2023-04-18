#Interface for preparing the model, and formatting data into the correct input format

import numpy as np
import torch

from nn import model

def fen_to_input(fen:str):
    input_vector = []
    fen_parts = fen.split(' ')
    fen = fen_parts[0]
    w_to_move = 1.0 if fen_parts[1] == 'w' else -1.0
    w_k_castle = 1.0 if 'K' in fen_parts[2] else 0.0
    w_q_castle = 1.0 if 'Q' in fen_parts[2] else 0.0
    b_k_castle = 1.0 if 'k' in fen_parts[2] else 0.0
    b_q_castle = 1.0 if 'q' in fen_parts[2] else 0.0
    half_move_clock = int(fen_parts[4])/50.0
    expanded_fen = ""
    input_vector = input_vector + [w_to_move,w_k_castle,w_q_castle,b_k_castle,b_q_castle,half_move_clock]
    for char in fen:
        if char.isdigit():
            expanded_fen += ('0'*int(char))
        elif char.isalpha():
            expanded_fen += char
    for square in expanded_fen:
        color,pawn,knight,bishop,rook,queen,king = (0.0,)*7
        if square == '0':
            #no change
            pass
        elif square.isalpha():
            color = -1.0 if square.islower() else 1.0
            t = square.lower()
            if t == 'p':
                pawn = 1.0
            elif t == 'n':
                knight = 1.0
            elif t == 'b':
                bishop = 1.0
            elif t == 'r':
                rook = 1.0
            elif t == 'q':
                queen = 1.0
            elif t == 'k':
                king = 1.0
        input_vector = input_vector + [color,pawn,knight,bishop,rook,queen,king]
    result = input_vector
    return torch.Tensor(result)

def get_model():
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    with open(r".\nn\chess_eval.pth", 'rb') as f:
        mod = model.EvalNetwork()
        mod.load_state_dict(torch.load(f, map_location=device))
        return mod