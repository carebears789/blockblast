import cv2
import numpy as np

def process_grid(image):
    try:
        """
        Analyzes the screenshot to find the 8x8 Block Blast grid.
        Returns:
            grid_state: 8x8 numpy array (1=filled, 0=empty)
            grid_image: Crop of the grid with visualization (for UI)
        """
        if image is None:
            return np.zeros((8, 8), dtype=int), None, []

        # Resize large images for faster processing (maintain aspect ratio)
        target_width = 600
        h, w = image.shape[:2]
        scale = target_width / float(w)
        processed_img = cv2.resize(image, (target_width, int(h * scale)))
        
        gray = cv2.cvtColor(processed_img, cv2.COLOR_BGR2GRAY)
        
        # 1. Edge Detection
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY_INV, 11, 2)

        # 2. Find Contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 3. Find the Grid Candidate
        best_contour = None
        max_area = 0
        
        center_x = processed_img.shape[1] // 2
        center_y = processed_img.shape[0] // 2
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 15000: # Slightly lower threshold for area
                continue
                
            x, y, w, h = cv2.boundingRect(cnt)
            aspect_ratio = float(w)/h
            
            # Grid should be roughly square and centered
            if 0.8 < aspect_ratio < 1.2:
                if abs((x + w/2) - center_x) < 150: 
                    if area > max_area:
                        # Filter out full screen or very large chunks (e.g. if crop is perfect)
                        # Use 95% threshold
                        if w > processed_img.shape[1] * 0.95 and h > processed_img.shape[0] * 0.95:
                            continue
                            
                        max_area = area
                        best_contour = cnt

        grid_state = np.zeros((8, 8), dtype=int)
        grid_roi = processed_img
        detected_shapes = []
        
        if best_contour is not None:
            x, y, w, h = cv2.boundingRect(best_contour)
            
            # Crop to grid (slightly inside borders)
            margin = int(w * 0.02)
            grid_roi = processed_img[y+margin:y+h-margin, x+margin:x+w-margin]
            
            # Calculate cell size from the bounding box, not the ROI, for consistency
            # The grid is 8x8
            cell_size_w = w / 8.0
            cell_size_h = h / 8.0
            avg_cell_size = (cell_size_w + cell_size_h) / 2.0
            
            cell_h = grid_roi.shape[0] / 8.0
            cell_w = grid_roi.shape[1] / 8.0
            
            cell_stats = []

            # Sample cell centers
            for r in range(8):
                for c in range(8):
                    cx = int(c * cell_w + cell_w/2)
                    cy = int(r * cell_h + cell_h/2)
                    
                    # patch sampling
                    s_w = int(cell_w * 0.2)
                    s_h = int(cell_h * 0.2)
                    patch = grid_roi[cy-s_h:cy+s_h, cx-s_w:cx+s_w]
                    
                    if patch.size == 0: 
                        cell_stats.append((r, c, 0, 0))
                        continue
                    
                    hsv_patch = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
                    mean_sat = np.mean(hsv_patch[:,:,1])
                    mean_val = np.mean(hsv_patch[:,:,2])
                    
                    cell_stats.append((r, c, mean_sat, mean_val))

            # Dynamic Thresholding using K-Means (k=2)
            data_points = np.array([[s, v] for (_, _, s, v) in cell_stats], dtype=np.float32)
            
            std_sat = np.std(data_points[:, 0])
            std_val = np.std(data_points[:, 1])
            
            # If variance is extremely low, the board is likely uniform (empty)
            if std_sat < 10 and std_val < 20:
                 mean_sat = np.mean(data_points[:, 0])
                 if mean_sat > 70: grid_state.fill(1)
                 else: grid_state.fill(0)
            else:
                criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
                _, labels, centers = cv2.kmeans(data_points, 2, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
                
                # Determine "filled" label based on Saturation (primary) and Value (secondary)
                c0 = centers[0]
                c1 = centers[1]
                
                # Use Saturation if difference is significant, else use Value
                if abs(c0[0] - c1[0]) > 15:
                    filled_label = 0 if c0[0] > c1[0] else 1
                else:
                    filled_label = 0 if c0[1] > c1[1] else 1
                
                # Ensure the "filled" cluster isn't actually just dark gray background
                f_center = centers[filled_label]
                if f_center[0] < 20 and f_center[1] < 100:
                    grid_state.fill(0)
                else:
                    for i, (r, c, _, _) in enumerate(cell_stats):
                        grid_state[r, c] = 1 if labels[i] == filled_label else 0

            # --- Shape Detection in "Hand" area ---
            # Hand is typically below the grid
            img_h, img_w = processed_img.shape[:2]
            hand_y_start = y + h + 10 # 10px buffer
            hand_roi = processed_img[hand_y_start:img_h, 0:img_w]
            
            detected_shapes = _extract_shapes_from_roi(hand_roi, avg_cell_size)

        else:
            print("Grid not found in image.")
            # Default empty return already setup

        return grid_state, grid_roi, detected_shapes

    except Exception as e:
        err_msg = f"ERROR in process_grid: {e}"
        print(err_msg)
        with open("error_log.txt", "a") as f:
            f.write(err_msg + "\n")
            import traceback
            traceback.print_exc(file=f)
            
        # Return safe default
        return np.zeros((8, 8), dtype=int), image, []


def _extract_shapes_from_roi(roi, cell_size):
    """
    Finds shapes in the ROI (bottom of screen).
    Returns list of binary matrices (lists of lists).
    """
    if roi.size == 0:
        return []
        
    # Convert to HSV for color segmentation
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    
    # Shapes in Block Blast are vibrant. Background is usually dark.
    # We filter for significant Saturation and Value.
    # Saturation > 40 (avoid gray/white), Value > 50 (avoid black)
    # UPDATED: Background detected with S=48. Increasing threshold to 70.
    lower = np.array([0, 70, 40])
    upper = np.array([180, 255, 255])
    mask = cv2.inRange(hsv, lower, upper)
    
    # Clean up noise
    kernel = np.ones((3,3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2) # Connect blocks
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter by area
    # Use a conservative min area for filtering noise, assuming at least 1 block of size 0.3*cell_size
    min_block_dim = cell_size * 0.3
    min_area = (min_block_dim * min_block_dim) * 0.5 
    
    valid_contours = []
    roi_h = roi.shape[0]
    
    roi_w = roi.shape[1]
    
    candidates = []
    dims = []
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > min_area:
            x, y, w, h = cv2.boundingRect(cnt)
            
            # Filter out footer UI/Ads (usually at the bottom)
            if y > roi_h * 0.6:
                continue
            
            # Filter out edge noise (touching left/right borders)
            if x < 5 or (x + w) > (roi_w - 5):
                continue
                
            candidates.append((x, cnt))
            dims.append(w)
            dims.append(h)
            
    if not candidates:
        return []

    # Sort left to right
    candidates.sort(key=lambda x: x[0])
    
    print(f"DEBUG: Found {len(candidates)} candidates after filtering.")
    for i, (cx, _) in enumerate(candidates):
        print(f"  Candidate {i}: x={cx}")
    
    # Estimate block unit size using Best Fit
    # We search for a unit size 'u' that minimizes the rounding error for all dimensions
    
    # Range: 30% to 70% of grid cell size
    search_start = int(cell_size * 0.3)
    search_end = int(cell_size * 0.7)
    if search_start < 10: search_start = 10
    if search_end <= search_start: search_end = search_start + 20
    
    best_u = search_start
    min_error = float('inf')
    
    # Check valid dimensions only
    valid_dims = [d for d in dims if d > search_start * 0.5]
    
    if not valid_dims:
        block_unit_size = cell_size * 0.5
    else:
        for u in range(search_start, search_end + 1):
            error = 0
            for d in valid_dims:
                ratio = d / float(u)
                rounded = round(ratio)
                if rounded == 0: rounded = 1 # Minimum 1 block
                
                # Penalty for deviation from integer
                error += abs(rounded - ratio)
                
            if error < min_error:
                min_error = error
                best_u = u
        
        block_unit_size = best_u
        print(f"DEBUG: Best fit block_unit_size = {block_unit_size} (Error: {min_error:.2f})")
        
    detected = []
    
    for _, cnt in candidates:
        x, y, w, h = cv2.boundingRect(cnt)
        
        # Estimate grid dimensions based on block_unit_size
        # Use round()
        cols = int(round(w / block_unit_size))
        rows = int(round(h / block_unit_size))
        
        if cols == 0: cols = 1
        if rows == 0: rows = 1
        
        # Create matrix
        matrix = [[0 for _ in range(cols)] for _ in range(rows)]
        
        local_cell_w = w / float(cols)
        local_cell_h = h / float(rows)
        
        # Check occupancy
        mask_roi = np.zeros((h, w), dtype=np.uint8)
        cv2.drawContours(mask_roi, [cnt], -1, 255, -1, offset=(-x, -y))
        
        filled_blocks = 0
        for r in range(rows):
            for c in range(cols):
                cx = int(c * local_cell_w + local_cell_w/2)
                cy = int(r * local_cell_h + local_cell_h/2)
                
                # Check safe bounds
                cx = min(max(cx, 0), w-1)
                cy = min(max(cy, 0), h-1)
                
                # Check center pixel
                if mask_roi[cy, cx] > 127:
                    matrix[r][c] = 1
                    filled_blocks += 1
                else:
                    # Fallback: check 3x3 patch in center
                    patch = mask_roi[max(0, cy-1):min(h, cy+2), max(0, cx-1):min(w, cx+2)]
                    if np.mean(patch) > 127:
                        matrix[r][c] = 1
                        filled_blocks += 1

        if filled_blocks > 0:
            detected.append(matrix)
            
    return detected[:3]
