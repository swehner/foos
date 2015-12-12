#!/usr/bin/python2

import gui
import sys
import time
import Queue
import getopt
from collections import namedtuple
from subprocess import check_output, call

from iohandler.io_serial import IOSerial
from iohandler.io_debug import IODebug
from iohandler.io_keyboard import IOKeyboard
from clock import Clock

ScoreInfo = namedtuple('ScoreInfo', ['yellow_goals', 'black_goals', 'time_goal'])

class ScoreBoard:
    event_queue = None
    last_goal_clock = None

    def __init__(self, event_queue):
        self.event_queue = event_queue
        self.reset()

    def score(self, team):
        if self.last_goal() <= 3:
            print("Ignoring goal command {} happening too soon".format(command))
            return

        self.increment(team)
        self.last_goal_clock.reset()
        replay()
        # Ignore events any event while replaying
        q = self.event_queue
        while not q.empty():
            q.get_nowait()
            q.task_done()

    def increment(self, team):
        s = self.scores.get(team, 0)
        self.scores[team] = s + 1

    def decrement(self, team):
        s = self.scores.get(team, 0)
        self.scores[team] = max(s - 1, 0)

    def getInfo(self):
        if sum(self.scores.values()):
            last_goal = self.last_goal_clock.get()
            time_goal = time.strftime('Last goal: %M:%S', time.gmtime(last_goal))
        else:
            time_goal = ''

        return ScoreInfo(self.scores['yellow'], self.scores['black'], time_goal)

    def reset(self):
        self.scores = {'black': 0, 'yellow': 0}
        if self.last_goal_clock:
            self.last_goal_clock.reset()
        else:
            self.last_goal_clock = Clock('last_goal_clock', self.event_queue)

    def last_goal(self):
        return self.last_goal_clock.get()


class Buttons:
    # Class to manage the state of the buttons and the needed logic
    event_table = {}

    def event(self, board, event):
        et = self.event_table
        print "New event:", event, et

        now = time.time()
        if event.state == 'down':
            # Actions are executed on button release
            et[event.action] = now
            return

        if event.action not in et:
            # No press action => ignore
            return

        delta = now - et[event.action]
        print "Press duration:", delta

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
    call(["./replay.sh", "manual" if manual else "auto", "true" if regenerate else "false"])
    return


def upload():
    call(["./upload-latest.sh"])


def draw():
    screen.drawScore(board.getInfo())


try:
    opts, args = getopt.getopt(sys.argv[1:], "f")
except getopt.GetoptError:
    print 'usage: python2 ir_controller [-f]'
    print '-f: Fullscreen mode'
    sys.exit(2)

fullscreen = False

for opt, arg in opts:
    if opt == '-f':
        fullscreen = True

print("Run GUI")
screen = gui.pyscope(fullscreen)

event_queue = Queue.Queue()

board = ScoreBoard(event_queue)
buttons = Buttons()

IOSerial(event_queue)
IODebug(event_queue)
IOKeyboard(event_queue)

draw()

while True:
    e = event_queue.get(True)
    print "Received event", e
    if e['type'] == 'quit':
        sys.exit(0)
    elif e['type'] == 'input_command':
        command = e['value']

        if command in button_events:
            buttons.event(board, button_events[command])

        if command == 'BG' or command == 'YG':
            command2team = {'BG': 'black', 'YG': 'yellow'}
            board.score(command2team[command])
    elif e['type'] == 'clock':
        # No need to do anything, we just need the redraw
        pass
    draw()
    event_queue.task_done()
