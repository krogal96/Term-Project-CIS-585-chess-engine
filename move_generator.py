#Contains the core components needed to generate valid moves on the given board position

import sys
import csv
import warnings
import numpy as np
from numpy import uint64 as u64

from constants import Direction as DIR
from constants import Board as BD
import move_encoding
import bb_utils

from board import Board
from position import Position
from chess_enums import Color,PieceType

class MoveGenerator():
    '''Generates all valid moves for a given board'''
    def __init__(self) -> None:
        #Load all of the attack tables from file
        self._generate_basic_attack_tables()
        self._load_slider_attack_tables()
        self._load_blocker_tables()
        self._load_magic_numbers()
        if self._load_magic_tables() == False:
                print("Unable to load magic tables, press enter to generate now...")
                self._generate_magic_tables()

    def get_mask_for_square(self, board:Board, square_index:int)->u64:
        '''Returns the move mask for the piece on the given square.
        
        Used for external move validation.'''
        piece = bb_utils.get_piece_from_square(board.position,square_index)
        occ = board.get_occupied()
        friendly = board.position.color_masks[piece.p_color.value]
        piece_mask = bb_utils.u64_from_index(square_index)
        w_to_move = True if piece.p_color == Color.WHITE else False
        threatened = self._get_threat_mask(board, w_to_move)
        castle_rights = (board.position.w_k_castle,board.position.w_q_castle) if w_to_move else (board.position.b_k_castle,board.position.b_q_castle)
        pinned = u64(0)
        mask = (0,u64(0))
        match piece.p_type:
            case PieceType.EMPTY:
                print("INVALID MOVE, SOURCE SQUARE EMPTY")
                return u64(0)
            case PieceType.PAWN:
                mask  = self._pawn_moves(piece_mask,occ,friendly,pinned,w_to_move)
            case PieceType.BISHOP:
                mask = self._bishop_moves(piece_mask,occ,friendly,pinned)
            case PieceType.KNIGHT:
                mask  = self._knight_moves(piece_mask,occ,friendly,pinned)
            case PieceType.ROOK:
                mask  = self._rook_moves(piece_mask,occ,friendly,pinned)
            case PieceType.QUEEN:
                mask  = self._queen_moves(piece_mask,occ,friendly,pinned)
            case PieceType.KING:
                mask  = self._king_moves(piece_mask,threatened,friendly,occ,w_to_move,castle_rights[0],castle_rights[1])
        return mask[0][1]

    #Generates all encoded valid moves for the given board 
    def generate_moves(self, board:Board):
        '''Generates all encoded valid moves for the given board'''
        w_move = board.position.w_to_move
        move_masks = self._generate_move_masks(board, w_move)
        friendly = move_encoding.Color.WHITE if w_move else move_encoding.Color.BLACK
        move_codes = []
        for i in range(6):
            for mask in move_masks[i]:
                for move in bb_utils.get_piecewise_bits(mask[1]):
                    source_type = move_encoding.PieceType(i+1)
                    source = move_encoding.Piece(friendly,source_type,mask[0])
                    dest = bb_utils.get_piece_from_square(board.position,move)
                    move_type = move_encoding.MoveType.CAPTURE if dest.p_type != move_encoding.PieceType.EMPTY else move_encoding.MoveType.QUIET
                    if source_type == move_encoding.PieceType.PAWN and move_type == move_encoding.MoveType.QUIET:
                        move_type = move_encoding.MoveType.PAWN_MOVE
                    check_type = move_encoding.CheckFlags.NONE
                    special = move_encoding.Special(move_type,check_type)
                    
                    #look for check and checkmate
                    base_move = move_encoding.encode(source,dest,special)
                    result = board.make_move_copy(base_move)
                    enemy_in_check = self._get_self_in_check(result)
                    if enemy_in_check:
                        new_masks = self._generate_move_masks(result,w_move)
                        has_valid_move = False
                        for piece_masks in new_masks:
                            for single_mask in piece_masks:
                                if single_mask[1] != 0:
                                    has_valid_move = True
                                    break
                        if has_valid_move:
                            check_type = move_encoding.CheckFlags.CHECK
                        else:
                            check_type = move_encoding.CheckFlags.CHECKMATE

                    #re-encode the move with new check information
                    special = move_encoding.Special(move_type,check_type)

                    #if self in check after move, don't add this move
                    result_threats = self._get_threat_mask(result,w_move)
                    if not self._calc_check(result,result_threats,w_move):
                        move_codes.append(move_encoding.encode(source,dest,special))
        return move_codes

    def _generate_basic_attack_tables(self):
        self._generate_pawn_attack_tables()
        self._generate_knight_attack_table()
        self._generate_king_attack_table()

    def _load_magic_tables(self):
        try:
            with open("tables\\rook_magic_tables.csv",'r') as f:
                reader = csv.reader(f)
                self.rook_magic_table = [[u64(num) for num in row] for row in reader]
            with open("tables\\bishop_magic_tables.csv",'r') as f:
                reader = csv.reader(f)
                self.bishop_magic_table = [[u64(num) for num in row] for row in reader]

            print("Magic tables loaded successfully.")
        except IOError:
            print("Failed to find magic table files.")

    def _load_slider_attack_tables(self):
        try:
            with open("tables\\rook_attack_table.txt",'r') as f:
                self.rook_attack_table = np.fromstring(f.read(),u64,sep='\n')
            with open("tables\\bishop_attack_table.txt",'r') as f:
                self.bishop_attack_table = np.fromstring(f.read(),u64,sep='\n')
        except IOError:
            print("You need to generate the attack tables before the first run.")
            print("run 'generate_lookup_tables.py', then try again.")
            sys.exit()

    def _load_blocker_tables(self):
        try:
            with open("tables\\rook_blockers_table.txt",'r') as f:
                self.rook_blocker_table = np.fromstring(f.read(),u64,sep='\n')
            with open("tables\\bishop_blockers_table.txt",'r') as f:
                self.bishop_blocker_table = np.fromstring(f.read(),u64,sep='\n')
        except IOError:
            print("You need to generate the blocker tables before the first run.")
            print("run 'generate_lookup_tables.py', then try again.")
            sys.exit()

    #Pawn Attacks
    def w_pawn_attacks_east(self, w_pawns:u64):
        return bb_utils.move(w_pawns,DIR.NE)
    
    def w_pawn_attacks_west(self, w_pawns:u64):
        return bb_utils.move(w_pawns, DIR.NW)
    
    def w_pawn_attacks_any(self, w_pawns:u64):
        return self.w_pawn_attacks_east(w_pawns) | self.w_pawn_attacks_west(w_pawns)
    
    def b_pawn_attacks_east(self, b_pawns:u64):
        return bb_utils.move(b_pawns,DIR.SE)
    
    def b_pawn_attacks_west(self, b_pawns:u64):
        return bb_utils.move(b_pawns, DIR.SW)
    
    def b_pawn_attacks_any(self, b_pawns:u64):
        return self.b_pawn_attacks_east(b_pawns) | self.b_pawn_attacks_west(b_pawns)

    #Pawn Captures
    def w_pawn_can_capture_east(self, w_pawns, b):
        targets = self.w_pawn_attacks_east(w_pawns) & b
        return bb_utils.move(targets, DIR.SW) & w_pawns
    
    def w_pawn_can_capture_west(self, w_pawns, b):
        targets = self.w_pawn_attacks_west(w_pawns) & b
        return bb_utils.move(targets, DIR.SE) & w_pawns
    
    def w_pawn_can_capture_any(self, w_pawns, b):
        return self.w_pawn_can_capture_east(w_pawns,b) | self.w_pawn_can_capture_west(w_pawns,b)
    
    def b_pawn_can_capture_east(self, b_pawns, w):
        targets = self.b_pawn_attacks_east(b_pawns) & w
        return bb_utils.move(targets, DIR.NW) & b_pawns
    
    def b_pawn_can_capture_west(self, b_pawns, w):
        targets = self.b_pawn_attacks_west(b_pawns) & w
        return bb_utils.move(targets, DIR.NE) & b_pawns
    
    def b_pawn_can_capture_any(self, b_pawns, w):
        return self.b_pawn_can_capture_east(b_pawns,w) | self.b_pawn_can_capture_west(b_pawns,w)
    
    #Knight Attacks
    def _knight_attacks(self, knights):
        #Prevents wrapping around sides of board
        not_a = ~BD.FILE_A
        not_ab = ~(BD.FILE_A | BD.FILE_B)
        not_h = ~BD.FILE_H
        not_gh = ~(BD.FILE_H | BD.FILE_G)

        nnw = u64(DIR.NW.value + DIR.N.value)
        nne = u64(DIR.NE.value + DIR.N.value)
        wnw = u64(DIR.W.value + DIR.NW.value)
        ene = u64(DIR.E.value + DIR.NE.value)
        attacks = ((knights << -nnw)&not_h) | ((knights << -nne)&not_a) | ((knights << -wnw)&not_gh) | ((knights << -ene)&not_ab)

        ssw = u64(DIR.SW.value + DIR.S.value)
        sse = u64(DIR.SE.value + DIR.S.value)
        wsw = u64(DIR.W.value + DIR.SW.value)
        ese = u64(DIR.E.value + DIR.SE.value)
        attacks |=  ((knights >> ssw)&not_h) | ((knights >> sse)&not_a) | ((knights >> wsw)&not_gh) | ((knights >> ese)&not_ab)

        return attacks
    
    def _king_attacks(self,king: u64):
        attacks = bb_utils.move(king,DIR.N) | bb_utils.move(king,DIR.NE) | bb_utils.move(king,DIR.E) | bb_utils.move(king,DIR.SE)
        attacks |= bb_utils.move(king,DIR.S) | bb_utils.move(king,DIR.SW) | bb_utils.move(king,DIR.W) | bb_utils.move(king,DIR.NW)
        return attacks
    
    #Sliding pieces
    def _bishop_attacks(self,bishop: u64):
        bishop_index = []
        res = 0
        while res != None:
            res = bb_utils.bitscan_fwd(bishop)
            if res != None:
                bishop_index.append(res)
                bishop -= u64(1)<<u64(res)
        attacks = []
        for b in bishop_index:
            attacks.append(self.bishop_attack_table[b])

        return attacks

    def _rook_attacks(self,rook: u64):
        rook_index = []
        res = 0
        while res != None:
            res = bb_utils.bitscan_fwd(rook)
            if res != None:
                rook_index.append(res)
                rook -= u64(1)<<u64(res)
        attacks = []
        for r in rook_index:
            attacks.append(self.rook_attack_table[r])

        return attacks

    def _queen_attacks(self,queen: u64):
        queen_index = []
        res = 0
        while res != None:
            res = bb_utils.bitscan_fwd(queen)
            if res != None:
                queen_index.append(res)
                queen -= u64(1)<<u64(res)
        attacks = []
        for q in queen_index:
            attacks.append(self.bishop_attack_table[q] | self.rook_attack_table[q])

        return attacks
    
    def _load_magic_numbers(self):
        try:
            with open("tables\\rook_magic_numbers.txt",'r') as f:
                self.rook_magics = np.fromstring(f.read(),u64,sep='\n')
            with open("tables\\bishop_magic_numbers.txt",'r') as f:
                self.bishop_magics = np.fromstring(f.read(),u64,sep='\n')
            
        except IOError:
            print("You're missing the magic numbers, please generate some and try again")
            sys.exit()

    def _generate_pawn_attack_tables(self):
        self.w_pawn_attack_table = np.zeros(64,u64)
        self.b_pawn_attack_table = np.zeros(64,u64)
        for square in range(64):
            sq_mask = bb_utils.u64_from_index(square)
            self.w_pawn_attack_table[square] = self.w_pawn_attacks_any(sq_mask)
            self.b_pawn_attack_table[square] = self.b_pawn_attacks_any(sq_mask)

    def _generate_knight_attack_table(self):
        self.knight_attack_table = np.zeros(64,u64)
        for square in range(64):
            sq_mask = bb_utils.u64_from_index(square)
            self.knight_attack_table[square] = self._knight_attacks(sq_mask)

    def _generate_king_attack_table(self):
        self.king_attack_table = np.zeros(64,u64)
        for square in range(64):
            sq_mask = bb_utils.u64_from_index(square)
            self.king_attack_table[square] = self._king_attacks(sq_mask)

    def _generate_rook_magic_table(self):
        print("Generating rook magic table...")
        for square in range(64):
            mask = self.rook_blocker_table[square]
            mask_pop_count = bb_utils.pop_count(mask)
            for i in range(1 << mask_pop_count):
                #start filling the table with calculated moves
                combo_mask = bb_utils.generate_blocker_combo_from_index(i,mask)
                #manually calculate rook moves for this situation
                moves = bb_utils.calc_rook_moves(square,combo_mask)
                #obtain the magic index
                magic_index = self._calc_magic_index(combo_mask,self.rook_magics[square],mask_pop_count)
                #fill the appropriate table slot with the valid moves
                if self.rook_magic_table[square][magic_index] == 0:
                    self.rook_magic_table[square][magic_index] = moves
                else:
                    print("SOMETHING WENT WRONG, INVALID MAGIC TABLE")

    def _generate_bishop_magic_table(self):
        print("Generating bishop magic table...")
        for square in range(64):
            mask = self.bishop_blocker_table[square]
            mask_pop_count = bb_utils.pop_count(mask)
            for i in range(1 << mask_pop_count):
                #start filling the table with calculated moves
                combo_mask = bb_utils.generate_blocker_combo_from_index(i,mask)
                #manually calculate bishop moves for this situation
                moves = bb_utils.calc_bishop_moves(square,combo_mask)
                #obtain the magic index
                magic_index = self._calc_magic_index(combo_mask,self.bishop_magics[square],mask_pop_count)
                #fill the appropriate table slot with the valid moves
                if self.bishop_magic_table[square][magic_index] == 0:
                    self.bishop_magic_table[square][magic_index] = moves
                else:
                    print("SOMETHING WENT WRONG, INVALID MAGIC TABLE")

    def _generate_magic_tables(self):
        #creates two arrays to hold the tables, rook tables need 4096 combos, bishops need 512
        #one spot for every possible combination of blocker pieces relevant to the given square
        self._load_magic_numbers()
        self.rook_magic_table = np.zeros((64,4096),u64)
        self.bishop_magic_table = np.zeros((64,4096),u64)

        self._generate_rook_magic_table()
        self._generate_bishop_magic_table()
        
        self._save_magic_tables_to_file()
        print("Done!")

    #Performs the transformation on the blockermask to get the magic index
    def _calc_magic_index(self, mask: u64, magic_number: u64, blocker_count: int):
        #overflow is expected when calculating hash values
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore',r'overflow encountered in ulonglong_scalars')
            result = mask * magic_number
        shift = u64(64 - blocker_count)
        return result >> shift

    def _save_magic_tables_to_file(self):
        with open("tables\\rook_magic_tables.csv",'w+',newline='') as f:
            magic_writer = csv.writer(f)
            for i, list in enumerate(self.rook_magic_table):
                line = [num for j,num in enumerate(self.rook_magic_table[i])]
                magic_writer.writerow(line)
        with open("tables\\bishop_magic_tables.csv",'w+',newline='') as f:
            magic_writer = csv.writer(f)
            for i, list in enumerate(self.bishop_magic_table):
                line = [num for j,num in enumerate(self.bishop_magic_table[i])]
                magic_writer.writerow(line)

    def _lookup_rook_moves(self, occupied: u64, square_index):
        magic = self.rook_magics[square_index]
        mask = self.rook_blocker_table[square_index]
        sub_mask = mask&occupied
        magic_index = self._calc_magic_index(sub_mask,magic,bb_utils.pop_count(mask))
        return self.rook_magic_table[square_index][magic_index]
    
    def _lookup_bishop_moves(self, occupied: u64, square_index):
        magic = self.bishop_magics[square_index]
        mask = self.bishop_blocker_table[square_index]
        sub_mask = mask&occupied
        magic_index = self._calc_magic_index(sub_mask,magic,bb_utils.pop_count(mask))
        return self.bishop_magic_table[square_index][magic_index]

    def _slider_moves(self, piece_mask: u64, occ_mask: u64,friendly_mask: u64, isRook: bool):
        #find all the rook index for the given side
        pieces = bb_utils.get_piecewise_bits(piece_mask)
        #for each rook, lookup the valid moves
        move_list = []
        for piece_index in pieces:
            #filter out friendly pieces
            moves = self._lookup_rook_moves(occ_mask,piece_index) if isRook else self._lookup_bishop_moves(occ_mask,piece_index)
            move_list.append((piece_index,moves&~friendly_mask))
        #return list of movesets
        return move_list

    def _queen_moves(self, queen_mask: u64, occ_mask: u64, friendly_mask: u64, pinned:u64):
        #find all the queen index for the given side
        queens = bb_utils.get_piecewise_bits(queen_mask)
        #for each queen, lookup the valid moves
        move_list = []
        for queen_index in queens:
            #Combine rook moves and bishop moves
            queen_moves = (self._lookup_rook_moves(occ_mask,queen_index)|self._lookup_bishop_moves(occ_mask,queen_index))&~friendly_mask
            move_list.append((queen_index,queen_moves))
        #return list of movesets
        return move_list
    
    #returns bitboard of all pieces that can be 'seen' by the piece
    def _get_attack_targets(self, enemy_mask: u64, moves_mask: u64):
        captures = moves_mask & enemy_mask
        return captures
    
    #finds captures, removes them, then recalculates attacks and returns only squares seen past the blockers
    def _x_ray_attacks(self, square_index, occ_mask: u64, blocker_mask: u64, isRook: bool):
        moves = self._lookup_rook_moves(occ_mask,square_index) if isRook else self._lookup_bishop_moves(occ_mask,square_index)
        targets = self._get_attack_targets(blocker_mask, moves)
        new_moves = self._lookup_rook_moves(occ_mask^targets, square_index) if isRook else self._lookup_bishop_moves(occ_mask^targets, square_index)
        return moves ^ new_moves
    
    #returns a mask of valid moves for each type and piece for the given side
    def _generate_move_masks(self,board: Board, w_to_move: bool):
        move_list = []
        occupied = board.position.color_masks[Color.WHITE.value]|board.position.color_masks[Color.BLACK.value]
        friendly = board.position.color_masks[Color.WHITE.value] if w_to_move else board.position.color_masks[Color.BLACK.value]
        castle_rights = (board.position.w_k_castle,board.position.w_q_castle) if w_to_move else (board.position.b_k_castle,board.position.b_q_castle)
        #TODO
        pinned = u64(0)
        #all squares attacked by enemy pieces(including protected pieces)
        threat_mask = self._get_threat_mask(board,w_to_move)
        #for piece, each is responsible for checking if move is legal
        move_list.append(self._pawn_moves(board.position.piece_masks[PieceType.PAWN.value]&friendly,occupied,friendly,pinned,w_to_move))
        move_list.append(self._knight_moves(board.position.piece_masks[PieceType.KNIGHT.value]&friendly,occupied,friendly,pinned))
        move_list.append(self._bishop_moves(board.position.piece_masks[PieceType.BISHOP.value]&friendly,occupied,friendly,pinned))
        move_list.append(self._rook_moves(board.position.piece_masks[PieceType.ROOK.value]&friendly,occupied,friendly,pinned))
        move_list.append(self._queen_moves(board.position.piece_masks[PieceType.QUEEN.value]&friendly,occupied,friendly,pinned))
        move_list.append(self._king_moves(board.position.piece_masks[PieceType.KING.value]&friendly,threat_mask,friendly,occupied,w_to_move,castle_rights[0],castle_rights[1]))

        return move_list

    #returns one mask of all squares the enemy can attack currently
    def _get_threat_mask(self,board:Board,w_to_move:bool)->u64:
        occupied = board.position.color_masks[Color.WHITE.value]|board.position.color_masks[Color.BLACK.value]
        friendly = board.position.color_masks[Color.BLACK.value] if w_to_move else board.position.color_masks[Color.WHITE.value]
        pinned = u64(0)
        threat_mask = u64(0)
        moves = [(0,u64(0))]
        moves = moves + self._pawn_capture_mask(board.position.piece_masks[PieceType.PAWN.value]&friendly,occupied,friendly,pinned,(not w_to_move))
        moves = moves + self._knight_moves(board.position.piece_masks[PieceType.KNIGHT.value]&friendly,occupied,friendly,pinned)
        moves = moves + self._bishop_moves(board.position.piece_masks[PieceType.BISHOP.value]&friendly,occupied,friendly,pinned)
        moves = moves + self._rook_moves(board.position.piece_masks[PieceType.ROOK.value]&friendly,occupied,friendly,pinned)
        moves = moves + self._queen_moves(board.position.piece_masks[PieceType.QUEEN.value]&friendly,occupied,friendly,pinned)
        moves = moves + self._king_attack_mask(board.position.piece_masks[PieceType.KING.value]&friendly,threat_mask,friendly)
        for mask in moves:
            threat_mask |= mask[1]
        return threat_mask

    #moves and captures
    def _pawn_moves(self, pawns: u64, occ: u64, friendly: u64, pinned: u64, w_to_move: bool, en_passant_target = 64):
        if pinned == 0:
            return self._calc_each_pawn_moves(pawns,occ,friendly,w_to_move,en_passant_target)

    def _pawn_capture_mask(self, pawns:u64, occ:u64, friendly:u64, pinned:u64, w_to_move:bool):
        pawn_index = bb_utils.get_piecewise_bits(pawns)
        move_set = []
        for index in pawn_index:
            moves = u64(0)
            moves |= self._pawn_captures(index,occ^friendly,w_to_move)
            move_set.append((index,moves))
        return move_set
    
    def _knight_moves(self, knights:u64, occ:u64, friendly:u64, pinned:u64):
        moves = []
        if pinned == 0:
            for piece in bb_utils.get_piecewise_bits(knights):
                moves.append((piece,self.knight_attack_table[piece]&~friendly))
        return moves

    def _bishop_moves(self, bishops: u64, occ: u64, friendly: u64, pinned: u64):
        if pinned == 0:
           return self._slider_moves(bishops,occ,friendly,False)

    def _rook_moves(self, rooks: u64, occ: u64, friendly: u64, pinned: u64):
        if pinned == 0:
            return self._slider_moves(rooks,occ,friendly,True)

    def _king_moves(self, king: u64, threatened:u64, friendly: u64, occ:u64, w_to_move:bool, king_castle:bool, queen_castle:bool):
        #return kings moves that are not occupied by friendly pieces, and that are not squares under attack

        castle_mask = u64(0)
        if king_castle:
            # white to move, path not occupied, and not under threat
            if w_to_move:
                if occ&BD.W_KING_CASTLE_MASK == 0:
                    if (BD.W_KING_CASTLE_MASK|king)&threatened == 0:
                        castle_mask |= BD.W_KING_CASTLE_SQUARE
            elif not w_to_move and occ&BD.B_KING_CASTLE_MASK == 0 and (BD.B_KING_CASTLE_MASK|king)&threatened == 0:
                castle_mask |= BD.B_KING_CASTLE_SQUARE
        if queen_castle:
            if w_to_move and occ&BD.W_QUEEN_CASTLE_MASK == 0 and (BD.W_QUEEN_CASTLE_MASK|king)&threatened == 0:
                castle_mask |= BD.W_QUEEN_CASTLE_SQUARE
            elif not w_to_move and occ&BD.B_QUEEN_CASTLE_MASK == 0 and (BD.B_QUEEN_CASTLE_MASK|king)&threatened == 0:
                castle_mask |= BD.B_QUEEN_CASTLE_SQUARE

        moves_list = self._king_attack_mask(king,threatened,friendly)
        moves_list = [(move[0], move[1]|castle_mask) for move in moves_list]
        return moves_list
    
    def _king_attack_mask(self, king: u64, threatened:u64, friendly: u64):
        moves_list = []
        index = bb_utils.bitscan_fwd(king)
        moves = self.king_attack_table[index]
        safe_moves = moves & ~(friendly|threatened)
        moves_list.append((index,safe_moves))
        return moves_list

    def _calc_each_pawn_moves(self, pawns:u64, occ:u64, friendly:u64, w_to_move:bool, ep_target_square = 64):
        pawn_index = bb_utils.get_piecewise_bits(pawns)
        move_set = []
        for index in pawn_index:
            moves = u64(0)
            moves |= self._pawn_single_push(index,occ,w_to_move)
            moves |= self._pawn_double_push(index,occ,w_to_move)
            moves |= self._pawn_captures(index,occ^friendly,w_to_move)
            if ep_target_square != 64:
                moves |= self._pawn_en_passant()
            move_set.append((index,moves))
        return move_set
    
    def _pawn_en_passant(self,square_index:int,occ:u64,w_to_move:bool, ep_target_index:int)->u64:
        w_valid = (w_to_move and int(square_index/8) == 4 and int(ep_target_index/8) == 5)
        b_valid = (not w_to_move and int(square_index/8) == 3 and int(ep_target_index/8) == 2)
        captures = u64(0)
        if w_valid or b_valid:
            piece = bb_utils.u64_from_index(square_index)
            directions = [DIR.NE,DIR.NW] if w_to_move else [DIR.SE, DIR.SW]
            captures = bb_utils.move(piece,directions[0]) | bb_utils.move(piece,directions[1])
        ep_mask = bb_utils.u64_from_index(ep_target_index)
        return captures & ep_mask

    def _pawn_captures(self, square_index:int, enemy:u64, w_to_move:bool)->u64:
        piece = bb_utils.u64_from_index(square_index)
        directions = [DIR.NE,DIR.NW] if w_to_move else [DIR.SE, DIR.SW]
        captures = bb_utils.move(piece,directions[0]) | bb_utils.move(piece,directions[1])
        return captures&enemy

    def _pawn_single_push(self, square_index:int, occ:u64, w_to_move:bool)->u64:
        piece = bb_utils.u64_from_index(square_index)
        direction = DIR.N if w_to_move else DIR.S
        return bb_utils.move(piece,direction)&~occ
    
    def _pawn_double_push(self, square_index:int, occ:u64, w_to_move:bool)->u64:
        piece = bb_utils.u64_from_index(square_index)
        starting_mask = BD.RANK_2 if w_to_move else BD.RANK_7
        if starting_mask & piece == 0:
            return u64(0)
        else:
            result = self._pawn_single_push(square_index,occ,w_to_move)
            new_index = bb_utils.bitscan_fwd(result)
            if new_index != None:
                return self._pawn_single_push(new_index,occ,w_to_move)
            else:
                return u64(0)

    #tells you if the given square is under attack by the given threat mask
    def _is_square_attacked(self,square_index:int,threat_mask:Position)->bool:
        return bb_utils.u64_from_index(square_index) & threat_mask != 0

    #tells you if the given side is in check currently
    def _calc_check(self,board:Board, threat_mask:u64, w_to_move:bool):
        king_mask = board.position.color_masks[Color.WHITE.value] if w_to_move else board.position.color_masks[Color.BLACK.value]
        king_mask &= board.position.piece_masks[PieceType.KING.value]
        king_square = bb_utils.bitscan_fwd(king_mask)
        return self._is_square_attacked(king_square,threat_mask)
    
    def _get_self_in_check(self,board:Board)->bool:
        '''Tells you if the current side is in check.'''
        threat_mask = self._get_threat_mask(board,board.position.w_to_move)
        return self._calc_check(board,threat_mask,board.position.w_to_move)

    #returns friendly pieces that are pinned to the friendly king
    def _absolute_pins(self, king_square_index: int, occ: u64, friendly: u64, enemy_rook_queen: u64, enemy_bishop_queen:u64)->u64:
        '''Returns friendly pieces that are pinned to the friendly king'''
        pinned = u64(0)
        attackers = self._x_ray_attacks(king_square_index,occ,friendly,True) & enemy_rook_queen
        attacker_squares = bb_utils.get_piecewise_bits(attackers)
        for square in attacker_squares:
            pinned |= self._lookup_rook_moves(occ,king_square_index) & self._lookup_rook_moves(occ,square) & friendly
        attackers = self._x_ray_attacks(king_square_index,occ,friendly,False) & enemy_bishop_queen
        attacker_squares = bb_utils.get_piecewise_bits(attackers)
        for square in attacker_squares:
            pinned |= self._lookup_bishop_moves(occ,king_square_index) & self._lookup_bishop_moves(occ,square) & friendly
        return pinned
