import time
import serial
import glob
from iohandler.io_base import IOBase

class IOSerial(IOBase):

    ser = None

    def reader_thread(self):
        while True:
            if not self.ser:
                self.open_serial()
            try:
                line = self.ser.readline().strip().decode('utf-8')
                self.read_queue.put({'type': 'input_command', 'source': 'serial', 'value': line})
            except serial.SerialException:
                self.open_serial()

    def writer_thread(self):
        while True:
            line = self.write_queue.get()
            if not self.ser:
                # Wait until the reader thread opens the serial line again
                # FIXME: What if the queue fills up?
                time.sleep(1)
                continue

            self.ser.write(bytes(line, "ascii"))

    def open_serial(self):
        while True:
            tty_list = glob.glob("/dev/ttyUSB[0-9]")
            if not len(tty_list):
                print("No ttyUSB device available")
                time.sleep(1)
            else:
                self.ser = serial.Serial(tty_list[0], 115200)
                return

