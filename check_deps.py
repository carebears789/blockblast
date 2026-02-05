try:
    import tkinter
    import cv2
    import numpy
    print("All imports successful.")
except ImportError as e:
    print(f"Missing dependency: {e}")
