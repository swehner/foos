import time
import os
from .io_base import IOBase
from .arduino import getEventForButton


class IODebug(IOBase):
    def convert_data(self, data):
        return ("Leds: %s\n" % ', '.join(data))

    def reader_thread(self):
        fifo_file = "/tmp/foos-debug.in"
        try:
            os.mkfifo(fifo_file)
        except:
            pass
        while True:
            f = open(fifo_file, "r")
            if not f:
                print("Error opening fifo file " + fifo_file)
                time.sleep(5)
                continue
            print("Opened new debugging session")
            while True:
                line = f.readline()
                if not line:
                    break
                line = line.strip()
                ev = getEventForButton(line)
                if ev:
                    self.bus.notify(ev)

    def writer_thread(self):
        fifo_file = "/tmp/foos-debug.out"
        try:
            os.mkfifo(fifo_file)
        except:
            pass

        f = open(fifo_file, "w")
        while True:
            line = self.write_queue.get()
            while True:
                try:
                    f.write(line)
                    f.flush()
                    break
                except:
                    f = open(fifo_file, "w")
                    if not f:
                        print("Error opening fifo file " + fifo_file)
                        time.sleep(5)
                    continue
