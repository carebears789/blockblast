import numpy as np
import copy

class BlockBlastSolver:
    def __init__(self):
        self.rows = 8
        self.cols = 8

    def solve(self, initial_grid, pieces):
        """
        Finds the best move sequence for the given pieces.
        pieces: list of shape names (keys from SHAPES) or shape matrices.
        Returns:
            best_score: float
            best_sequence: list of tuples (piece_index, r, c)
        """
        # pieces argument might be just names, we need the actual matrices.
        # But wait, user passes 'pieces' which are the definitions. 
        # Let's assume input is a list of shape objects (lists of lists) or dictionaries.
        # For simplicity in recursion, let's work with indices of the pieces list.
        
        # We need to try all permutations because order matters in Block Blast 
        # (clearing lines opens space for next piece).
        
        best_score = -float('inf')
        best_sequence = []
        
        # We need to track which pieces from the input list are used.
        # indices = [0, 1, 2] usually.
        indices = list(range(len(pieces)))
        
        import itertools
        permutations = list(itertools.permutations(indices))
        
        for p_order in permutations:
            # p_order is a tuple like (0, 2, 1) representing the index in original 'pieces' list
            ordered_pieces = [pieces[i] for i in p_order]
            
            score, moves = self._solve_recursive(initial_grid.copy(), ordered_pieces, [], 0)
            
            if score > best_score:
                best_score = score
                # Reconstruct the sequence with original indices
                # 'moves' is list of (r, c).
                # We need to map back to (original_index, r, c)
                final_seq = []
                for i, move in enumerate(moves):
                    original_idx = p_order[i]
                    final_seq.append((original_idx, move[0], move[1]))
                best_sequence = final_seq

        return best_score, best_sequence

    def _solve_recursive(self, grid, remaining_pieces, current_moves, current_score):
        if not remaining_pieces:
            # All pieces placed successfully.
            return current_score + self._evaluate_board(grid), current_moves

        piece = remaining_pieces[0]
        
        # Try all positions
        best_local_score = -float('inf')
        best_local_moves = []
        
        possible_moves = self._get_valid_moves(grid, piece)
        
        if not possible_moves:
            # Game Over path
            return -9999, current_moves # Heavy penalty for dying
            
        for r, c in possible_moves:
            # Simulate placement
            new_grid, points = self._place_and_clear(grid, piece, r, c)
            
            # Recurse
            # Add placement points to score
            new_score = current_score + points
            
            final_score, result_moves = self._solve_recursive(new_grid, remaining_pieces[1:], current_moves + [(r, c)], new_score)
            
            if final_score > best_local_score:
                best_local_score = final_score
                best_local_moves = result_moves
                
        return best_local_score, best_local_moves

    def _get_valid_moves(self, grid, piece):
        """Returns list of (r, c) top-left coordinates where piece fits."""
        p_rows = len(piece)
        p_cols = len(piece[0])
        valid_moves = []
        
        for r in range(self.rows - p_rows + 1):
            for c in range(self.cols - p_cols + 1):
                if self._check_fit(grid, piece, r, c):
                    valid_moves.append((r, c))
        return valid_moves

    def _check_fit(self, grid, piece, r, c):
        for pr in range(len(piece)):
            for pc in range(len(piece[0])):
                if piece[pr][pc] == 1 and grid[r + pr][c + pc] == 1:
                    return False
        return True

    def _place_and_clear(self, grid, piece, r, c):
        """Places piece, clears lines, returns new_grid and score gained."""
        temp_grid = grid.copy()
        
        # Place
        for pr in range(len(piece)):
            for pc in range(len(piece[0])):
                if piece[pr][pc] == 1:
                    temp_grid[r + pr][c + pc] = 1
        
        # Check clears
        rows_to_clear = []
        cols_to_clear = []
        
        for i in range(self.rows):
            if np.all(temp_grid[i, :] == 1):
                rows_to_clear.append(i)
                
        for j in range(self.cols):
            if np.all(temp_grid[:, j] == 1):
                cols_to_clear.append(j)
        
        lines_cleared = len(rows_to_clear) + len(cols_to_clear)
        
        # Clear them
        for row in rows_to_clear:
            temp_grid[row, :] = 0
        for col in cols_to_clear:
            temp_grid[:, col] = 0
            
        # Scoring logic
        # 10 points per line, bonus for multiple lines (combo)
        score = 0
        if lines_cleared > 0:
            score = 10 * lines_cleared * lines_cleared # Quadratic bonus
            
        # Small points for placing blocks (encourages using larger blocks if no clear?)
        # Actually in Block Blast, survival is key, but filling space without clearing is risky.
        # Let's just track clearing score for now.
        
        return temp_grid, score

    def _evaluate_board(self, grid):
        """
        Heuristic evaluation of the final board state.
        Higher is better.
        """
        # 1. Count holes (empty spots inaccessible or surrounded) - Bad
        # 2. Count occupied cells - Generally Bad (we want space)
        # 3. Max contiguous free space - Good
        
        occupied_count = np.sum(grid)
        
        # Simple heuristic: less occupied is better
        score = -occupied_count
        
        # Penalty for 'holes' (0s surrounded by 1s)
        # Simplified: checking for fragmentation
        # ... (Advanced logic could go here)
        
        return score
