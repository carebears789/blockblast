import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import numpy as np
import threading
import base64

# Local modules
import capture
import image_processing
from shapes import SHAPES, SHAPE_CATEGORIES, identify_shape
from solver_logic import BlockBlastSolver

class BlockBlastApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Block Blast AI Assistant")
        self.root.geometry("1100x700")
        
        # State
        self.current_grid_image = None # The visual image
        self.grid_state = np.zeros((8, 8), dtype=int) # The logical 0/1 grid
        self.selected_shapes = [None, None, None] # The 3 shapes in hand
        self.active_slot_index = 0
        self.solution_moves = None
        
        # Setup UI
        self._setup_ui()
        
    def _setup_ui(self):
        # Top Bar
        top_frame = tk.Frame(self.root, pady=10)
        top_frame.pack(fill=tk.X)
        
        btn_capture = ttk.Button(top_frame, text="📸 Capture Grid", command=self.capture_screen)
        btn_capture.pack(side=tk.LEFT, padx=10)
        
        btn_solve = ttk.Button(top_frame, text="🧠 Solve", command=self.solve_game)
        btn_solve.pack(side=tk.LEFT, padx=10)
        
        btn_clear = ttk.Button(top_frame, text="❌ Clear Selection", command=self.clear_selection)
        btn_clear.pack(side=tk.LEFT, padx=10)

        self.status_var = tk.StringVar(value="Ready. Connect device and click Capture.")
        lbl_status = tk.Label(top_frame, textvariable=self.status_var, fg="blue")
        lbl_status.pack(side=tk.LEFT, padx=20)
        
        # Main Content
        content_frame = tk.Frame(self.root)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Left: Grid Canvas
        left_panel = tk.Frame(content_frame, width=600)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(left_panel, bg="#222", width=500, height=500)
        self.canvas.pack(pady=10)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        
        tk.Label(left_panel, text="Click cells to toggle manually if detection fails.").pack()
        
        # Right: Shape Selection
        right_panel = tk.Frame(content_frame, width=400)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=10)
        
        # Slots Area
        slots_frame = tk.LabelFrame(right_panel, text="Your Hand (Select a slot then pick a shape)")
        slots_frame.pack(fill=tk.X, pady=5)
        
        self.slot_buttons = []
        for i in range(3):
            btn = tk.Button(slots_frame, text=f"Slot {i+1}: (Empty)", 
                            command=lambda idx=i: self.select_slot(idx),
                            bg="#eee", height=2)
            btn.pack(fill=tk.X, pady=2)
            self.slot_buttons.append(btn)
        
        # Shape Library
        lib_frame = tk.LabelFrame(right_panel, text="Shape Library")
        lib_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Scrollable list for shapes
        canvas_lib = tk.Canvas(lib_frame)
        scrollbar = ttk.Scrollbar(lib_frame, orient="vertical", command=canvas_lib.yview)
        scrollable_frame = tk.Frame(canvas_lib)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas_lib.configure(scrollregion=canvas_lib.bbox("all"))
        )
        
        canvas_lib.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas_lib.configure(yscrollcommand=scrollbar.set)
        
        canvas_lib.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Populate Shapes
        for category, shape_names in SHAPE_CATEGORIES.items():
            lbl = tk.Label(scrollable_frame, text=f"--- {category} ---", font=("Arial", 10, "bold"))
            lbl.pack(anchor="w", pady=(10, 2))
            
            # Grid of buttons for shapes
            cat_frame = tk.Frame(scrollable_frame)
            cat_frame.pack(fill=tk.X)
            
            col = 0
            row = 0
            for name in shape_names:
                # Mini visual for button text? Too hard for now, just text.
                btn = tk.Button(cat_frame, text=name, width=15,
                                command=lambda n=name: self.assign_shape(n))
                btn.grid(row=row, column=col, padx=2, pady=2)
                col += 1
                if col > 2:
                    col = 0
                    row += 1
                    
        # Initial Highlight
        self.select_slot(0)

    def select_slot(self, idx):
        self.active_slot_index = idx
        # Update UI highlight
        for i, btn in enumerate(self.slot_buttons):
            if i == idx:
                btn.config(bg="#add8e6", relief=tk.SUNKEN)
            else:
                btn.config(bg="#eee", relief=tk.RAISED)

    def assign_shape(self, shape_name):
        self.selected_shapes[self.active_slot_index] = shape_name
        self.slot_buttons[self.active_slot_index].config(text=f"Slot {self.active_slot_index+1}: {shape_name}")
        
        # Auto-advance to next empty slot
        next_slot = (self.active_slot_index + 1) % 3
        self.select_slot(next_slot)

    def clear_selection(self):
        self.selected_shapes = [None, None, None]
        for i, btn in enumerate(self.slot_buttons):
            btn.config(text=f"Slot {i+1}: (Empty)")
        self.select_slot(0)
        self.solution_moves = None
        self.redraw_grid()

    def capture_screen(self):
        self.status_var.set("Capturing screen...")
        self.root.update()
        
        def task():
            try:
                raw_img = capture.get_screen()
                # Debug: Save the last capture
                import os
                abs_path = os.path.abspath("last_capture.jpg")
                cv2.imwrite(abs_path, raw_img)
                
                with open("debug_log.txt", "a") as f:
                    f.write(f"Captured image saved to: {abs_path}\n")
                
                state, processed_img, detected_shapes = image_processing.process_grid(raw_img)
                
                # Update UI in main thread
                self.root.after(0, lambda: self.on_capture_complete(state, processed_img, detected_shapes))
            except Exception as e:
                with open("debug_log.txt", "a") as f:
                    f.write(f"Capture Task Error: {e}\n")
                print(f"Capture Task Error: {e}")
                import traceback
                traceback.print_exc()
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
                self.root.after(0, lambda: self.status_var.set("Capture failed."))
        
        threading.Thread(target=task).start()

    def on_capture_complete(self, state, img, detected_shapes=None):
        msg = f"DEBUG: detected_shapes: {len(detected_shapes) if detected_shapes else 0}\n"
        
        self.grid_state = state
        self.current_grid_image = img
        self.solution_moves = None # Reset previous solution
        
        # Auto-fill shapes if detected
        if detected_shapes:
            self.selected_shapes = [None, None, None]
            for i, matrix in enumerate(detected_shapes):
                if i >= 3: break
                
                # Try to identify
                name = identify_shape(matrix)
                msg += f"Slot {i}: {name} (Mat: {matrix})\n"
                
                if name:
                    self.selected_shapes[i] = name
                    self.slot_buttons[i].config(text=f"Slot {i+1}: {name}")
                else:
                    self.slot_buttons[i].config(text=f"Slot {i+1}: (Unknown)")
            
            # Update UI highlight to first empty slot
            first_empty = 0
            for k in range(3):
                if self.selected_shapes[k] is None:
                    first_empty = k
                    break
            self.select_slot(first_empty)
            
        self.redraw_grid()
        self.status_var.set("Capture complete. Verify grid and shapes.")
        messagebox.showinfo("Debug Info", msg)

    def redraw_grid(self):
        if self.current_grid_image is None:
            return
            
        # We draw the image, then overlay the grid state, then overlay the solution if exists.
        
        # 1. Convert CV2 image to PhotoImage
        img_rgb = cv2.cvtColor(self.current_grid_image, cv2.COLOR_BGR2RGB)
        
        # If we have a solution, draw it on the CV2 image before converting?
        # Or draw on Canvas. Canvas is better for interactive toggling.
        # Let's draw the logical grid on top of the image in the Canvas.
        
        h, w, _ = img_rgb.shape
        # Resize to fit canvas
        canvas_w = 500
        scale = canvas_w / w
        new_h = int(h * scale)
        
        img_resized = cv2.resize(img_rgb, (canvas_w, new_h))
        
        # Encode to PNG for Tkinter
        success, encoded = cv2.imencode('.png', cv2.cvtColor(img_resized, cv2.COLOR_RGB2BGR))
        if not success: return
        
        data = base64.b64encode(encoded).decode('utf-8')
        self.tk_image = tk.PhotoImage(data=data) # Keep reference!
        
        self.canvas.config(width=canvas_w, height=new_h)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        
        # Draw logical grid overlay (semi-transparent logic is hard in Tkinter, use outlines)
        cell_w = canvas_w / 8
        cell_h = new_h / 8
        
        for r in range(8):
            for c in range(8):
                x1 = c * cell_w
                y1 = r * cell_h
                x2 = x1 + cell_w
                y2 = y1 + cell_h
                
                # If logical grid thinks it's filled, draw a red dot if it wasn't clear in image
                # Actually, just outline everything lightly
                self.canvas.create_rectangle(x1, y1, x2, y2, outline="#444", tags=f"cell_{r}_{c}")
                
                if self.grid_state[r, c] == 1:
                    # Draw visual indicator of filled state
                    margin = 5
                    self.canvas.create_oval(x1+margin, y1+margin, x2-margin, y2-margin, 
                                            outline="lime", width=2)

        # Draw Solution if available
        if self.solution_moves:
            colors = ["#ff0000", "#00ff00", "#0000ff"] # Red, Green, Blue for steps 1, 2, 3
            
            for idx, (piece_idx, r, c) in enumerate(self.solution_moves):
                # piece_idx is index in selected_shapes
                shape_name = self.selected_shapes[piece_idx]
                shape_matrix = SHAPES[shape_name]
                
                color = colors[idx]
                offset = idx * 2 # Slight offset to separate overlapping lines
                
                for pr in range(len(shape_matrix)):
                    for pc in range(len(shape_matrix[0])):
                        if shape_matrix[pr][pc] == 1:
                            gr = r + pr
                            gc = c + pc
                            
                            x1 = gc * cell_w + offset
                            y1 = gr * cell_h + offset
                            x2 = (gc+1) * cell_w - offset
                            y2 = (gr+1) * cell_h - offset
                            
                            self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=4)
                            # Add number label
                            if pr == 0 and pc == 0:
                                self.canvas.create_text(x1+10, y1+10, text=str(idx+1), fill="white", font=("Arial", 12, "bold"))


    def on_canvas_click(self, event):
        if self.current_grid_image is None: return
        
        # Determine cell
        canvas_w = int(self.canvas['width'])
        canvas_h = int(self.canvas['height'])
        
        cell_w = canvas_w / 8
        cell_h = canvas_h / 8
        
        c = int(event.x / cell_w)
        r = int(event.y / cell_h)
        
        if 0 <= r < 8 and 0 <= c < 8:
            # Toggle state
            self.grid_state[r, c] = 1 - self.grid_state[r, c]
            self.redraw_grid()

    def solve_game(self):
        # Validate inputs
        active_pieces = []
        indices = []
        
        for i, name in enumerate(self.selected_shapes):
            if name is not None:
                active_pieces.append(SHAPES[name])
                indices.append(i)
                
        if not active_pieces:
            messagebox.showwarning("No Pieces", "Please select at least one piece.")
            return
            
        self.status_var.set("Solving...")
        self.root.update()
        
        solver = BlockBlastSolver()
        # Solver expects list of matrices
        # But our solver logic assumes permutations of the input list.
        # We need to map the result back to our UI slots.
        
        # To keep it simple, we pass the active pieces. 
        # The solver returns indices relative to the list we passed.
        # We need to correct them to the original slots (0, 1, 2).
        
        score, moves = solver.solve(self.grid_state, active_pieces)
        
        if score <= -9000:
            messagebox.showerror("Game Over", "No solution found! You might lose.")
            self.status_var.set("No solution.")
        else:
            # moves is list of (idx_in_active_pieces, r, c)
            # Map idx_in_active_pieces -> original slot index
            final_moves = []
            for (local_idx, r, c) in moves:
                original_slot = indices[local_idx]
                final_moves.append((original_slot, r, c))
            
            self.solution_moves = final_moves
            self.redraw_grid()
            self.status_var.set(f"Solved! Score potential: {score}")


if __name__ == "__main__":
    root = tk.Tk()
    app = BlockBlastApp(root)
    root.mainloop()
