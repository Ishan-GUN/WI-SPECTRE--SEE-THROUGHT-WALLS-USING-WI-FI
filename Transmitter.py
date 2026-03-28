import network
import time
import machine
import socket

# Setup status LED
led = machine.Pin(2, machine.Pin.OUT)

def start_floodlight():
    # 1. Start Access Point
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    
    # AUTH_OPEN (0) makes it easier for the receiver to 'see' the headers
    ap.config(essid='RADAR_FLOODLIGHT', channel=6, authmode=0)
    
    print("RADAR FLOODLIGHT ONLINE")
    print("Listening for reflections on Channel 6...")

    # 2. Setup UDP Broadcaster
    # This forces the radio to actually transmit data packets, not just a name
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_dest = ('192.168.4.255', 1234)

    while True:
        try:
            # Blast a dummy packet into the air
            sock.sendto(b'RADAR_PULSE', broadcast_dest)
            
            # Visual feedback: Rapid blink means "Data is Blasting"
            led.value(1)
            time.sleep(0.01) # 10ms pulse
            led.value(0)
            
            # Wait 10ms before the next pulse (Total 50 pulses per second)
            time.sleep(0.01) 
            
        except Exception as e:
            print("Pulse Error:", e)
            time.sleep(1)

# Start the transmitter
start_floodlight()
