import os
import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify, url_for
import time

# Local modules
import capture
import image_processing
from shapes import SHAPES, SHAPE_CATEGORIES
from solver_logic import BlockBlastSolver

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Global State
CURRENT_GRID_STATE = np.zeros((8, 8), dtype=int)
CURRENT_IMG_PATH = "static/grid_capture.jpg"

@app.route('/')
def index():
    return render_template('index.html', categories=SHAPE_CATEGORIES, all_shapes=SHAPES)

@app.route('/capture', methods=['POST'])
def do_capture():
    global CURRENT_GRID_STATE
    try:
        raw_img = capture.get_screen()
        if raw_img is None:
            return jsonify({"status": "error", "message": "Failed to capture image. Check ADB connection."})
        
        state, processed_img = image_processing.process_grid(raw_img)
        CURRENT_GRID_STATE = state
        
        # Save image
        cv2.imwrite(CURRENT_IMG_PATH, processed_img)
        
        # Return the grid state and a timestamp to force image reload
        return jsonify({
            "status": "success",
            "grid": state.tolist(),
            "image_url": f"{CURRENT_IMG_PATH}?t={int(time.time())}"
        })
    except Exception as e:
        print(f"Capture Error: {e}")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/update_grid', methods=['POST'])
def update_grid():
    global CURRENT_GRID_STATE
    data = request.json
    # Expecting {"r": 0, "c": 0, "val": 1}
    r = data.get('r')
    c = data.get('c')
    val = data.get('val')
    
    if r is not None and c is not None:
        CURRENT_GRID_STATE[r][c] = val
        return jsonify({"status": "success"})
    return jsonify({"status": "error"})

@app.route('/invert_grid', methods=['POST'])
def invert_grid():
    global CURRENT_GRID_STATE
    # Flip 0 to 1 and 1 to 0
    CURRENT_GRID_STATE = 1 - CURRENT_GRID_STATE
    return jsonify({"status": "success", "grid": CURRENT_GRID_STATE.tolist()})

@app.route('/solve', methods=['POST'])
def solve():
    data = request.json
    # Expecting list of shape names ["T_UP", "O", ...]
    selected_shapes = data.get('shapes', [])
    
    active_pieces = []
    indices = []
    
    for i, name in enumerate(selected_shapes):
        if name and name in SHAPES:
            active_pieces.append(SHAPES[name])
            indices.append(i)
            
    if not active_pieces:
        return jsonify({"status": "error", "message": "No valid pieces selected"})
        
    solver = BlockBlastSolver()
    try:
        score, moves = solver.solve(CURRENT_GRID_STATE, active_pieces)
    except Exception as e:
        print(f"Solver Error: {e}")
        return jsonify({"status": "error", "message": f"Solver failed: {str(e)}"})
    
    if score <= -9000:
        return jsonify({"status": "fail", "message": "No solution found!"})
        
    # moves is [(local_idx, r, c)]
    # map back to original indices
    final_moves = []
    for (local_idx, r, c) in moves:
        original_idx = indices[local_idx]
        final_moves.append({
            "slot_index": int(original_idx),
            "shape": selected_shapes[original_idx],
            "r": int(r),
            "c": int(c),
            "matrix": SHAPES[selected_shapes[original_idx]]
        })
        
    return jsonify({
        "status": "success",
        "score": int(score),
        "moves": final_moves
    })

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True)