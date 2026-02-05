# shapes.py

# Definitions of block shapes for Block Blast
# Represented as list of coordinates [(r, c), ...] relative to top-left (0,0)
# or as 2D binary grids. Using 2D grids is often easier for convolution/checking.

SHAPES = {}

# --- Traditional Tetris Pieces (7) ---

# I-piece (4 blocks straight)
SHAPES['I4_H'] = [[1, 1, 1, 1]]
SHAPES['I4_V'] = [[1], 
                  [1], 
                  [1], 
                  [1]]

# O-piece (2x2 square)
SHAPES['O'] = [[1, 1], 
               [1, 1]]

# T-piece
SHAPES['T_UP']    = [[0, 1, 0], 
                     [1, 1, 1]]
SHAPES['T_DOWN']  = [[1, 1, 1], 
                     [0, 1, 0]]
SHAPES['T_LEFT']  = [[0, 1], 
                     [1, 1], 
                     [0, 1]]
SHAPES['T_RIGHT'] = [[1, 0], 
                     [1, 1], 
                     [1, 0]]

# S-piece
SHAPES['S_H'] = [[0, 1, 1], 
                 [1, 1, 0]]
SHAPES['S_V'] = [[1, 0], 
                 [1, 1], 
                 [0, 1]]

# Z-piece
SHAPES['Z_H'] = [[1, 1, 0], 
                 [0, 1, 1]]
SHAPES['Z_V'] = [[0, 1], 
                 [1, 1], 
                 [1, 0]]

# J-piece
SHAPES['J_UP']    = [[1, 0, 0], 
                     [1, 1, 1]]
SHAPES['J_DOWN']  = [[1, 1, 1], 
                     [0, 0, 1]]
SHAPES['J_LEFT']  = [[0, 1], 
                     [0, 1], 
                     [1, 1]]
SHAPES['J_RIGHT'] = [[1, 1], 
                     [1, 0], 
                     [1, 0]]

# L-piece
SHAPES['L_UP']    = [[0, 0, 1], 
                     [1, 1, 1]]
SHAPES['L_DOWN']  = [[1, 1, 1], 
                     [1, 0, 0]]
SHAPES['L_LEFT']  = [[1, 1], 
                     [0, 1], 
                     [0, 1]]
SHAPES['L_RIGHT'] = [[1, 0], 
                     [1, 0], 
                     [1, 1]]

# --- Block Blast Variations (12+ types) ---

# 1. Single Block (1x1)
SHAPES['1x1'] = [[1]]

# 2. Dominoes
SHAPES['1x2'] = [[1, 1]]
SHAPES['2x1'] = [[1], 
                 [1]]

# 3. Triominoes (Straight)
SHAPES['1x3'] = [[1, 1, 1]]
SHAPES['3x1'] = [[1], 
                 [1], 
                 [1]]

# 4. Triominoes (Corner/L-small)
SHAPES['Corner_Small_TL'] = [[1, 1], 
                             [1, 0]] # Top-Left filled
SHAPES['Corner_Small_TR'] = [[1, 1], 
                             [0, 1]]
SHAPES['Corner_Small_BL'] = [[1, 0], 
                             [1, 1]]
SHAPES['Corner_Small_BR'] = [[0, 1], 
                             [1, 1]]

# 5. Rectangles (Larger)
SHAPES['1x4'] = [[1, 1, 1, 1]] # Same as I4_H
# (Assuming 1x4 is distinct in game logic or just visual, keeping I4 definitions covers it)
# 1x5? Block Blast sometimes has 5. User mentioned 1x3, 1x4, 2x3.

SHAPES['2x3_H'] = [[1, 1, 1], 
                   [1, 1, 1]]
SHAPES['2x3_V'] = [[1, 1], 
                   [1, 1], 
                   [1, 1]]

SHAPES['2x2'] = [[1, 1], [1, 1]] # Same as O

# NEW 1x5 Blocks
SHAPES['1x5'] = [[1, 1, 1, 1, 1]]
SHAPES['5x1'] = [[1], 
                 [1], 
                 [1], 
                 [1], 
                 [1]]

SHAPES['3x3'] = [[1, 1, 1],
                 [1, 1, 1],
                 [1, 1, 1]]

# 6. Large Corners (3x3 bounding box, 5 blocks)
SHAPES['Corner_Large_TL'] = [[1, 1, 1], 
                             [1, 0, 0], 
                             [1, 0, 0]]
SHAPES['Corner_Large_TR'] = [[1, 1, 1], 
                             [0, 0, 1], 
                             [0, 0, 1]]
SHAPES['Corner_Large_BL'] = [[1, 0, 0], 
                             [1, 0, 0], 
                             [1, 1, 1]]
SHAPES['Corner_Large_BR'] = [[0, 0, 1], 
                             [0, 0, 1], 
                             [1, 1, 1]]

# 7. Diagonal 2 (Step)
SHAPES['Diag2_R'] = [[0, 1], 
                     [1, 0]]
SHAPES['Diag2_L'] = [[1, 0], 
                     [0, 1]]

# 8. Diagonal 3
SHAPES['Diag3_R'] = [[0, 0, 1], 
                     [0, 1, 0], 
                     [1, 0, 0]]
SHAPES['Diag3_L'] = [[1, 0, 0], 
                     [0, 1, 0], 
                     [0, 0, 1]]

# 9. U-Shapes (sometimes present, check if standard Block Blast)
# User mentioned "Modified T-pieces with extended arms"
# Maybe a T with longer stem?
# Let's add 3x3 T
SHAPES['T_Large_UP'] = [[0, 1, 0], 
                        [0, 1, 0], 
                        [1, 1, 1]]
SHAPES['T_Large_DOWN'] = [[1, 1, 1], 
                          [0, 1, 0], 
                          [0, 1, 0]]
SHAPES['T_Large_LEFT'] = [[0, 0, 1], 
                          [1, 1, 1], 
                          [0, 0, 1]]
SHAPES['T_Large_RIGHT'] = [[1, 0, 0], 
                           [1, 1, 1], 
                           [1, 0, 0]]

# Helper to categorize shapes for the UI
SHAPE_CATEGORIES = {
    "Lines": ["1x2", "2x1", "1x3", "3x1", "I4_H", "I4_V", "1x5", "5x1"],
    "Squares & Rectangles": ["1x1", "O", "2x3_H", "2x3_V", "3x3"],
    "Corners": [
        "Corner_Small_TL", "Corner_Small_TR", "Corner_Small_BL", "Corner_Small_BR",
        "Corner_Large_TL", "Corner_Large_TR", "Corner_Large_BL", "Corner_Large_BR"
    ],
    "T-Shapes": [
        "T_UP", "T_DOWN", "T_LEFT", "T_RIGHT",
        "T_Large_UP", "T_Large_DOWN", "T_Large_LEFT", "T_Large_RIGHT"
    ],
    "L & J Shapes": [
        "L_UP", "L_DOWN", "L_LEFT", "L_RIGHT",
        "J_UP", "J_DOWN", "J_LEFT", "J_RIGHT"
    ],
    "Z, S & Diagonals": [
        "S_H", "S_V", "Z_H", "Z_V",
        "Diag2_R", "Diag2_L", "Diag3_R", "Diag3_L"
    ]
}