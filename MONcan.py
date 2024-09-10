import can
import sys
from can.interfaces.pcan.pcan import PcanCanInitializationError

def open_can_interface(channel='PCAN_USBBUS1', bustype='pcan', bitrate=500000):
    try:
        bus = can.interface.Bus(channel=channel, bustype=bustype, bitrate=bitrate)
        print(f"CAN interface {channel} opened.")
        return bus
    except PcanCanInitializationError as e:
        print(f"PCAN initialization error: {e}")
        sys.exit(1)
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

def close_can_interface(channel):
    print(f"CAN interface {channel} closed.")

# Main flow
channel = 'PCAN_USBBUS1'  # Change this to your actual PCAN channel
bus = open_can_interface(channel=channel, bustype='pcan')

try:
    while True:
        read_can_frame(bus)
except KeyboardInterrupt:
    pass
finally:
    close_can_interface(channel)
