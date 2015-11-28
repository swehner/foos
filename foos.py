#!/usr/bin/python

from subprocess import check_output, call
import time
import threading
import gui
import pygame
import sys
import getopt
from functools import partial


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
    buttons = {
        'white_minus': 'down',
        'white_plus': 'down',
        'black_minus': 'down',
        'black_plus': 'down',
        'replay': 'down'
    }

    def event(self, board, what):
        button, state = what.split('#')
        print "Button {} is now {}".format(button, state)

        if state == 'up':
            if button == 'white_minus':
                board.decrement('WHITE')
            elif button == 'white_plus':
                board.increment('WHITE')
            elif button == 'black_minus':
                board.decrement('BLACK')
            elif button == 'black_plus':
                board.increment('BLACK')
            elif button == 'replay':
                replay(True)

teams = ["BLACK", "WHITE"]
board = ScoreBoard(teams)
buttons = Buttons()

button_events = [
    'white_minus#down',
    'white_minus#up',
    'white_plus#down',
    'white_plus#up',
    'black_minus#down',
    'black_minus#up',
    'black_plus#down',
    'black_plus#up',
    'replay#down',
    'replay#up'
]


def readArduino():
#    tty = getTTY()
#    with open(tty, "r") as f:
    for line in sys.stdin:
        line = line.strip()
        if len(line) <= 0:
            continue
        print("ARD: ", line)

        if line in button_events:
            buttons.event(board, line)

        if line == 'black_goal' or line == 'white_goal':
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

key_map = {
    pygame.K_PERIOD: partial(sys.exit, 0),
    pygame.K_a: board.anull,
    pygame.K_r: board.reset,
    pygame.K_o: partial(board.increment, "WHITE"),
    pygame.K_p: partial(board.increment, "BLACK"),
    pygame.K_k: partial(board.decrement, "WHITE"),
    pygame.K_l: partial(board.decrement, "BLACK"),
    pygame.K_v: partial(replay, True),
    pygame.K_n: partial(replay, True, False),
    pygame.K_u: upload
}

buttons_map = {
    pygame.K_KP1: 'white_minus',
    pygame.K_KP3: 'white_plus',
    pygame.K_KP7: 'black_minus',
    pygame.K_KP9: 'black_plus',
    pygame.K_KP5: 'replay'
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
                event = buttons_map[e.key] + '#down'
                buttons.event(board, event)
        elif e.type == pygame.KEYUP:
            if e.key in buttons_map:
                event = buttons_map[e.key] + '#up'
                buttons.event(board, event)
        elif e.type == pygame.USEREVENT:
            replay()

    if len(events) > 0:
        print events
        draw()
