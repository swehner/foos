import time
from iohandler.io_base import IOBase


class IOKeyboard(IOBase):
    key_map = {
        87: 'YD',
        79: 'YI',
        89: 'BD',
        81: 'BI',
        84: 'OK'
    }

    goal_map = {
        83: 'YG',
        85: 'BG',
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
                    command = self.key_map.get(e.xkey.keycode, None)
                    if command:
                        command += "_D" if e.type == x.KeyPress else "_U"
                    else:
                        command = self.goal_map.get(e.xkey.keycode, None)

                    if command:
                        self.read_queue.put({'type': 'input_command', 'source': 'keyboard', 'value': command})
                    if e.xkey.keycode == 60:  # PERIOD
                        self.read_queue.put({'type': 'quit'})

    def writer_thread(self):
        while True:
            self.write_queue.get()
            # FIXME: What to do here? Make the num/caps/scroll lock keys blink? :P
            pass
