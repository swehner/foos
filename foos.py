#!/usr/bin/python

from subprocess import check_output, call
import time
import threading
import gui
import pygame
import sys
import getopt
from functools import partial
from collections import namedtuple


def getTTY(baud=115200):
    tty = check_output("ls /dev/ttyACM[0-9]", shell=True).strip()
    call(["/bin/stty", "-F", tty, "%d" % baud])
    return tty


class ScoreBoard:
    def __init__(self, teams, min_goal_interval=3):
        self.last_goal = 0
        self.min_goal_interval = min_goal_interval
        self.teams = teams
        self.scores = dict([(t, 0) for t in self.teams])
        self.last_team = None

    def score(self, team):
        now = time.time()
        if now > (self.last_goal + self.min_goal_interval):
            self.increment(team)
            self.last_goal = now
            self.last_team = team
            return True

        return False

    def increment(self, team):
        s = self.scores.get(team, 0)
        self.scores[team] = s + 1

    def decrement(self, team):
        s = self.scores.get(team, 0)
        self.scores[team] = max(s - 1, 0)

    def getScore(self):
        return self.scores

    def anull(self):
        if self.last_team:
            score = min(self.scores[self.last_team] - 1, 0)
            self.scores[self.last_team] = score

    def reset(self):
        for k in self.scores:
            self.scores[k] = 0


class Buttons:
    # Class to manage the state of the buttons and the needed logic
    event_table = {}

    def event(self, board, event):
        print "New event:", event, self.event_table

        now = time.time()
        if event.state == 'down':
            # Actions are executed on button release
            self.event_table[event.action] = now
            return

        if event.action not in self.event_table:
            # No press action => ignore
            return

        delta = now - self.event_table[event.action]
        print "Press duration:", delta

        if event.action != 'ok':
            color, what = event.action.split('_')

            if color == 'yellow':
                # Double press for reset?
                if 'yellow_minus' in self.event_table and 'yellow_plus' in self.event_table:
                    board.reset()
                    del self.event_table['yellow_minus']
                    del self.event_table['yellow_plus']
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

        del self.event_table[event.action]

teams = ['black', 'yellow']
board = ScoreBoard(teams)
buttons = Buttons()

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


def readArduino():
#    tty = getTTY()
#    with open(tty, "r") as f:
    for line in sys.stdin:
        line = line.strip()
        if len(line) <= 0:
            continue
        print("ARD: ", line)

        if line in button_events:
            buttons.event(board, button_events[line])

        if line == 'BG' or line == 'YG':
            team = line.split('_')[0].upper()
            board.score(team)
            print board.getScore()
            scored()


def replay(manual=False, regenerate=True):
    call(["./replay.sh", "manual" if manual else "auto", "true" if regenerate else "false"])


def upload():
    call(["./upload-latest.sh"])


def scored():
    draw()
    pygame.event.post(pygame.event.Event(pygame.USEREVENT, {}))


def draw():
    screen.drawScore(board.getScore())


try:
    opts, args = getopt.getopt(sys.argv[1:], "fa")
except getopt.GetoptError:
    print 'usage: python2 ir_controller [-f] [-a]'
    print '-f: Fullscreen mode'
    print '-a: Arduino mode (read commands from serial port)'
    sys.exit(2)

fullscreen = False
arduino = False

for opt, arg in opts:
    if opt == '-f':
        fullscreen = True
    elif opt == '-a':
        arduino = True

print("Run GUI")
screen = gui.pyscope(fullscreen)
draw()

if arduino:
    print("Run Arduino thread")
    t1 = threading.Thread(target=readArduino)
    t1.daemon = True
    t1.start()

# Keyboard control (to be deleted when the button code is working properly)
key_map = {
    pygame.K_PERIOD: partial(sys.exit, 0),
    pygame.K_a: board.anull,
    pygame.K_r: board.reset,
    pygame.K_o: partial(board.increment, "yellow"),
    pygame.K_p: partial(board.increment, "black"),
    pygame.K_k: partial(board.decrement, "yellow"),
    pygame.K_l: partial(board.decrement, "black"),
    pygame.K_v: partial(replay, True),
    pygame.K_n: partial(replay, True, False),
    pygame.K_u: upload
}

# Simulate button actions with the keyboard
buttons_map = {
    pygame.K_KP1: ButtonEvent('yellow_minus', None),
    pygame.K_KP3: ButtonEvent('yellow_plus', None),
    pygame.K_KP7: ButtonEvent('black_minus', None),
    pygame.K_KP9: ButtonEvent('black_plus', None),
    pygame.K_KP5: ButtonEvent('ok', None)
}

while not time.sleep(0.01):
    events = pygame.event.get()
    for e in events:
        if e.type == pygame.QUIT:
            sys.exit(0)
        elif e.type == pygame.KEYDOWN:
            if e.key in key_map:
                key_map[e.key]()
            if e.key in buttons_map:
                event = buttons_map[e.key]._replace(state = 'down')
                buttons.event(board, event)
        elif e.type == pygame.KEYUP:
            if e.key in buttons_map:
                event = buttons_map[e.key]._replace(state = 'up')
                buttons.event(board, event)
        elif e.type == pygame.USEREVENT:
            replay()

    if len(events) > 0:
        print events
        draw()
