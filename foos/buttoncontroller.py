import time
import queue
from threading import Thread
from .bus import Bus, Event


def key(btns, state, duration, ev, ar):
    return {(frozenset(btns), state, duration): (ev, ar)}


def press(btns, state, short, long=None, ar=False):
    s = {}
    if short:
        s.update(key(btns, state, 'short', short, ar))
    if not long:
        long = short
    s.update(key(btns, state, 'long', long, ar))

    return s


def up(btns, short, long=None):
    return press(btns, 'up', short, long, False)


def down(btns, short, long=None, ar=False):
    return press(btns, 'down', short, long, ar)


class Buttons:
    """Class to manage the state of the buttons and the needed logic"""

    def __init__(self, bus, enabled=True, long_press_delay=0.6):
        self.long_press_delay = long_press_delay
        self.queue = queue.Queue(maxsize=20)
        self.bus = bus
        self.bus.subscribe(self.enqueue, thread=False)
        self.buttons = frozenset([])
        self.last_time = 0
        self.press = 'short'
        self.enabled = enabled
        self.auto_repeat_interval = 0.2
        self.keymap = self.generateKeyMap()
        Thread(daemon=True, target=self.run).start()

    def enqueue(self, ev):
        try:
            self.queue.put_nowait(ev)
        except queue.Full:
            pass

    def checkState(self, state):
        keypress = (self.buttons, state, self.press)

        if keypress in self.keymap:
            ev, ar = self.keymap[keypress]
            self.bus.notify(Event(*ev))

    def run(self):
        while True:
            while not self.queue.empty():
                ev = self.queue.get_nowait()
                self.process_event(ev)

            if len(self.buttons) > 0:
                now = time.time()
                diff = now - self.last_time

                state = 'down'
                keypress = (self.buttons, state, self.press)

                if keypress in self.keymap:
                    ev, ar = self.keymap[keypress]
                    if diff > self.auto_repeat_interval and ar:
                        self.checkState('down')
                        self.last_time = now

                # generate key press event
                if self.press == 'short' and diff > self.long_press_delay:
                    self.press = 'long'
                    self.checkState('down')

            time.sleep(0.01)

    def setEnabled(self, state):
        self.enabled = state
        self.clearState()

    def clearState(self):
        self.buttons = frozenset([])
        self.last_time = 0
        self.press = 'short'

    def process_event(self, ev):
        if not self.enabled or ev.name != 'button_event' or 'state' not in ev.data:
            return

        button, state = (ev.data['btn'], ev.data['state'])

        now = time.time()
        if state == 'down':
            self.buttons = self.buttons.union([button])
            self.last_time = now
            # reset duration
            self.press = 'short'
            self.checkState(state)

        elif state == 'up':
            if button in self.buttons:
                self.checkState(state)
                # Delete all button events to avoid double processing (e.g. reset and one other key)
                self.clearState()


class GameButtons(Buttons):
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


class MenuButtons(Buttons):
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
