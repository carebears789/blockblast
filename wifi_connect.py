import subprocess
import sys
import re

def run_adb_command(command):
    """Runs an adb command and returns output, handling errors."""
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except FileNotFoundError:
        return None, "ADB not found", 1

def list_devices():
    """Returns a list of connected devices (serial, status)."""
    out, err, code = run_adb_command(['adb', 'devices'])
    if code != 0:
        return []
    
    devices = []
    lines = out.split('\n')[1:] # Skip first line "List of devices attached"
    for line in lines:
        if line.strip():
            parts = line.split()
            if len(parts) >= 2:
                devices.append((parts[0], parts[1]))
    return devices

def connect():
    print("--- Android Wireless Debugging Connector ---")
    print("Ensure your phone and computer are on the same Wi-Fi network.")
    print("1. Go to Developer Options > Wireless Debugging.")
    print("2. Enable Wireless Debugging.")
    
    choice = input("Do you need to PAIR a new device? (required for Android 11+ first time) [y/N]: ").lower()
    
    if choice == 'y':
        print("\nOn your phone, select 'Pair device with pairing code'.")
        ip_port = input("Enter IP address and Port shown (e.g., 192.168.1.5:34567): ").strip()
        code = input("Enter the 6-digit Wi-Fi pairing code: ").strip()
        
        print(f"Pairing with {ip_port}...")
        out, err, ret = run_adb_command(['adb', 'pair', ip_port, code])
        print(out)
        if ret != 0:
            print(f"Pairing failed: {err}")
            return

    print("\nNow connecting to the device service...")
    # Wireless debugging port often changes or is different from pairing port
    ip_port = input("Enter IP address and Port for 'Wireless Debugging' (NOT the pairing port): ").strip()
    
    print(f"Connecting to {ip_port}...")
    out, err, ret = run_adb_command(['adb', 'connect', ip_port])
    print(out)
    if ret != 0:
        print(f"Connection failed: {err}")
    else:
        print("Connected!")
        # Verify
        devices = list_devices()
        print("\nConnected Devices:")
        for d in devices:
            print(f"- {d[0]} ({d[1]})")

if __name__ == "__main__":
    try:
        connect()
    except KeyboardInterrupt:
        print("\nCancelled.")
