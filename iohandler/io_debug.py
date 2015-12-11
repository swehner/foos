import pygame
import time
import os
from iohandler.io_base import IOBase

class IODebug(IOBase):

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
                pygame.fastevent.post(pygame.event.Event(pygame.USEREVENT, event_type='input_command', source='debug', value=line))

    def writer_thread(self):
        fifo_file = "/tmp/foos-debug.out"
        try:
            os.mkfifo(fifo_file)
        except:
            pass
        while True:
            f = open(fifo_file, "a")
            if not f:
                print("Error opening fifo file " + fifo_file)
                time.sleep(5)
                continue
            while True:
                if len(self.write_queue):
                    self.write_lock.acquire()
                    line = self.write_queue.pop(0)
                    self.write_lock.release()
                    f.write(line)
                    f.flush()
                else:
                    time.sleep(0.1)

