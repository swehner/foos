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
from gl.anim import Move, Disappear, Wiggle, Delegate

monkeypatch.patch()


class GuiState():
    def __init__(self, yScore=0, bScore=0, lastGoal=None):
        self.yScore = yScore
        self.bScore = bScore
        self.lastGoal = lastGoal


class Counter(Delegate):
    def __init__(self, value, shader, prefix, **kwargs):
        self.textures = [pi3d.Texture("numbers/%s%d.png" % (prefix, i))
                         for i in range(0, 10)]
        self.value = value
        self.number = Wiggle(pi3d.ImageSprite(self.textures[value], shader, **kwargs),
                             5, 10, 0.8)
        super().__init__(self.number)

    def draw(self):
        self.number.set_textures([self.textures[self.value % 10]])
        self.number.draw()

    def setValue(self, value):
        if self.value != value:
            self.value = value
            self.wiggle()


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
        self.all_messages = []
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
            self.DISPLAY = pi3d.Display.create(x=0, y=0, w=int(1920 / sf), h=int(1080 / sf),
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
            self.yCounter.moveTo((posx - 65, posy, 5), scale)
            self.bCounter.moveTo((posx + 65, posy, 5), scale)
        else:
            scale = (1, 1, 1)
            self.yCounter.moveTo((-380, 0, 5), scale)
            self.bCounter.moveTo((380, 0, 5), scale)

    def __cp_lg(self):
        """Generate codepoint list for last goal display"""
        l = "Last Goal:.-O123456789"
        return map(ord, set(sorted(l)))

    def __display_message(self, string, shader):
        msg = pi3d.String(font=self.msg_font, string=string,
                          is_3d=False, y=-380, z=5)
        msg.set_shader(shader)
        msg = Disappear(msg, 2, 0.5)
        self.all_messages.append(msg)
        return msg

    def show_message(self, msg):
        for m in self.all_messages:
            if m == msg:
                m.show()
            else:
                m.hide()

    def __setup_sprites(self):
        flat = pi3d.Shader("uv_flat")

        self.bg_textures = [pi3d.Texture(f) for f in glob.glob("gl/bg/*.jpg")]

        self.bg = pi3d.ImageSprite(self.bg_textures[0], flat, w=1920, h=1080, z=10)
        self.logo = pi3d.ImageSprite("logo.png", flat, w=80, h=80, x=880, y=-460, z=5)

        self.instructions = pi3d.ImageSprite("instructions.png", flat, w=512, h=256, x=-1920 / 2 + 256 + 20, y=-1080 / 2 + 128 + 10, z=5)
        self.instructions.scale(0.75, 0.75, 1)
        self.instructions = Disappear(self.instructions)
        font = pi3d.Font("UbuntuMono-B.ttf", (255, 255, 255, 255), font_size=40, codepoints=self.__cp_lg(), image_size=1024)
        self.msg_font = pi3d.Font("UbuntuMono-B.ttf", (255, 255, 255, 255), font_size=50)

        self.uploading = self.__display_message("Uploading replay...", flat)
        self.uploadok = self.__display_message("Upload ok!", flat)
        self.uploaderror = self.__display_message("Upload error :(", flat)
        self.goal_time = pi3d.String(font=font, string=self.__get_time_since_last_goal(),
                                     is_3d=False, y=380, z=5)
        # scale text, because bigger font size creates weird artifacts
        self.goal_time.scale(2, 2, 1)
        self.goal_time.set_shader(flat)

        s = 512
        self.yCounter = Move(Counter(0, flat, 'y_', w=s, h=s, z=5))
        self.bCounter = Move(Counter(0, flat, 'b_', w=s, h=s, z=5))

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
        if ev.name == "upload_start":
            self.show_message(self.uploading)
        if ev.name == "upload_ok":
            self.show_message(self.uploadok)
        if ev.name == "upload_error":
            self.show_message(self.uploaderror)
        if ev.name == "button_event" and ev.data['btn'] != 'goal':
            self.instructions.show()

    def __set_bg(self):
        now = time.time()
        if now > (self.last_bg_change + self.bg_change_interval):
            self.last_bg_change = now
            self.bg_idx = (self.bg_idx + 1) % len(self.bg_textures)
            self.bg.set_textures([self.bg_textures[self.bg_idx]])

    def run(self):
        try:
            print("Running")
            while self.DISPLAY.loop_running():
                self.__set_bg()
                if not self.overlay_mode:
                    self.bg.draw()
                    self.instructions.draw()

                    for m in self.all_messages:
                        m.draw()

                    self.goal_time.draw()
                    self.goal_time.quick_change(self.__get_time_since_last_goal())

                self.logo.draw()
                self.yCounter.draw()
                self.bCounter.draw()

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
