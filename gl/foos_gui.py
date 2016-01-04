#!/usr/bin/python
from __future__ import absolute_import, division, print_function, unicode_literals

import pi3d
import os
import datetime
import random
import threading
import time
import sys
import traceback
import math
import numpy
import glob
from gl import monkeypatch

monkeypatch.patch()


class GuiState():
    def __init__(self, yScore=0, bScore=0, lastGoal=None):
        self.yScore = yScore
        self.bScore = bScore
        self.lastGoal = lastGoal


class Counter():
    def __init__(self, value, shader, prefix, **kwargs):
        self.textures = [pi3d.Texture("numbers/%s%d.png" % (prefix, i))
                         for i in range(0, 10)]
        self.value = value
        self.number = pi3d.ImageSprite(self.textures[value], shader, **kwargs)
        self.anim_start = None
        self.speed = 5
        self.maxAngle = 10
        self.time = 0.8

    def step(self, now):
        s = self.number
        s.set_textures([self.textures[self.value % 10]])

        if self.anim_start and (now - self.anim_start) <= self.time:
            angle = self.animValue(now) * self.maxAngle
            s.rotateToZ(angle)
        else:
            s.rotateToZ(0)
            self.anim_start = None

    def setValue(self, value):
        if self.value != value:
            self.value = value
            self.anim_start = time.time()

    def animValue(self, now):
        x = now - self.anim_start
        return math.sin(2 * math.pi * x * self.speed) * math.pow(100., -x * x)

    def shape(self):
        return self.number


class Anim:
    def __init__(self, shape, opos=(0, 0, 0), oscale=(1, 1, 1)):
        self.tstart = 0
        self.duration = 0.3
        self.pos = opos
        self.scale, self.shape = oscale, shape
        self.tpos, self.tscale = self.pos, self.scale
        self.opos, self.oscale = self.pos, self.scale

    def step(self, now):
        tdiff = now - self.tstart
        tdiff /= self.duration
        tdiff = math.pow(tdiff, 2)
        if tdiff > 1:
            self.tstart = 0
            self.pos, self.scale = self.tpos, self.tscale
        else:
            self.pos = numpy.add(self.opos, numpy.multiply(tdiff, numpy.subtract(self.tpos, self.opos)))
            self.scale = numpy.add(self.oscale, numpy.multiply(tdiff, numpy.subtract(self.tscale, self.oscale)))

        self.shape.position(*self.pos)
        self.shape.scale(*self.scale)

    def next(self, tpos, tscale, now):
        self.opos = (self.shape.x(), self.shape.y(), self.shape.z())  # self.pos
        # extract current sx, sy, sz (no accessors defined)
        u = self.shape.unif
        self.oscale = (u[6], u[7], u[8])  # self.scale
        self.tpos, self.tscale = tpos, tscale
        self.tstart = now


