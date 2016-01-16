import time
import serial
import glob
from .io_base import IOBase
from .arduino import getEventForButton
from .. bus import Event

class IOSerial(IOBase):
    bitmap = {
        "YD": 0b00001,
        "YI": 0b00010,
        "BD": 0b00100,
        "BI": 0b01000,
        "OK": 0b10000
    }

    def __init__(self, bus):
        self.ser = None
        super().__init__(bus)

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
                line = self.ser.readline()
                try:
                    line = line.decode('ascii').strip()
                    ev = getEventForButton(line)
                    if ev:
                        self.bus.notify(ev)
                except Exception as e:
                    print(e)

            except serial.SerialException as e:
                print(e)
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
        if self.ser:
            self.ser.close()
            self.ser = None

        while not self.ser:
            tty_list = glob.glob("/dev/ttyUSB[0-9]")
            tty_list.extend(glob.glob("/dev/ttyACM[0-9]"))
            if not len(tty_list):
                print("No ttyUSB device available")
            else:
                try:
                    print("Opening", tty_list[0])
                    # seems like it's necessary to change the baudrate for it to be set correctly
                    self.ser = serial.Serial(tty_list[0], 9600, timeout=10)
                    self.ser.baudrate = 115200
                    self.bus.notify(Event("serial_connected"))
                    return
                except Exception as e:
                    print(e)

            self.bus.notify(Event("serial_disconnected"))
            time.sleep(1)
