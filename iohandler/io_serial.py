import time
import serial
import glob
from iohandler.io_base import IOBase

class IOSerial(IOBase):

    ser = None
    bitmap = {
        "YD": 0b00001,
        "YI": 0b00010,
        "BD": 0b00100,
        "BI": 0b01000,
        "OK": 0b10000
    }

    def __getArduinoValueFor(self, leds):
        value = sum(map(lambda x: IOSerial.bitmap.get(x, 0), leds))
        return chr(value + ord('A'))

    def convert_data(self, data):
        return (self.__getArduinoValueFor(data) + "\n").encode("ascii")

    def reader_thread(self):
        while True:
            if not self.ser:
                self.open_serial()
            try:
                line = self.ser.readline().strip().decode('ascii')
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

            self.ser.write(line)

    def open_serial(self):
        while True:
            tty_list = glob.glob("/dev/ttyUSB[0-9]")
            if not len(tty_list):
                print("No ttyUSB device available")
                time.sleep(1)
            else:
                self.ser = serial.Serial(tty_list[0], 115200)
                return
