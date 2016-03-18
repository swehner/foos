#!/usr/bin/python
from __future__ import absolute_import, division, print_function, unicode_literals

import pi3d
from pi3d.constants import GL_LINEAR, GL_NEAREST, GL_LUMINANCE_ALPHA, GL_ALPHA
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
import logging
from functools import partial
from pi3d import opengles

from .anim import Move, Disappear, Wiggle, Delegate, ChangingTextures, ChangingText, Multiline
from .menu import Menu, MenuTree
from .OutlineFont import OutlineFont
import config
import itertools

media_path = ""
logger = logging.getLogger(__name__)
menuGenerators = []


def registerMenu(f):
    menuGenerators.append(f)


def img(filename):
    if os.path.isabs(filename):
        return filename
    else:
        return media_path + "/" + filename


def load_texture(filename, i_format=None, mipmap=False):
    return pi3d.Texture(img(filename), defer=False, free_after_load=True, i_format=i_format, mipmap=mipmap, filter=GL_LINEAR)


def load_bg(filename):
    return load_texture(filename)


def load_icon(filename):
    return load_texture(filename, i_format=GL_LUMINANCE_ALPHA)


class GuiState():
    def __init__(self, yScore=0, bScore=0, lastGoal=None):
        self.yScore = yScore
        self.bScore = bScore
        self.lastGoal = lastGoal


class Counter(Delegate):
    textures = None

    def __init__(self, value, shader, color, **kwargs):
        if Counter.textures is None:
            logger.info("Loading numbers")
            Counter.textures = [load_icon("numbers/%d.png" % (i))
                                for i in range(0, 10)]
        self.value = value
        self.disk = pi3d.shape.Disk.Disk(radius=(kwargs['w'] - 10) / 2, sides=6, rx=90)
        self.disk.set_material(color)
        self.number = Wiggle(pi3d.ImageSprite(Counter.textures[value], shader, **kwargs),
                             5, 10, 0.8)
        super().__init__(self.number)

    def draw(self):
        self.disk.draw()
        self.number.draw()

    def setValue(self, value):
        if self.value != value:
            self.value = value
            self.number.set_textures([Counter.textures[self.value % 10]])
            self.wiggle()

    def position(self, x, y, z):
        self.number.position(x, y, z)
        self.disk.position(x, y, z + 1)

    def scale(self, sx, sy, sz):
        self.number.scale(sx, sy, sz)
        # reorder due to initial rx=90 rotation
        self.disk.scale(sx, sz, sy)


class KeysFeedback:
    def __init__(self, shader):
        icon = pi3d.Sprite(w=256, h=256, z=50, y=-400)
        icon.set_shader(shader)
        upload = load_icon("icons/upload.png")
        replay = load_icon("icons/replay.png")
        self.icons = {"will_upload": (upload, {'alpha': 0.5}),
                      "will_replay": (replay, {'alpha': 0.5}),
                      "error": (load_icon("icons/error.png"), {'duration': 2}),
                      "ok": (load_icon("icons/ok.png"), {'duration': 1}),
                      "uploading": (upload, {'duration': 2}),
                      "unplugged": (load_icon("icons/unplugged.png"), {'duration': 1})}
        self.icon = Disappear(icon, duration=1, fade=0.5, alpha=1)

    def draw(self):
        self.icon.draw()

    def setIcon(self, i):
        if i:
            texture, params = self.icons[i]
            self.icon.set_textures([texture])
            self.icon.show(**params)
        else:
            self.icon.hide()


