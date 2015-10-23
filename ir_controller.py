#!/usr/bin/python

from subprocess import check_output, call
import time
import threading
import gui
import pygame

def getTTY(baud=115200):
  tty = check_output("ls /dev/ttyACM[0-9]", shell=True).strip()
  call(["/bin/stty", "-F", tty,  "%d"%baud])
  return tty


class ScoreBoard:
  def __init__(self, teams, min_goal_interval = 3):
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
      score = min(self.scores[self.last_team]-1, 0)
      self.scores[self.last_team] = score 
 
  def reset(self):
    for k in self.scores:
      self.scores[k]=0

teams = ["BLACK", "WHITE"]
board = ScoreBoard(teams)
stop = False

def readArduino():
  tty=getTTY()
  with open(tty, "r") as f:
    while not stop:
      line = f.readline().strip()
      if len(line) > 0:
        print("ARD: ", line)
        matched_teams = [t for t in teams if t in line]
        if len(matched_teams) > 0:
          if board.score(matched_teams[0]):
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


print("Run GUI")
screen = gui.pyscope()
draw()

print("Run Arduino thread")
t1 = threading.Thread(target=readArduino)
t1.daemon = True
t1.start()

while not stop:
  events = pygame.event.get()
  for e in events:
    if e.type == pygame.QUIT:
      stop=True
    elif e.type == pygame.KEYDOWN:
      if e.key == pygame.K_PERIOD:
        stop=True
      if e.key == pygame.K_a:
        board.anull()
      if e.key == pygame.K_r:
        board.reset()
      if e.key == pygame.K_o:
        board.increment("WHITE")
      if e.key == pygame.K_p:
        board.increment("BLACK")
      if e.key == pygame.K_k:
        board.decrement("WHITE")
      if e.key == pygame.K_l:
        board.decrement("BLACK")
      if e.key == pygame.K_v:
        replay(True)
      if e.key == pygame.K_n:
        replay(True, False)
      if e.key == pygame.K_u:
        upload()
    elif e.type == pygame.USEREVENT:
        replay()

  if len(events) > 0:
    print events
    draw()

  time.sleep(0.01)

pygame.quit()
