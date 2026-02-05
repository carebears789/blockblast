import subprocess
import cv2
import numpy as np
import sys

SELECTED_DEVICE = None

def select_device():
    """
    Checks for connected devices. If multiple, asks user to pick.
    Returns the serial ID of the device to use.
    """
    global SELECTED_DEVICE
    if SELECTED_DEVICE:
        return SELECTED_DEVICE
        
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')[1:]
        devices = [line.split()[0] for line in lines if line.strip() and 'device' in line]
        
        if not devices:
            return None
            
        if len(devices) == 1:
            SELECTED_DEVICE = devices[0]
            return SELECTED_DEVICE
            
        print("\nMultiple devices found:")
        for i, dev in enumerate(devices):
            print(f"{i + 1}: {dev}")
            
        # If running in non-interactive mode (like just imported), we might fail here.
        # But for this CLI app, input() is fine.
        try:
            choice = int(input("Select device number: "))
            if 1 <= choice <= len(devices):
                SELECTED_DEVICE = devices[choice - 1]
                return SELECTED_DEVICE
        except ValueError:
            pass
            
        print("Invalid selection. Defaulting to first device.")
        SELECTED_DEVICE = devices[0]
        return SELECTED_DEVICE
        
    except FileNotFoundError:
        return None

def get_screen(device_id=None):
    """
    Captures the Android screen using ADB and returns it as an OpenCV image.
    """
    if device_id is None:
        device_id = select_device()
        
    cmd = ['adb']
    if device_id:
        cmd.extend(['-s', device_id])
    cmd.extend(['exec-out', 'screencap', '-p'])

    try:
        # Execute adb command to capture screen to stdout
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stream_data, error = process.communicate()

        if error:
            # Check if adb is just not found or if the device is offline
            err_msg = error.decode('utf-8')
            if "command not found" in err_msg:
                print("Error: 'adb' command not found. Please install Android Debug Bridge.")
                sys.exit(1)
            elif "no devices/emulators found" in err_msg:
                print("Error: No Android device found. Please connect your phone via USB and enable Debugging.")
                sys.exit(1)
            elif "more than one device" in err_msg:
                 # Should be handled by select_device, but safe fallback
                 print("Error: Multiple devices found. Please specify one.")
                 sys.exit(1)
            else:
                # Some other adb error (maybe unauthorized)
                # print(f"ADB Error: {err_msg}")
                # Sometimes stderr has warnings but stdout has image. Check stream_data size.
                pass

        if not stream_data:
            print(f"Error: No data received from ADB. {error.decode('utf-8') if error else ''}")
            sys.exit(1)

        # Convert the raw data to a numpy array
        image_array = np.frombuffer(stream_data, np.uint8)
        
        # Decode the image
        img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        if img is None:
            print("Error: Failed to decode image from ADB stream.")
            sys.exit(1)
            
        return img

    except FileNotFoundError:
        print("Error: 'adb' executable not found in PATH.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Test the capture
    img = get_screen()
    print(f"Successfully captured image with shape: {img.shape}")
    # Resize for easier viewing on desktop if needed
    scale_percent = 30 # percent of original size
    width = int(img.shape[1] * scale_percent / 100)
    height = int(img.shape[0] * scale_percent / 100)
    dim = (width, height)
    resized = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)
    
    cv2.imshow("ADB Screen Capture Test", resized)
    print("Press any key to close the window...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()