class Gui():
    def __init__(self, scaling_factor, fps, bus, show_leds=False, bg_change_interval=300, bg_amount=3):
        self.state = GuiState()
        self.overlay_mode = False
        self.bus = bus
        self.bus.subscribe_map(self.__event_map())
        self.bg_change_interval = bg_change_interval
        self.bg_amount = 1 if bg_change_interval == 0 else bg_amount
        self.show_leds = show_leds
        self.game_mode = None
        self.draw_menu = False
        self.countdown = None
        self.__init_display(scaling_factor, fps)
        self.__setup_menu()
        self.__setup_sprites()

    def __event_map(self):
        return {'quit': lambda d: self.stop(),
                'score_changed': lambda d: self.set_state(GuiState(d['yellow'], d['black'], d['last_goal'])),
                "button_will_upload": lambda d: self.feedback.setIcon("will_upload"),
                "button_will_replay": lambda d: self.feedback.setIcon("will_replay"),
                "upload_start": lambda d: self.feedback.setIcon("uploading"),
                "upload_ok": lambda d: self.feedback.setIcon("ok"),
                "upload_error": lambda d: self.feedback.setIcon("error"),
                "serial_disconnected": lambda d: self.feedback.setIcon("unplugged"),
                "button_event": lambda d: self.instructions.show(),
                "menu_down": lambda d: self.menu.down(),
                "menu_up": lambda d: self.menu.up(),
                "menu_select": lambda d: self.menu.select(),
                "set_game_mode": self.__set_game_mode,
                "movement_detected": lambda d: self.people.show(),
                "set_players": lambda d: self.setPlayers(d['black'], d['yellow'],
                                                         d.get('black_points', []), d.get('yellow_points', [])),
                "leds_enabled": partial(setattr, self, 'leds'),
                "replay_start": lambda d: self._handle_replay(True),
                "replay_end": lambda d: self._handle_replay(False),
                "menu_show": lambda d: self._handle_menu(True),
                "menu_hide": lambda d: self._handle_menu(False),
                "win_game": self._win_game,
                "countdown": lambda d: setattr(self, 'countdown', d['end_time']),
                "sudden_death": lambda d: setattr(self, 'countdown', 'Sudden death')}

    def __set_game_mode(self, d):
        self.game_mode = d["mode"]
        if d.get("timeout", None) is None:
            self.countdown = None

    def __setup_menu(self):
        self.main_menu = []
        for f in menuGenerators:
            elems = f()
            if len(elems) > 0:
                self.main_menu.extend(elems)
                self.main_menu.append(("", None))

        self.main_menu.append(("« Back", lambda: self.bus.notify("menu_hide")))

    def resetMenu(self):
        self.__setup_menu()
        self.menu.reset(self.main_menu)

    def __init_display(self, sf, fps):
        bgcolor = (0.0, 0.0, 0.0, 0.2)
        if sf == 0:
            #adapt to screen size
            self.DISPLAY = pi3d.Display.create(background=bgcolor, layer=1)
            sf = 1920 / self.DISPLAY.width
        else:
            logger.info("Forcing size")
            self.DISPLAY = pi3d.Display.create(x=0, y=0, w=int(1920 / sf), h=int(1080 / sf),
                                               background=bgcolor, layer=1)

        self.DISPLAY.frames_per_second = fps
        logger.info("Display %dx%d@%d", self.DISPLAY.width, self.DISPLAY.height, self.DISPLAY.frames_per_second)

        self.CAMERA = pi3d.Camera(is_3d=False, scale=1 / sf)
        opengles.glBlendFuncSeparate(pi3d.constants.GL_SRC_ALPHA, pi3d.constants.GL_ONE_MINUS_SRC_ALPHA, 1, pi3d.constants.GL_ONE_MINUS_SRC_ALPHA)

    def __move_sprites(self, now=None):
        if now is None:
            now = time.time()

        posz = 50
        if self.overlay_mode:
            posx = 800
            posy = 450
            scale = (0.2, 0.2, 1.0)
            self.yCounter.moveTo((posx - 65, posy, posz), scale)
            self.bCounter.moveTo((posx + 65, posy, posz), scale)
        else:
            scale = (1, 1, 1)
            self.yCounter.moveTo((-380, 0, posz), scale)
            self.bCounter.moveTo((380, 0, posz), scale)

    def __get_bg_textures(self):
        bgs = glob.glob(img("bg/*.jpg"))
        random.shuffle(bgs)
        bgs = bgs[0:self.bg_amount]

        logger.info("Loading %d bgs %s", len(bgs), bgs)
        return [load_bg(f) for f in bgs]

    def __setup_sprites(self):
        flat = pi3d.Shader("uv_flat")

        bg = pi3d.Sprite(w=1920, h=1080, z=100)
        bg.set_shader(flat)
        self.bg = ChangingTextures(bg, self.__get_bg_textures(), self.bg_change_interval)

        logger.info("Loading other images")
        logo_d = (80, 80)
        self.logo = pi3d.ImageSprite(load_icon("icons/logo.png"), flat, w=logo_d[0], h=logo_d[1],
                                     x=(1920 - logo_d[0]) / 2 - 40, y=(-1080 + logo_d[1]) / 2 + 40, z=50)
        self.people = Disappear(pi3d.ImageSprite(load_icon("icons/people.png"), flat, w=logo_d[0], h=logo_d[1],
                                                 x=(1920 - logo_d[0]) / 2 - 40 - logo_d[0] - 20, y=(-1080 + logo_d[1]) / 2 + 40, z=50),
                                duration=config.md_ev_interval + 1, fade=0.5)

        in_d = (512 * 0.75, 185 * 0.75)
        self.instructions = pi3d.ImageSprite(load_icon("icons/instructions.png"), flat, w=in_d[0], h=in_d[1],
                                             x=(-1920 + in_d[0]) / 2 + 40, y=(-1080 + in_d[1]) / 2 + 40, z=50)
        self.instructions = Disappear(self.instructions, duration=5)

        logger.info("Loading font")
        printable_cps = list(itertools.chain(range(ord(' '), ord('~')), range(161, 255), [ord("○"), ord("●"), ord("◌"), ord("◉"), ord('Ω')]))
        fontfile = img("UbuntuMono-B_circle.ttf")
        font = OutlineFont(fontfile, font_size=80, image_size=1024, outline_size=2,
                           codepoints=printable_cps, mipmap=False, filter=GL_LINEAR)
        self.goal_time = ChangingText(flat, font=font, string=self.__get_time_since_last_goal(),
                                      is_3d=False, justify='R', x=920, y=380, z=50)

        self.winner = Disappear(ChangingText(flat, font=font, string=self.__get_winner_string({}),
                                             is_3d=False, y=380, z=40), duration=10)

        self.game_mode_ui = ChangingText(flat, font=font, string=self.__get_mode_string(None),
                                         is_3d=False, justify='R', x=920, y=480, z=50)

        self.feedback = KeysFeedback(flat)

        s = 512
        self.yCounter = Move(Counter(0, flat, (10, 7, 0), w=s, h=s, z=50))
        self.bCounter = Move(Counter(0, flat, (0, 0, 0), w=s, h=s, z=50))
        playerfont = OutlineFont(fontfile, font_size=50, image_size=768, outline_size=2,
                                 codepoints=printable_cps, mipmap=False, filter=GL_LINEAR)
        self.yPlayers = Multiline(flat, font=playerfont, string=self.getPlayers(left=True),
                                  x=-380, y=-300, z=50, justify='C')
        self.bPlayers = Multiline(flat, font=playerfont, string=self.getPlayers(left=False),
                                  x=380, y=-300, z=50, justify='C')

        menufont = OutlineFont(fontfile, (255, 255, 255, 255), font_size=50, image_size=768,
                               codepoints=printable_cps, mipmap=False, filter=GL_LINEAR)
        arrow = load_icon("icons/arrow.png")
        menu = Menu(menufont, arrow, wchar=60, n=12, z=10)
        self.menu = MenuTree(self.main_menu, menu, rootTitle="Game mode")

        self.ledShapes = {
            "YD": pi3d.shape.Disk.Disk(radius=20, sides=12, x=-100, y=-430, z=0, rx=90),
            "YI": pi3d.shape.Disk.Disk(radius=20, sides=12, x=-100, y=-370, z=0, rx=90),
            "OK": pi3d.shape.Disk.Disk(radius=50, sides=12, x=0, y=-400, z=0, rx=90),
            "BD": pi3d.shape.Disk.Disk(radius=20, sides=12, x=100, y=-430, z=0, rx=90),
            "BI": pi3d.shape.Disk.Disk(radius=20, sides=12, x=100, y=-370, z=0, rx=90),
        }
        red = (10, 0, 0, 0)
        green = (0, 10, 0, 0)
        self.blackColor = (0, 0, 0, 0)
        self.ledColors = {"YD": red, "YI": green, "OK": green, "BD": red, "BI": green}
        self.leds = []
        # move immediately to position
        self.__move_sprites(0)

    def _win_game(self, data):
        self.winner.show()
        s = self.__get_winner_string(data)
        self.winner.quick_change(s)
        logger.info(s)

    def _handle_menu(self, show):
        self.draw_menu = show
        if show:
            self.resetMenu()
        self.bus.notify("menu_visible" if show else "menu_hidden", {})

    def _handle_replay(self, start):
        self.overlay_mode = start
        self.__move_sprites()
        if start:
            self.feedback.setIcon(None)

    def __get_winner_string(self, evdata):
        s = "Black wins  %d-%d" if evdata.get('team', None) == 'black' else "Yellow wins %d-%d"
        return (s % (evdata.get('yellow', 0), evdata.get('black', 0))).replace('0', 'O')

    def __get_mode_string(self, mode=None):
        if self.game_mode is None:
            mode = "  "
        else:
            mode = "»%d" % self.game_mode

        timestr = time.strftime("%H:%M", time.localtime()).replace("0", "O")

        return mode + " " + timestr

    def getPlayers(self, players=[], points=[], left=True):
        l = 20
        if len(players) == 0:
            players = ["", ""]
        if len(points) == 0:
            points = ["", ""]

        f = "{:<%d.%d} {}" % (l - len(points[0]), l - len(points[0]))
        p0 = f.format(players[0], points[0])
        p1 = f.format(players[1], points[1])
        return "%s\n%s" % (p0, p1)

    def setPlayers(self, black, yellow, black_points, yellow_points):
        self.yPlayers.quick_change(self.getPlayers(yellow, points=yellow_points, left=True))
        self.bPlayers.quick_change(self.getPlayers(black, points=black_points, left=False))

    def run(self):
        try:
            while self.DISPLAY.loop_running():
                if not self.overlay_mode:
                    self.bg.draw()
                    self.instructions.draw()

                    self.goal_time.quick_change(self.__get_time_since_last_goal())
                    self.goal_time.draw()
                    self.feedback.draw()

                self.logo.draw()
                self.people.draw()
                self.yCounter.draw()
                self.bCounter.draw()
                if not self.overlay_mode:
                    self.winner.draw()
                    self.game_mode_ui.quick_change(self.__get_mode_string())
                    self.game_mode_ui.draw()
                    self.yPlayers.draw()
                    self.bPlayers.draw()

                    if self.draw_menu:
                        self.menu.draw()

                if self.show_leds:
                    self.__draw_leds()

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
        if self.countdown:
            s = self.__get_countdown()
        else:
            if self.state.lastGoal:
                diff = time.time() - self.state.lastGoal
                fract = diff - int(diff)
                # replace 0 with O because of dots in 0 in the chosen font
                timestr = time.strftime("%M:%S", time.gmtime(diff)).replace("0", "O")
            else:
                timestr = "--:--"

            s = "LG %s" % timestr

        return "{:>15.15}".format(s)

    def __get_countdown(self):
        if isinstance(self.countdown, str):
            return self.countdown
        
        diff = max(self.countdown - time.time(), 0)
        # replace 0 with O because of dots in 0 in the chosen font
        timestr = time.strftime("%M:%S", time.gmtime(diff)).replace("0", "O")

        return "»Ω %s" % timestr

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
