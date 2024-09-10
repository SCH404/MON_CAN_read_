import can
import sys

def open_can_interface(channel=0, bustype='kvaser', bitrate=500000):
    try:
        bus = can.interface.Bus(channel=channel, bustype=bustype, bitrate=bitrate)
        print(f"Kvaser CAN interface on channel {channel} opened.")
        return bus
    except Exception as e:
        print(f"Failed to open CAN interface: {e}")
        sys.exit(1)

def read_can_frame(bus):
    try:
        msg = bus.recv()  # Receive a message from the bus
        if msg:
            print(f"Received message: {msg}")
        else:
            print("No message received.")
    except Exception as e:
        print(f"Error reading from CAN bus: {e}")

def close_can_interface():
    print("CAN interface closed.")

# Main flow
channel = 0  # This is typically 0 for the first Kvaser channel, you can change if needed
bus = open_can_interface(channel=channel, bustype='kvaser')

try:
    while True:
        read_can_frame(bus)
except KeyboardInterrupt:
    pass
finally:
    close_can_interface()
