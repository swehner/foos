import time
from .io_base import IOBase
from .. bus import Event


class IOKeyboard(IOBase):
    key_map = {
        87: 'yellow_minus',  # KP_1
        79: 'yellow_plus',  # KP_7
        89: 'black_minus',  # KP_3
        81: 'black_plus',  # KP_9
        84: 'ok',  # KP_5

        24: 'yellow_plus',  # Q
        26: 'black_plus',  # E
        39: 'ok',  # S
        52: 'yellow_minus',  # Z
        54: 'black_minus',  # C
    }

    goal_map = {
        83: 'yellow',  # KP_4
        85: 'black',  # KP_6

        38: 'yellow',  # A
        40: 'black',  # D
    }

    def reader_thread(self):
        from pi3d.Display import Display
        from pyxlib import x
        display = Display.INSTANCE
        last_event = None

        while True:
            time.sleep(0.01)
            while len(display.event_list) > 0:
                e = display.event_list.pop()
                if last_event == (e.type, e.xkey.keycode):
                    continue

                last_event = (e.type, e.xkey.keycode)
                if e.type == x.KeyPress or e.type == x.KeyRelease:
                    code = e.xkey.keycode
                    if code in self.key_map:
                        btn = self.key_map[code]
                        state = "down" if e.type == x.KeyPress else "up"
                        event = Event('button_event', {'source': 'keyboard', 'btn': btn, 'state': state})
                        self.bus.notify(event)

                    if code in self.goal_map and e.type == x.KeyPress:
                        team = self.goal_map[code]
                        event = Event('button_event', {'source': 'keyboard', 'btn': 'goal', 'team': team})
                        self.bus.notify(event)

                    if code == 60:  # PERIOD
                        self.bus.notify(Event('quit'))

    def writer_thread(self):
        while True:
            self.write_queue.get()
            # FIXME: What to do here? Make the num/caps/scroll lock keys blink? :P
            pass
