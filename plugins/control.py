from .buttons import *

class Plugin(Buttons):
    def __init__(self, bus):
        super().__init__(bus, long_press_delay=0.6)

    def generateKeyMap(self):
        key_map = {}
        for d in [up(['black_minus'], ('decrement_score', {'team': 'black'})),
                  up(['black_plus'], ('increment_score', {'team': 'black'})),
                  up(['yellow_minus'], ('decrement_score', {'team': 'yellow'})),
                  up(['yellow_plus'], ('increment_score', {'team': 'yellow'})),
                  up(['ok'], ('replay_request', {}), long=('upload_request', {})),
                  down(['ok'], ('button_will_replay', {}), long=('button_will_upload', {})),
                  up(['black_minus', 'black_plus'], ('reset_score', {}), long=None),
                  up(['yellow_minus', 'yellow_plus'], ('reset_score', {}), long=None),
                  down(['black_minus', 'black_plus'], None, long=('menu_show', {})),
                  down(['yellow_minus', 'yellow_plus'], None, long=('menu_show', {}))]:
            key_map.update(d)
        return key_map

    def process_event(self, ev):
        if ev.name == 'menu_visible':
            self.setEnabled(False)
        elif ev.name == 'menu_hidden':
            self.setEnabled(True)
        else:
            super().process_event(ev)
