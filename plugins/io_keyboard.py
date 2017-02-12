import time
from .io_base import IOBase
import pygame


class Plugin(IOBase):
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
        # Only allow keyboard events
        pygame.event.set_allowed(None)
        pygame.event.set_allowed([pygame.KEYDOWN, pygame.KEYUP])

        while True:
            e = pygame.event.wait()
            code = e.scancode

            if code in self.key_map:
                btn = self.key_map[code]
                state = "down" if e.type == pygame.KEYDOWN else "up"
                event_data = {'source': 'keyboard', 'btn': btn, 'state': state}
                self.bus.notify('button_event', event_data)

            if code in self.goal_map and e.type == pygame.KEYDOWN:
                team = self.goal_map[code]
                self.bus.notify('goal_event', {'source': 'keyboard', 'team': team})

            if code == 60:  # PERIOD
                self.bus.notify('quit')
                return

    def writer_thread(self):
        while True:
            self.write_queue.get()
            pass
