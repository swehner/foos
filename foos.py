#!/usr/bin/python

from subprocess import check_output, call
import time
import threading
import gui
import os
import sys
import getopt
import serial
from functools import partial
from collections import namedtuple
import multiprocessing
import Queue
from iohandler.io_serial import IOSerial
from iohandler.io_debug import IODebug
from iohandler.io_keyboard import IOKeyboard
from clock import Clock

ScoreInfo = namedtuple('ScoreInfo', ['yellow_goals', 'black_goals', 'time_goal'])

class ScoreBoard:
    def __init__(self, teams, event_queue):
        self.teams = teams
        self.scores = dict([(t, 0) for t in self.teams])
        self.last_goal = None
        self.last_goal_clock = Clock('last_goal_clock', event_queue)

    def score(self, team):
        self.increment(team)
        self.last_goal_clock.reset()

    def increment(self, team):
        s = self.scores.get(team, 0)
        self.scores[team] = s + 1

    def decrement(self, team):
        s = self.scores.get(team, 0)
        self.scores[team] = max(s - 1, 0)

    def getScore(self):
        return self.scores

    def getInfo(self):
        if self.scores[self.teams[0]] > 0 or self.scores[self.teams[1]] > 0:
            time_goal = time.strftime('Last goal: %M:%S', time.gmtime(self.last_goal))
        else:
            time_goal = ''

        return ScoreInfo(self.scores['yellow'], self.scores['black'], time_goal)

    def reset(self):
        for k in self.scores:
            self.scores[k] = 0

    def update_last_goal(self, seconds):
        self.last_goal = seconds


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
                action = board.score

            action(color)
        else:
            if delta < 1:
                replay(True)
            else:
                upload()

        del et[event.action]

teams = ['black', 'yellow']

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

last_goal_time = 0

def process_command(command):
    print("COMMAND: ", command)

    if command in button_events:
        buttons.event(board, button_events[command])

    if command == 'BG' or command == 'YG':
        now = time.time()
        global last_goal_time
        guard_interval = 3
        if now > last_goal_time+guard_interval:
            last_goal_time = now
            if command == 'BG':
                board.score('black')
            if command == 'YG':
                board.score('yellow')
            print board.getInfo()
            scored()
        else:
            print("Ignoring goal command {} happening too soon".format(command))


def replay(manual=False, regenerate=True):
    call(["./replay.sh", "manual" if manual else "auto", "true" if regenerate else "false"])
    return


def upload():
    call(["./upload-latest.sh"])


def scored():
    replay()


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

event_queue = multiprocessing.Queue()

board = ScoreBoard(teams, event_queue)
buttons = Buttons()

IOSerial(event_queue)
IODebug(event_queue)
IOKeyboard(event_queue)

draw()

while True:
    e = event_queue.get(True)
    if e['type'] == 'quit':
        sys.exit(0)
    elif e['type'] == 'input_command':
        print("Received command {0} from {1}".format(e['value'], e['source']))
        process_command(e['value'])
    elif e['type'] == 'clock':
        seconds = e['value']
        if e['name'] == 'last_goal_clock':
            board.update_last_goal(seconds)

    draw()

