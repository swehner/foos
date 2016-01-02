#!/usr/bin/python3

from gl.foos_gui import Gui
import os
import sys
import time
import queue
import getopt
import atexit
import pickle
import hipbot
from collections import namedtuple
from subprocess import check_output, call
import threading
import traceback

from iohandler.io_serial import IOSerial
from iohandler.io_debug import IODebug
from iohandler.io_keyboard import IOKeyboard
from clock import Clock
from ledcontroller import LedController, Pattern
from soundcontroller import SoundController
import config
import uploader
from bus import Bus, Event

State = namedtuple('State', ['yellow_goals', 'black_goals', 'last_goal'])


class ScoreBoard:
    status_file = '.status'

    def __init__(self, bus):
        # Register save status on exit
        atexit.register(self.save_info)
        self.last_goal_clock = Clock('last_goal_clock')
        self.scores = {'black': 0, 'yellow': 0}
        self.bus = bus
        self.bus.subscribe(self.process_event, thread=True)
        if not self.__load_info():
            self.reset()

    def score(self, team):
        d = self.last_goal_clock.get_diff()
        if d and d <= 3:
            print("Ignoring goal command {} happening too soon".format(team))
            return

        self.last_goal_clock.reset()
        self.increment(team)
        data = self.__get_event_data()
        data['team'] = team
        self.bus.notify(Event('score_goal', data))

    def increment(self, team):
        s = self.scores.get(team, 0)
        self.scores[team] = (s + 1) % 10
        self.pushState()

    def decrement(self, team):
        s = self.scores.get(team, 0)
        self.scores[team] = max(s - 1, 0)
        self.pushState()

    def __load_info(self):
        loaded = False
        try:
            if os.path.isfile(self.status_file):
                with open(self.status_file, 'rb') as f:
                    state = pickle.load(f)
                    self.scores['yellow'] = state.yellow_goals
                    self.scores['black'] = state.black_goals
                    self.last_goal_clock.set(state.last_goal)
                    self.pushState()
                    loaded = True
        except:
            print("State loading failed")
            traceback.print_exc()

        return loaded

    def save_info(self):
        state = State(self.scores['yellow'], self.scores['black'], self.last_goal())
        with open(self.status_file, 'wb') as f:
            pickle.dump(state, f)

    def reset(self):
        self.scores = {'black': 0, 'yellow': 0}
        self.last_goal_clock.reset()
        self.bus.notify(Event('score_reset', self.__get_event_data()))
        self.pushState()

    def last_goal(self):
        return self.last_goal_clock.get()

    def __get_event_data(self):
        return {'yellow': self.scores['yellow'],
                'black': self.scores['black'],
                'last_goal': self.last_goal()}

    def pushState(self):
        self.bus.notify(Event("score_changed", self.__get_event_data()))

    def process_event(self, ev):
        if ev.name == 'button_event' and ev.data['btn'] == 'goal':
            # process goals
            board.score(ev.data['team'])
        if ev.name == 'increment_score':
            board.increment(ev.data['team'])
        if ev.name == 'decrement_score':
            board.decrement(ev.data['team'])
        if ev.name == 'reset_score':
            board.reset()


class Buttons:
    # Class to manage the state of the buttons and the needed logic
    event_table = {}

    def __init__(self, bus, upload_delay=1):
        self.upload_delay = upload_delay
        self.bus = bus
        self.bus.subscribe(self.process_event, thread=True)

    def process_event(self, ev):
        if ev.name != 'button_event' or 'state' not in ev.data:
            return

        button, state = (ev.data['btn'], ev.data['state'])

        et = self.event_table
        print("New event:", ev, et)

        now = time.time()
        if state == 'down':
            # Actions are executed on button release
            if button not in et:
                et[button] = now
                if button == 'ok':
                    schedule_upload_confirmation(self.upload_delay)

            return

        if button not in et:
            # No press action => ignore
            return

        delta = now - et[button]
        print("Press duration:", delta)

        if button != 'ok':
            color, what = button.split('_')

            if ('yellow_minus' in et and 'yellow_plus' in et) or ('black_minus' in et and 'black_plus' in et):
                self.bus.notify(Event('reset_score'))
                for key in ['yellow_minus', 'yellow_plus', 'black_minus', 'black_plus']:
                    if key in et:
                        del et[key]
                return

            if what == 'minus':
                gen_event = 'decrement_score'
            else:
                gen_event = 'increment_score'

            self.bus.notify(Event(gen_event, {'team': color}))
        else:
            reset_upload_confirmation()
            if delta < self.upload_delay:
                self.bus.notify(Event('replay_request'))
            else:
                self.bus.notify(Event('upload_request'))

        del et[button]


def replay_handler(ev):
    regenerate = True
    manual = False
    if ev.name == 'score_goal':
        pass
    elif ev.name == 'replay_request':
        manual = True
    else:
        return

    if config.replay_enabled:
        bus.notify(Event('replay_start'))
        call(["./replay.sh", "manual" if manual else "auto", "true" if regenerate else "false"])
        bus.notify(Event('replay_end'))


def schedule_upload_confirmation(delay):
    leds.setMode([Pattern(delay, []), Pattern(0.1, ["OK"])])


def reset_upload_confirmation():
    leds.setMode([])

try:
    opts, args = getopt.getopt(sys.argv[1:], "s:f:")
except getopt.GetoptError:
    print('usage: ./foos.py [-sf]')
    print('-s: scale')
    print('-f: framerate (default: 25)')
    sys.exit(2)

sf = 0
frames = 25
for opt, arg in opts:
    if opt == '-f':
        frames = int(arg)
    if opt == '-s':
        sf = int(arg)

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/gl/")

bus = Bus()
gui = Gui(sf, frames, bus, show_leds=config.onscreen_leds_enabled)
bot = hipbot.HipBot(bus)
sound = SoundController(bus)
board = ScoreBoard(bus)
bus.subscribe(replay_handler, thread=True)

# IO
buttons = Buttons(bus, upload_delay=0.6)
if config.serial_enabled:
    serial = IOSerial(bus)
debug = IODebug(bus)
leds = LedController(bus)
uploader.Uploader(bus)

if gui.is_x11():
    print("Running Keyboard")
    IOKeyboard(bus)

# Run main gui main loop
print("Run GUI")
gui.run()
gui.cleanup()
