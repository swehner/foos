import time
from multiprocessing import Queue
from iohandler.io_debug import IODebug

q = Queue()
io = IODebug(q)
while True:
    line = q.get()
    print(line['value'])
    io.writeline("Response: " + line['value'])
    time.sleep(0.1)
