import can
import time
import sys
import threading
import keyboard

# Frames mapped to numeric keys
frames_dict = {
    '0': [0x00, 0x00, 0x00, 0x00,  0x5D, 0x0E, 0x61, 0x07],   
    '1': [0x00, 0x00, 0x00, 0x00,  0x56, 0xB1, 0xA6, 0x34],   
    '2': [0x00, 0x00, 0x00, 0x00,  0x50, 0x54, 0xEB, 0x61],   
    '3': [0x00, 0x00, 0x00, 0x00,  0x49, 0xF8, 0x2F, 0x8E],   
    '4': [0x00, 0x00, 0x00, 0x00,  0x43, 0x8B, 0x74, 0xBB], 
    '5': [0x00, 0x00, 0x00, 0x00,  0x3D, 0x2E, 0xB9, 0xE8],                            
    '6': [0x00, 0x00, 0x00, 0x00,  0x36, 0xD1, 0xFF, 0x15], 
    '7': [0x00, 0x00, 0x00, 0x00,  0x30, 0x85, 0x43, 0x42], 
    '8': [0x00, 0x00, 0x00, 0x00,  0x2A, 0x28, 0x78, 0x70],   
    '9': [0x00, 0x00, 0x00, 0x00,  0x26, 0x0F, 0xC0, 0x6E],   
}

# Stop frames
stop_frames = [
    [0x19, 0x99, 0x99, 0x99, 0x00, 0x00, 0x00, 0x00],  # First stop frame
    [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],  # Second stop frame
]

# Pre-stop frame to be sent 30 times
pre_stop_frame = [0x00, 0x00, 0x00, 0x00, 0x43, 0x8B, 0x74, 0xBB]

# Function to open the CAN interface using PCAN
def open_can_interface(channel='PCAN_USBBUS1', bustype='pcan', bitrate=500000):
    try:
        bus = can.interface.Bus(channel=channel, bustype=bustype, bitrate=bitrate)
        print(f"PCAN interface on channel {channel} opened.")
        return bus
    except Exception as e:
        print(f"Failed to open PCAN interface: {e}")
        sys.exit(1)

# Function to send a CAN frame
def send_can_frame(bus, arbitration_id, data):
    try:
        msg = can.Message(arbitration_id=arbitration_id, data=data, is_extended_id=False)
        bus.send(msg)
        print(f"Sent message: {msg}")
    except can.CanError as e:
        print(f"Failed to send message: {e}")

# Function to gradually interpolate between two frames (ramping effect)
def interpolate_frames(bus, arbitration_id, current_frame, target_frame, steps=10, delay=0.1):
    for i in range(steps):
        interpolated_frame = []
        for j in range(8):  # Assuming 8 bytes in the frame
            diff = (target_frame[j] - current_frame[j]) / steps
            interpolated_value = int(current_frame[j] + (i + 1) * diff)
            interpolated_frame.append(interpolated_value)
        
        send_can_frame(bus, arbitration_id, interpolated_frame)
        time.sleep(delay)

# Function to keep sending the final frame infinitely
def send_final_frame_infinite(bus, arbitration_id, final_frame, stop_event):
    while not stop_event.is_set():
        send_can_frame(bus, arbitration_id, final_frame)
        time.sleep(0.1)

# Function to handle the transition and then continuously send the final setpoint
def send_frame_with_inertia(bus, current_frame_id, target_frame_id, stop_event):
    arbitration_id = 0x11C  # Use the correct arbitration ID
    current_frame = frames_dict[current_frame_id]
    target_frame = frames_dict[target_frame_id]
    steps = 50  # Increase the number of steps for smoother transitions

    # Smooth transition to the target frame
    interpolate_frames(bus, arbitration_id, current_frame, target_frame, steps=steps)

    # Start sending the final frame continuously
    send_final_frame_infinite(bus, arbitration_id, target_frame, stop_event)

# Function to handle the stop command
def send_stop_frames(bus):
    arbitration_id = 0x11C  # Use the correct arbitration ID

    # Send the pre-stop frame 30 times
    for _ in range(5):
        send_can_frame(bus, arbitration_id, pre_stop_frame)
        time.sleep(0.1)

    # Send the first stop frame 10 times
    for _ in range(5):
        send_can_frame(bus, arbitration_id, stop_frames[0])
        time.sleep(0.1)

    # Send the second stop frame 10 times
    for _ in range(5):
        send_can_frame(bus, arbitration_id, stop_frames[1])
        time.sleep(0.1)

# Main function to handle user input and control the sending process
def main():
    bus = open_can_interface(channel='PCAN_USBBUS1', bustype='pcan')

    current_frame_id = '0'  # Start with frame '0'
    stop_event = threading.Event()
    send_thread = None

    print("Press 1 to 9 to send corresponding frames with smooth transition. Press 's' for stop command. Press 'c' to close the communication.")

    try:
        while True:
            # Detect key presses for frame selection
            for frame_id in frames_dict.keys():
                if keyboard.is_pressed(frame_id):
                    if send_thread and send_thread.is_alive():
                        stop_event.set()  # Stop the previous thread
                        send_thread.join()

                    stop_event.clear()  # Clear stop event for the next thread
                    send_thread = threading.Thread(target=send_frame_with_inertia, args=(bus, current_frame_id, frame_id, stop_event))
                    send_thread.start()

                    current_frame_id = frame_id  # Update the current frame ID after transition
                    time.sleep(0.3)  # Debounce keypress to avoid multiple transitions from one keypress

            # Detect 's' key to send stop frames
            if keyboard.is_pressed('s'):
                if send_thread and send_thread.is_alive():
                    stop_event.set()
                    send_thread.join()
                send_stop_frames(bus)

            # Detect 'c' key to stop the sending process and exit
            if keyboard.is_pressed('c'):
                if send_thread and send_thread.is_alive():
                    stop_event.set()
                    send_thread.join()
                break

            time.sleep(0.01)  # Small delay to reduce CPU usage

    finally:
        bus.shutdown()
        print("CAN interface closed.")

if __name__ == "__main__":
    main()
