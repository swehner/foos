import time
from iohandler.io_debug import IODebug

io = IODebug()
while True:
    line = io.readline()
    if line:
        print(line)
        io.writeline("Response: " + line)
    time.sleep(0.1)
