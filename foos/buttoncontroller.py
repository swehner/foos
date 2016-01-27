import time
import queue
from threading import Thread
from .bus import Bus, Event


class Buttons:
    """Class to manage the state of the buttons and the needed logic"""

    def __init__(self, bus, upload_delay=0.6):
        self.upload_delay = upload_delay
        self.queue = queue.Queue(maxsize=20)
        self.bus = bus
        self.bus.subscribe(self.enqueue, thread=False)
        self.event_table = {}
        self.press = 'short'

        self.generateKeyMaps()
        Thread(daemon=True, target=self.run).start()

    def generateKeyMaps(self):
        def key(btns, state, duration, ev):
            return {(frozenset(btns), state, duration): ev}

        def press(btns, state, short, long=None):
            s = {}
            if short:
                s.update(key(btns, state, 'short', short))
            if not long:
                long = short
            s.update(key(btns, state, 'long', long))

            return s

        def up(btns, short, long=None):
            return press(btns, 'up', short, long)

        def down(btns, short, long=None):
            return press(btns, 'down', short, long)

        self.ingame_map = {}
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
            self.ingame_map.update(d)

        self.menu_map = {}
        for d in [up(['black_minus'], ('menu_down', {})),
                  up(['yellow_minus'], ('menu_down', {})),
                  up(['black_plus'], ('menu_up', {})),
                  up(['yellow_plus'], ('menu_up', {})),
                  up(['ok'], ('menu_select', {})),
                  down(['black_minus', 'black_plus'], ('menu_hide', {})),
                  down(['yellow_minus', 'yellow_plus'], ('menu_hide', {}))]:
            self.menu_map.update(d)

        self.keymap = self.ingame_map

    def enqueue(self, ev):
        try:
            self.queue.put_nowait(ev)
        except queue.Full:
            pass

    def checkState(self, state):
        et = self.event_table
        btns = frozenset(et.keys())
        keypress = (btns, state, self.press)

        if keypress in self.keymap:
            ev = self.keymap[keypress]
            self.bus.notify(Event(*ev))

    def run(self):
        while True:
            while not self.queue.empty():
                ev = self.queue.get_nowait()
                self.process_event(ev)

            et = self.event_table
            if len(et) > 0:
                diff = time.time() - max(et.values())

                # generate key press event
                if self.press == 'short' and diff > self.upload_delay:
                    self.press = 'long'
                    self.checkState('down')

            time.sleep(0.01)

    def clearState(self):
        self.event_table.clear()
        self.press = 'short'

    def process_event(self, ev):
        # switch keymap depending on game mode
        if ev.name == 'menu_visible':
            self.keymap = self.menu_map
            self.clearState()
        if ev.name == 'menu_hidden':
            self.keymap = self.ingame_map
            self.clearState()
        if ev.name != 'button_event' or 'state' not in ev.data:
            return

        button, state = (ev.data['btn'], ev.data['state'])

        et = self.event_table
        now = time.time()
        if state == 'down':
            et[button] = now
            # reset duration
            self.press = 'short'
            self.checkState(state)

        elif state == 'up':
            if button in et:
                self.checkState(state)
                # Delete all button events to avoid double processing (e.g. reset and one other key)
                self.clearState()
