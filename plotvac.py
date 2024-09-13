import can
from ctypes import c_int16 as int16
import matplotlib.pyplot as plt
import numpy as np
import collections
from matplotlib.animation import FuncAnimation
import time
import struct

# Define the arbitration IDs
VCU_pump_infos = 0x11C  
VCU_other_infos = 0x12C  # New ID
channel = 0  # Kvaser channel

# Initialize the deque for storing data
selectedinfos_11C = collections.deque(np.zeros(500))  # queue for 0x11C
selectedinfos_12C = collections.deque(np.zeros(500))  # queue for 0x12C

class CanHandler(can.Listener):
    def on_message_received(self, msg):
        # Ensure msg.data has enough length, otherwise fill with zeros
        data_bytes = msg.data + bytearray(8 - len(msg.data))

        if msg.arbitration_id == VCU_pump_infos:
            # Extract the relevant bytes (4th, 5th, 6th, and 7th bytes) for 0x11C
            byte_4 = data_bytes[4]
            byte_5 = data_bytes[5]
            byte_6 = data_bytes[6]
            byte_7 = data_bytes[7]
            raw_value_11C = struct.unpack('>I', bytes([byte_4, byte_5, byte_6, byte_7]))[0]
            selectedinfos_11C.append(raw_value_11C)

            # Update the text to display the four bytes near the plot
            
            #global byte_text_11C
            #byte_text_11C.set_text(f"0x11C Bytes:\n4th: {byte_4}\n5th: {byte_5}\n6th: {byte_6}\n7th: {byte_7}")

            # Maintain the size of the deque
            if len(selectedinfos_11C) > 500:
                selectedinfos_11C.popleft()

        elif msg.arbitration_id == VCU_other_infos:
            # Extract the relevant byte (2nd byte) for 0x12C
            raw_value_12C = data_bytes[2]
            selectedinfos_12C.append(raw_value_12C)

            # Maintain the size of the deque
            if len(selectedinfos_12C) > 500:
                selectedinfos_12C.popleft()

# Initialize CAN interface
ch = CanHandler()
try:
    cbus = can.interface.Bus(channel=channel, bustype="kvaser", bitrate=500000)
    notif = can.Notifier(cbus, [ch])
except can.CanError as e:
    print(f"CAN Error: {e}")

# Set up the plot
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), facecolor='#DEDEDE')
fig.subplots_adjust(right=0.75)  # Make room for text on the right side of the plot

# Initialize text for displaying byte values (for 0x11C)

#byte_text_11C = fig.text(0.85, 0.9, "", fontsize=12, bbox=dict(facecolor='white', alpha=0.5))

# Update function for the plot
def upd_graph(i):
    # Clear and update the first plot (for 0x11C)
    ax1.cla()
    ax1.plot(selectedinfos_11C)
    ax1.set_ylim(0, 1600000000)
    ax1.set_title("Data from 0x11C")
    ax1.grid(True)
    ax1.set_facecolor('#DEDEDE')

    # Clear and update the second plot (for 0x12C)
    ax2.cla()
    ax2.plot(selectedinfos_12C)
    ax2.set_ylim(0, 255)  # Adjust the y-limit for byte range
    ax2.set_title("Data from 0x12C")
    ax2.grid(True)
    ax2.set_facecolor('#DEDEDE')

# Animate the plots
ani = FuncAnimation(fig, upd_graph, interval=10)

plt.show()
