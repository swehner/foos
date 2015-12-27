import time
from iohandler.io_base import IOBase


class IOKeyboard(IOBase):
    key_map = {
        87: 'YD',  # KP_1
        79: 'YI',  # KP_7
        89: 'BD',  # KP_3
        81: 'BI',  # KP_9
        84: 'OK',  # KP_5

        24: 'YI',  # Q
        26: 'BI',  # E
        39: 'OK',  # S
        52: 'YD',  # Z
        54: 'BD',  # C
    }

    goal_map = {
        83: 'YG',  # KP_4
        85: 'BG',  # KP_6

        38: 'YG',  # A
        40: 'BG',  # D
    }

    def reader_thread(self):
        from pi3d.Display import Display
        from pyxlib import x
        display = Display.INSTANCE
        while True:
            time.sleep(0.01)
            while len(display.event_list) > 0:
                e = display.event_list.pop()
                if e.type == x.KeyPress or e.type == x.KeyRelease:
                    code = e.xkey.keycode
                    command = None
                    if code in self.key_map:
                        command = self.key_map[code]
                        command += "_D" if e.type == x.KeyPress else "_U"

                    if code in self.goal_map and e.type == x.KeyPress:
                        command = self.goal_map[code]

                    if command:
                        self.read_queue.put({'type': 'input_command', 'source': 'keyboard', 'value': command})
                    if code == 60:  # PERIOD
                        self.read_queue.put({'type': 'quit'})

    def writer_thread(self):
        while True:
            self.write_queue.get()
            # FIXME: What to do here? Make the num/caps/scroll lock keys blink? :P
            pass