class Gui():
    def __init__(self, scaling_factor, fps, bus, show_leds=False, bg_change_interval=300):
        self.state = GuiState()
        self.overlay_mode = False
        self.bus = bus
        self.bus.subscribe(self.process_event)
        self.show_leds = show_leds
        self.last_bg_change = time.time()
        self.bg_change_interval = bg_change_interval
        self.bg_idx = 0
        self.__init_display(scaling_factor, fps)
        if self.is_x11():
            monkeypatch.fixX11KeyEvents(self.DISPLAY)

        self.__setup_sprites()

    def __init_display(self, sf, fps):
        bgcolor = (0.0, 0.0, 0.0, 0.2)
        if sf == 0:
            #adapt to screen size
            self.DISPLAY = pi3d.Display.create(background=bgcolor)
            sf = 1920 / self.DISPLAY.width
        else:
            print("Forcing size")
            self.DISPLAY = pi3d.Display.create(x=0, y=0, w=1920 // sf, h=1080 // sf,
                                               background=bgcolor)

        self.DISPLAY.frames_per_second = fps
        print("Display %dx%d@%d" % (self.DISPLAY.width, self.DISPLAY.height, self.DISPLAY.frames_per_second))

        self.CAMERA = pi3d.Camera(is_3d=False, scale=1 / sf)

    def __move_sprites(self, now=None):
        if now is None:
            now = time.time()

        if self.overlay_mode:
            posx = 800
            posy = 450
            scale = (0.2, 0.2, 1.0)
            self.yAnim.next((posx - 65, posy, 5), scale, now)
            self.bAnim.next((posx + 65, posy, 5), scale, now)
        else:
            scale = (1, 1, 1)
            self.yAnim.next((-380, 0, 5), scale, now)
            self.bAnim.next((380, 0, 5), scale, now)

    def __setup_sprites(self):
        flat = pi3d.Shader("uv_flat")

        self.bg_textures = [pi3d.Texture(f) for f in glob.glob("gl/bg/*.jpg")]

        self.bg = pi3d.ImageSprite(self.bg_textures[0], flat, w=1920, h=1080, z=10)
        self.logo = pi3d.ImageSprite("logo.png", flat, w=80, h=80, x=880, y=-460, z=5)
        font = pi3d.Font("LiberationMono-Bold.ttf", (255, 255, 255, 255), font_size=60)

        self.goal_time = pi3d.String(font=font, string=self.__get_time_since_last_goal(),
                                     is_3d=False, y=390, z=5)
        self.goal_time.set_shader(flat)

        s = 512
        self.yCounter = Counter(0, flat, 'y_', w=s, h=s, z=5)
        self.bCounter = Counter(0, flat, 'b_', w=s, h=s, z=5)
        self.yAnim = Anim(self.yCounter.shape())
        self.bAnim = Anim(self.bCounter.shape())

        self.ledShapes = {
            "YD": pi3d.shape.Disk.Disk(radius=20, sides=12, x=-100, y=-430, z=0, rx=90),
            "YI": pi3d.shape.Disk.Disk(radius=20, sides=12, x=-100, y=-370, z=0, rx=90),
            "OK": pi3d.shape.Disk.Disk(radius=50, sides=12, x=0, y=-400, z=0, rx=90),
            "BD": pi3d.shape.Disk.Disk(radius=20, sides=12, x=100, y=-430, z=0, rx=90),
            "BI": pi3d.shape.Disk.Disk(radius=20, sides=12, x=100, y=-370, z=0, rx=90),
        }
        red = (255, 0, 0, 0)
        green = (0, 255, 0, 0)
        self.blackColor = (0, 0, 0, 0)
        self.ledColors = {"YD": red, "YI": green, "OK": green, "BD": red, "BI": green}
        self.leds = []
        # move immediately to position
        self.__move_sprites(0)

    def process_event(self, ev):
        if ev.name == "leds_enabled":
            self.leds = ev.data
        if ev.name == "quit":
            self.stop()
        if ev.name == "score_changed":
            self.set_state(GuiState(ev.data['yellow'], ev.data['black'], ev.data['last_goal']))
        if ev.name == "replay_start":
            self.overlay_mode = True
            self.__move_sprites()
        if ev.name == "replay_end":
            self.overlay_mode = False
            self.__move_sprites()

    def __set_bg(self, now):
        if now > (self.last_bg_change + self.bg_change_interval):
            self.last_bg_change = now
            self.bg_idx = (self.bg_idx + 1) % len(self.bg_textures)
            self.bg.set_textures([self.bg_textures[self.bg_idx]])

    def run(self):
        try:
            print("Running")
            while self.DISPLAY.loop_running():
                now = time.time()
                self.__set_bg(now)
                if not self.overlay_mode:
                    self.bg.draw()

                self.logo.draw()
                self.yAnim.step(now)
                self.yCounter.step(now)
                self.yCounter.shape().draw()
                self.bAnim.step(now)
                self.bCounter.step(now)
                self.bCounter.shape().draw()
                if not self.overlay_mode:
                    self.goal_time.draw()

                self.goal_time.quick_change(self.__get_time_since_last_goal())
                if self.show_leds:
                    self.__draw_leds()

            print("Loop finished")

        except:
            traceback.print_exc()

    def __draw_leds(self):
        for name, s in self.ledShapes.items():
            color = self.blackColor
            if name in self.leds:
                color = self.ledColors[name]

            s.set_material(color)
            s.draw()

    def __get_time_since_last_goal(self):
        if self.state.lastGoal:
            diff = time.time() - self.state.lastGoal
            fract = diff - int(diff)
            # replace 0 with O because of dots in 0 in the chosen font
            timestr = ("%s.%d" % (time.strftime("%M:%S", time.gmtime(diff)), int(fract * 10))).replace("0", "O")
        else:
            timestr = "--:--.-"

        return "Last Goal: %s" % timestr

    def set_state(self, state):
        self.state = self.__validate(state)
        self.yCounter.setValue(self.state.yScore)
        self.bCounter.setValue(self.state.bScore)

    def __validate(self, state):
        return GuiState(state.yScore, state.bScore, state.lastGoal)

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
