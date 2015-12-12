#!/usr/bin/python
from __future__ import absolute_import, division, print_function, unicode_literals

""" Example showing what can be left out. ESC to quit"""
import pi3d
import os
import datetime
import random
import threading
import time
import sys

#read scaling factor from argv if set, 2 means half the size
sf=1
if len(sys.argv) > 1:
  sf = int(sys.argv[1]) 

path = os.path.dirname(os.path.realpath(__file__))

w, h=(1920//sf, 1080//sf)

DISPLAY = pi3d.Display.create(x=0, y=0, w=w, h=h, background=(0.0, 0.0, 0.0, 1.0))
CAMERA = pi3d.Camera(is_3d=False, scale=1/sf)
shader = pi3d.Shader("uv_flat")

bg = pi3d.ImageSprite(os.path.join(path, "foosball.jpg"), shader, w=1920, h=1080, z=10)
sprite = pi3d.ImageSprite(os.path.join(path, "pattern.png"), shader, w=100.0, h=100.0, z=5.0)
yellow = pi3d.ImageSprite(os.path.join(path, "yellow.jpg"), shader, x=400, y=200, w=300.0, h=300.0, z=5.0)
black = pi3d.ImageSprite(os.path.join(path, "black.jpg"), shader, x=-400, y=200, w=300.0, h=300.0, z=5.0)

mykeys = pi3d.Keyboard()

#stuff for the floating thingy
xloc = 100.0
dx = 2.1
yloc = 100.0
dy = 1.13

def getTime():
  return "Now: "+ datetime.datetime.now().strftime("%H:%M:%S")

arialFont = pi3d.Font("UbuntuMono-B.ttf", (255,255,255,255), font_size=60)
mystring = pi3d.String(font=arialFont, string=getTime(), is_3d=False, z=6.0)
mystring.set_shader(shader)

ynumbers=[pi3d.ImageSprite(os.path.join(path, "numbers/%d.png" % i), shader, w=300, h=444, x=400, y=-200, z=5) for i in range(0,6)]
bnumbers=[pi3d.ImageSprite(os.path.join(path, "numbers/%d.png" % i), shader, w=300, h=444, x=-400, y=-200, z=5) for i in range(0,6)]

yScore=0
bScore=0

def randomScore():
  global yScore, bScore
  while True:
    time.sleep(1)
    yScore=random.randint(0,5)
    bScore=random.randint(0,5)

threading.Thread(target=randomScore, daemon=True).start()

try:

  while DISPLAY.loop_running():
    bg.draw()
    ynumbers[yScore].draw()  
    bnumbers[bScore].draw()  
    mystring.draw()
    mystring.quick_change(getTime())
    yellow.draw()
    black.draw()
    sprite.draw()
    sprite.rotateIncZ(1)
    #floating thingy stuff
    sprite.position(xloc, yloc, 5.0)
    if xloc > 300.0:
      dx = -2.1
    elif xloc < -300.0:
      dx = 2.1
    if yloc > 300.0:
      dy = -1.13
    elif yloc < -300.0:
      dy = 1.13
    xloc += dx
    yloc += dy
  
    if mykeys.read() == 27:
      break
except:
 pass


mykeys.close()
DISPLAY.destroy()
