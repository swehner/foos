import time
import random
from iohandler.io_serial import IOSerial

io = IOSerial()
while True:
    line = io.readline()
    if line:
        response = 65 + int(random.random()*32)
        print(line)
        print("Response: %d" % response)
        io.writeline(chr(response))
    time.sleep(0.1)
