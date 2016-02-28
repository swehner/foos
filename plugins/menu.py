from .buttons import *


class Plugin(Buttons):
    def __init__(self, bus):
        super().__init__(bus, long_press_delay=0.3, enabled=False)

    def generateKeyMap(self):
        key_map = {}
        for d in [down(['black_minus'], ('menu_down', {}), ar=True),
                  down(['yellow_minus'], ('menu_down', {}), ar=True),
                  down(['black_plus'], ('menu_up', {}), ar=True),
                  down(['yellow_plus'], ('menu_up', {}), ar=True),
                  down(['ok'], ('menu_select', {})),
                  down(['black_minus', 'black_plus'], None, long=('menu_hide', {})),
                  down(['yellow_minus', 'yellow_plus'], None, long=('menu_hide', {}))]:
            key_map.update(d)

        return key_map

    def process_event(self, ev):
        if ev.name == 'menu_visible':
            self.setEnabled(True)
        elif ev.name == 'menu_hidden':
            self.setEnabled(False)
        else:
            super().process_event(ev)
