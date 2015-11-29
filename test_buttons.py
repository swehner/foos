import time
import sys
import threading
import serial
ser = serial.Serial('/dev/ttyUSB0', 115200)

states = [
(0b00001, 300),
(0b00010, 300),
(0b00100, 300),
(0b01000, 300),
(0b10000, 300),
(0b00011, 1000),
(0b01100, 1000),
(0b10000, 1000),
(0b00000, 500),
(0b00101, 500),
(0b01010, 500),
(0b10000, 500),
(0b11111, 500),
]

def readArduino():
    while True:
        line = ser.readline()
        line = line.strip()
        if len(line) <= 0:
            continue
        print("ARD: ", line)

t1 = threading.Thread(target=readArduino)
t1.daemon=True
t1.start()

time.sleep (5)
while True:
  for s, t in states:
    ser.write(chr(s + 32) + "\n")
    time.sleep(t/1000.)

