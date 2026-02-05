import cv2
import numpy as np

def process_grid(image):
    """
    Analyzes the screenshot to find the 8x8 Block Blast grid.
    Returns:
        grid_state: 8x8 numpy array (1=filled, 0=empty)
        grid_image: Crop of the grid with visualization (for UI)
    """
    if image is None:
        return np.zeros((8, 8), dtype=int), None

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
                    max_area = area
                    best_contour = cnt

    grid_state = np.zeros((8, 8), dtype=int)
    
    if best_contour is not None:
        x, y, w, h = cv2.boundingRect(best_contour)
        
        # Crop to grid (slightly inside borders)
        margin = int(w * 0.02)
        grid_roi = processed_img[y+margin:y+h-margin, x+margin:x+w-margin]
        
        cell_h = grid_roi.shape[0] / 8
        cell_w = grid_roi.shape[1] / 8
        
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

        return grid_state, grid_roi

    else:
        print("Grid not found in image.")
        return grid_state, processed_img