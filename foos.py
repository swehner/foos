#!/usr/bin/python2

from gl.foos_gui import Gui, GuiState
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
import os
import threading

from iohandler.io_serial import IOSerial
from iohandler.io_debug import IODebug
from iohandler.io_keyboard import IOKeyboard
from clock import Clock

State = namedtuple('ScoreInfo', ['yellow_goals', 'black_goals', 'last_goal'])


class ScoreBoard:
    event_queue = None
    last_goal_clock = None
    status_file = '.status'

    def __init__(self, event_queue):
        self.event_queue = event_queue
        self.reset()

    def score(self, team):
        d = self.last_goal_clock.get_diff()
        if d and d <= 3:
            print("Ignoring goal command {} happening too soon".format(team))
            return

        self.increment(team)
        self.last_goal_clock.reset()
        replay()
        # Ignore events any event while replaying
        q = self.event_queue
        while not q.empty():
            q.get_nowait()
            q.task_done()
        self.pushState()

    def increment(self, team):
        s = self.scores.get(team, 0)
        self.scores[team] = s + 1
        self.pushState()

    def decrement(self, team):
        s = self.scores.get(team, 0)
        self.scores[team] = max(s - 1, 0)
        self.pushState()

    def load_info(self):
        if os.path.isfile(self.status_file):
            with open(self.status_file, 'r') as f:
                state = pickle.load(f)
                self.scores['yellow'] = state.yellow_goals
                self.scores['black'] = state.black_goals
                selg.last_goal_clock.set(state.last_goal)

    def save_info(self):
        state = State(self.scores['yellow'], self.scores['black'], self.last_goal())
        with open(self.status_file, 'w') as f:
            pickle.dump(state, f)

    def reset(self):
        self.scores = {'black': 0, 'yellow': 0}
        if self.last_goal_clock:
            self.last_goal_clock.reset()
        else:
            self.last_goal_clock = Clock('last_goal_clock')
        self.pushState()

    def last_goal(self):
        return self.last_goal_clock.get()

    def pushState(self):
        state = GuiState(self.scores['yellow'], self.scores['black'], self.last_goal())
        gui.set_state(state)
        bot.send_info(state)


class Buttons:
    # Class to manage the state of the buttons and the needed logic
    event_table = {}

    def event(self, board, event):
        et = self.event_table
        print("New event:", event, et)

        now = time.time()
        if event.state == 'down':
            # Actions are executed on button release
            et[event.action] = now
            return

        if event.action not in et:
            # No press action => ignore
            return

        delta = now - et[event.action]
        print("Press duration:", delta)

        if event.action != 'ok':
            color, what = event.action.split('_')

            if ('yellow_minus' in et and 'yellow_plus' in et) or ('black_minus' in et and 'black_plus' in et):
                # Double press for reset?
                board.reset()
                for key in ['yellow_minus', 'yellow_plus', 'black_minus', 'black_plus']:
                        if key in et:
                            del et[key]
                return

            if what == 'minus':
                action = board.decrement
            else:
                action = board.increment

            action(color)
        else:
            if delta < 1:
                replay(True)
            else:
                upload()

        del et[event.action]

ButtonEvent = namedtuple('ButtonEvent', ['action', 'state'])

button_events = {
    'YD_D': ButtonEvent('yellow_minus', 'down'),
    'YD_U': ButtonEvent('yellow_minus', 'up'),
    'YI_D': ButtonEvent('yellow_plus', 'down'),
    'YI_U': ButtonEvent('yellow_plus', 'up'),
    'BD_D': ButtonEvent('black_minus', 'down'),
    'BD_U': ButtonEvent('black_minus', 'up'),
    'BI_D': ButtonEvent('black_plus', 'down'),
    'BI_U': ButtonEvent('black_plus', 'up'),
    'OK_D': ButtonEvent('ok', 'down'),
    'OK_U': ButtonEvent('ok', 'up')
}


def replay(manual=False, regenerate=True):
    #TODO: where to move this?
    call(["./replay.sh", "manual" if manual else "auto", "true" if regenerate else "false"])
    return


def upload():
    call(["./upload-latest.sh"])

try:
    opts, args = getopt.getopt(sys.argv[1:], "s:f:")
except getopt.GetoptError:
    print('usage: python2 ir_controller [-s]')
    print('-s: scale')
    print('-f: framerate')
    sys.exit(2)

fullscreen = False

sf = 0
frames = 0
for opt, arg in opts:
    if opt == '-f':
        frames = int(arg)
    if opt == '-s':
        sf = int(arg)

print("Run GUI")
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/gl/")
gui = Gui(sf, frames)
bot = hipbot.HipBot()

event_queue = queue.Queue()

board = ScoreBoard(event_queue)
# Load status and register save status on exit
board.load_info()
atexit.register(board.save_info)

buttons = Buttons()

IOSerial(event_queue)
IODebug(event_queue)

if gui.is_x11():
    print("Running Keyboard")
    IOKeyboard(event_queue)


def processEvents():
    while True:
        e = event_queue.get(True)
        print("Received event", e)
        if e['type'] == 'quit':
            gui.stop()
        elif e['type'] == 'input_command':
            command = e['value']

            if command in button_events:
                buttons.event(board, button_events[command])

            if command == 'BG' or command == 'YG':
                command2team = {'BG': 'black', 'YG': 'yellow'}
                board.score(command2team[command])

        event_queue.task_done()

threading.Thread(target=processEvents, daemon=True).start()
gui.run()
gui.cleanup()
