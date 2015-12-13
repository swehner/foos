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
from functools import partial
import traceback
import math

class GuiState():
    def __init__(self, yScore=0, bScore=0, lastGoal=None):
        self.yScore = yScore
        self.bScore = bScore
        self.lastGoal = lastGoal


def mangleDisplay(display):
    print("Careful! Mangling pi3d stuff")
    old = display._loop_begin
    from pyxlib import xlib, x

    # register for all key events
    xlib.XSelectInput(display.opengl.d, display.opengl.window, x.KeyPressMask | x.KeyReleaseMask)

    def my_begin(self):
        n = xlib.XEventsQueued(self.opengl.d, xlib.QueuedAfterFlush)
        for i in range(0, n):
            if xlib.XCheckMaskEvent(self.opengl.d, x.KeyPressMask | x.KeyReleaseMask, self.ev):
                self.event_list.append(self.ev)

        # continue with the old code (which processes events - so this might not work 100%
        old()

    display._loop_begin = partial(my_begin, display)


class Counter():
    textures = None
    def __init__(self, value, shader, **kwargs):
        if not Counter.textures:
            Counter.textures = [pi3d.Texture("numbers/%d.png" % i)
                                   for i in range(0, 10)]
        self.value = value
        self.number = pi3d.ImageSprite(Counter.textures[value], shader, **kwargs)
        self.anim_start = None
        self.speed = 5
        self.maxAngle = 5
        self.time = 0.8

    def draw(self):
        now = time.time()
        s = self.number
        s.set_textures([Counter.textures[self.value]])

        if self.anim_start and (now - self.anim_start) <= self.time:
            angle = self.animValue(now) * self.maxAngle
            s.rotateToZ(angle)
        else:
            s.rotateToZ(0)
            self.anim_start = None

        s.draw()

    def setValue(self, value):
        if self.value != value:
            self.value = value
            self.anim_start = time.time()

    def animValue(self, now):
        x = now - self.anim_start
        return math.sin(2 * math.pi * x * self.speed) * math.pow(100., -x * x)


class Gui():
    def __init__(self, scaling_factor, fps):
        self.do_replay = False
        self.state = GuiState()
        self.__init_display(scaling_factor, fps)
        if self.is_x11():
            mangleDisplay(self.DISPLAY)

        self.__setup_sprites()

    def __init_display(self, sf, fps):
        if sf == 0:
            #adapt to screen size
            self.DISPLAY = pi3d.Display.create(background=(0.0, 0.0, 0.0, 1.0))
            sf = 1920 / self.DISPLAY.width
        else:
            print("Forcing size")
            self.DISPLAY = pi3d.Display.create(x=0, y=0, w=1920 // sf, h=1080 // sf,
                                          background=(0.0, 0.0, 0.0, 1.0))

        self.DISPLAY.frames_per_second = fps
        print("Display %dx%d@%d" % (self.DISPLAY.width, self.DISPLAY.height, self.DISPLAY.frames_per_second))

        self.CAMERA = pi3d.Camera(is_3d=False, scale=1 / sf)

    def __setup_sprites(self):
        flat = pi3d.Shader("uv_flat")
        self.bg = pi3d.ImageSprite("foosball.jpg", flat, w=1920, h=1080, z=10)
        self.yellow = pi3d.ImageSprite("yellow.jpg", flat, x=-400, y=200, w=300.0, h=300.0, z=5.0)
        self.black = pi3d.ImageSprite("black.jpg", flat, x=400, y=200, w=300.0, h=300.0, z=5.0)
        font = pi3d.Font("UbuntuMono-B.ttf", (0, 0, 0, 255), font_size=60)
        self.goal_time = pi3d.String(font=font, string=self.__get_time_since_last_goal(), is_3d=False, y=400, z=6.0)
        self.goal_time.set_shader(flat)

        self.yCounter = Counter(0, flat, w=300, h=444, x=-400, y=-200, z=5)
        self.bCounter = Counter(0, flat, w=300, h=444, x=400, y=-200, z=5)

    def run(self):
        try:
            print("Running")
            while self.DISPLAY.loop_running():
                if self.do_replay:
                    self.__replay()
                    self.do_replay = False

                self.bg.draw()
                self.yellow.draw()
                self.black.draw()
                self.yCounter.draw()
                self.bCounter.draw()
                self.goal_time.draw()
                self.goal_time.quick_change(self.__get_time_since_last_goal())

            print("Loop finished")

        except:
            traceback.print_exc()

    def __get_time_since_last_goal(self):
        if self.state.lastGoal:
            diff = time.time() - self.state.lastGoal
            fract = diff - int(diff)
            timestr = "%s.%d" % (time.strftime("%M:%S", time.gmtime(diff)), int(fract * 10))
        else:
            timestr = "--:--.-"

        return "Last Goal: %s" % timestr

    def set_state(self, state):
        self.state = self.__validate(state)
        self.yCounter.setValue(self.state.yScore)
        self.bCounter.setValue(self.state.bScore)

    def __validate(self, state):
        return GuiState(state.yScore % 10, state.bScore % 10, state.lastGoal)

    def __replay(self):
        print("Replay now!")

    def request_replay(self):
        self.do_replay = True

    def cleanup(self):
        self.DISPLAY.destroy()

    def stop(self):
        self.DISPLAY.stop()

    def is_x11(self):
        return pi3d.PLATFORM != pi3d.PLATFORM_PI and pi3d.PLATFORM != pi3d.PLATFORM_ANDROID


class RandomScore(threading.Thread):
    def __init__(self, gui):
        super(RandomScore, self).__init__(daemon=True)
        self.gui = gui

    def run(self):
        state = GuiState()
        while True:
            if random.random() < 0.2:
                who = random.randint(0, 1)
                if who == 0:
                    state.yScore += 1
                else:
                    state.bScore += 1

                state.lastGoal = time.time()
                self.gui.set_state(state)
                self.gui.request_replay()
            time.sleep(1)


if __name__ == "__main__":
    #read scaling factor from argv if set, 2 means half the size, 0 means adapt automatically
    sf = 0
    frames = 0
    if len(sys.argv) > 1:
        sf = int(sys.argv[1])

    #optionally set the fps to limit CPU usage
    if len(sys.argv) > 2:
        frames = int(sys.argv[2])

    gui = Gui(sf, frames)

    RandomScore(gui).start()

    gui.run()
    gui.cleanup()
