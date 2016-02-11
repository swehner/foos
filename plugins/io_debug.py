import time
import os
import logging
from .io_base import IOBase
from .arduino import getEventForButton

logger = logging.getLogger(__name__)


class Plugin(IOBase):
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
                logger.error("Error opening fifo file %s", fifo_file)
                time.sleep(5)
                continue

            logger.info("Opened new debugging session")
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
                        logger.error("Error opening fifo file %s", fifo_file)
                        time.sleep(5)
                    continue
