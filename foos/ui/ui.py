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
import fractions
from functools import partial
from pi3d import opengles

from .anim import Move, Disappear, Wiggle, Delegate, ChangingTextures, ChangingText, Multiline, Flashing
from .menu import Menu, MenuTree
from .OutlineFont import OutlineFont
from .FixedOutlineString import FixedOutlineString
import config
import itertools

media_path = ""
logger = logging.getLogger(__name__)
menuGenerators = []
flash_yellow = (0.2, 0.15, -0.3)
flash_red = (0.2, -0.3, -0.3)
flash_black = (-0.2, -0.2, -0.2)


def registerMenu(f):
    menuGenerators.append(f)


def img(filename):
    if os.path.isabs(filename):
        return filename
    else:
        return media_path + "/" + filename


def load_texture(filename, i_format=None, mipmap=False, fallback=None):
    f = img(filename)
    if fallback is not None and not os.path.exists(f):
        f = img(fallback)
    return pi3d.Texture(f, defer=False, free_after_load=True, i_format=i_format, mipmap=mipmap, filter=GL_LINEAR)


def load_bg(filename):
    return load_texture(filename)


def load_icon(filename, fallback=None):
    return load_texture(filename, i_format=GL_LUMINANCE_ALPHA, fallback=fallback)


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
        self.override = None
        self.last_shown = None
        super().__init__(self.number)

    def draw(self):
        v = self.getFaceValue()
        if v != self.last_shown:
            self.last_shown = v
            self.number.set_textures([Counter.textures[v % 10]])
            self.wiggle()

        self.disk.draw()
        self.number.draw()

    def getFaceValue(self):
        if self.override is None:
            return self.value
        else:
            return self.override

    def setValue(self, value):
        self.value = value

    def setOverride(self, value):
        self.override = value

    def position(self, x, y, z):
        self.number.position(x, y, z)
        self.disk.position(x, y, z + 1)

    def scale(self, sx, sy, sz):
        self.number.scale(sx, sy, sz)
        # reorder due to initial rx=90 rotation
        self.disk.scale(sx, sz, sy)


class LazyTrigger(Delegate):
    def __init__(self, sprite, min=2):
        super().__init__(sprite)
        self.__last_time = time.time()
        self.value = 0
        self.min = min

    def draw(self):
        # decrement counter
        now = time.time()
        self.value = max(0, self.value - (time.time() - self.__last_time))
        self.__last_time = now
        self.delegate.draw()

    def show(self):
        self.value += 1
        if (self.value >= self.min):
            self.delegate.show()
            self.value = 0


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


class WinnerString:
    def __init__(self, shader, teams=["yellow", "black"]):
        font = img("Ubuntu-B.ttf")
        duration = 5
        drop_duration = 0.2
        self.shapes = {}
        for team in teams:
            s = FixedOutlineString(font, "{} wins!".format(team.capitalize()), outline_size=2, font_size=180, shader=shader)
            s = Move(Disappear(s.sprite, duration=duration), duration=drop_duration)
            self.shapes[team] = s

    def draw(self):
        for team, s in self.shapes.items():
            s.draw()

    def show_winner(self, team):
        for t, s in self.shapes.items():
            if team == t:
                s.position(0, 650, 40)
                s.moveTo((0, 330, 40), (1, 1, 1))
                s.show()
            else:
                s.hide()


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
        self.schedules = []

    def __event_map(self):
        evnt = {'quit': lambda d: self.stop(),
                'score_changed': lambda d: self.set_state(GuiState(d['yellow'], d['black'], d['last_goal'])),
                "button_will_upload": lambda d: self.feedback.setIcon("will_upload"),
                "button_will_replay": lambda d: self.feedback.setIcon("will_replay"),
                "upload_start": lambda d: self.feedback.setIcon("uploading"),
                "upload_ok": lambda d: self.feedback.setIcon("ok"),
                "upload_error": lambda d: self.feedback.setIcon("error"),
                "serial_disconnected": lambda d: self.feedback.setIcon("unplugged"),
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
                "sudden_death": self.__sudden_death,
                "timeout_close": lambda x: self.bg.flash(speed=1, times=0.5, color=flash_yellow, color2=flash_black)}

        if config.show_instructions:
            evnt["increment_score"] = lambda d: self.instructions.show()
            evnt["decrement_score"] = lambda d: self.instructions.show()

        return evnt

    def __sudden_death(self, d):
        self.countdown = '» Sudden death «'
        self.bg.flash(speed=1, times=0.5, color=flash_red, color2=flash_black)

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
            aspect = fractions.Fraction(self.DISPLAY.width, self.DISPLAY.height)
            if aspect != fractions.Fraction(16, 9):
                logger.warn("Your display aspect ratio is %s instead of 16/9 expect some black bars", aspect)
            sf = 1920 / self.DISPLAY.width
        else:
            logger.info("Forcing size")
            self.DISPLAY = pi3d.Display.create(x=0, y=0, w=int(1920 / sf), h=int(1080 / sf),
                                               background=bgcolor, layer=1)

        self.DISPLAY.frames_per_second = fps
        logger.info("Display %dx%d@%d", self.DISPLAY.width, self.DISPLAY.height, self.DISPLAY.frames_per_second)

        self.CAMERA = pi3d.Camera(is_3d=False, scale=1 / sf)
        opengles.glBlendFuncSeparate(pi3d.constants.GL_SRC_ALPHA, pi3d.constants.GL_ONE_MINUS_SRC_ALPHA, 1, pi3d.constants.GL_ONE_MINUS_SRC_ALPHA)

    def __move_sprites(self):
        posz = 50
        if self.overlay_mode:
            posx = 800
            posy = 450
            scale = (0.2, 0.2, 1.0)
            self.yCounter.moveTo((posx - 65, posy, posz), scale)
            self.bCounter.moveTo((posx + 65, posy, posz), scale)
        else:
            scale = (1, 1, 1)
            self.yCounter.moveTo((-380, 50, posz), scale)
            self.bCounter.moveTo((380, 50, posz), scale)

    def __move_winner(self):
        scale = (0.75, 0.75, 0.75)
        self.yCounter.moveTo((-300, 0, 50), scale)
        self.bCounter.moveTo((300, 0, 50), scale)

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
        self.bg = Flashing(ChangingTextures(bg, self.__get_bg_textures(), self.bg_change_interval))

        logger.info("Loading other images")
        logo_d = (80, 80)
        self.logo = pi3d.ImageSprite(load_icon("icons/logo.png", fallback="icons/logo_fallback.png"), flat, w=logo_d[0], h=logo_d[1],
                                     x=(1920 - logo_d[0]) / 2 - 40, y=(-1080 + logo_d[1]) / 2 + 40, z=50)
        self.people = Disappear(pi3d.ImageSprite(load_icon("icons/people.png"), flat, w=logo_d[0], h=logo_d[1],
                                                 x=(1920 - logo_d[0]) / 2 - 40 - logo_d[0] - 20, y=(-1080 + logo_d[1]) / 2 + 40, z=50),
                                duration=config.md_ev_interval + 1, fade=0.5)

        in_d = (512 * 0.75, 185 * 0.75)
        self.instructions = pi3d.ImageSprite(load_icon("icons/instructions.png"), flat, w=in_d[0], h=in_d[1],
                                             x=(-1920 + in_d[0]) / 2 + 40, y=(-1080 + in_d[1]) / 2 + 40, z=50)
        self.instructions = LazyTrigger(Disappear(self.instructions, duration=5))

        logger.info("Loading font")
        printable_cps = list(itertools.chain(range(ord(' '), ord('~')), range(161, 255), [ord("○"), ord("●"), ord("◌"), ord("◉"), ord('Ω')]))
        fontfile = img("UbuntuMono-B_circle.ttf")
        font = OutlineFont(fontfile, font_size=80, image_size=1024, outline_size=2,
                           codepoints=printable_cps, mipmap=False, filter=GL_LINEAR)
        self.goal_time = ChangingText(flat, font=font, string=self.__get_time_since_last_goal(),
                                      is_3d=False, justify='C', x=0, y=-450, z=50)

        self.game_mode_ui = ChangingText(flat, font=font, string=self.__get_mode_string(None),
                                         is_3d=False, justify='R', x=920, y=480, z=50)

        self.feedback = KeysFeedback(flat)

        s = 512
        self.yCounter = Move(Counter(0, flat, (10, 7, 0), w=s, h=s, z=50))
        self.bCounter = Move(Counter(0, flat, (0, 0, 0), w=s, h=s, z=50))
        playerfont = OutlineFont(fontfile, font_size=50, image_size=768, outline_size=2,
                                 codepoints=printable_cps, mipmap=False, filter=GL_LINEAR)
        self.yPlayers = Multiline(flat, font=playerfont, string=self.getPlayers(left=True),
                                  x=-380, y=-250, z=50, justify='C')
        self.bPlayers = Multiline(flat, font=playerfont, string=self.getPlayers(left=False),
                                  x=380, y=-250, z=50, justify='C')

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

        self.winner = WinnerString(flat)
        # move immediately to position
        self.__move_sprites()

    def _win_game(self, data):
        self.schedule(time.time() + 5, self._reset_winner, True)
        self.winner.show_winner(data['team'])
        self.yCounter.setOverride(data['yellow'])
        self.bCounter.setOverride(data['black'])
        self.__move_winner()

        if self.countdown:
            self.bg.flash(speed=3, times=2.5, color=flash_red, color2=flash_black)

        logger.info("Wins: {team} {yellow}-{black}".format(**data))

    def _reset_winner(self):
        self.__move_sprites()
        self.yCounter.setOverride(None)
        self.bCounter.setOverride(None)

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
        else:
            self.bg.encourage_change()

    def __get_mode_string(self, mode=None):
        l = 20
        mode = ""
        if self.game_mode is not None:
            mode = "»%d" % self.game_mode

        if self.countdown is not None:
            mode = "Party! " + mode

        timestr = time.strftime("%H:%M", time.localtime()).replace("0", "O")

        return (mode + " " + timestr).rjust(l)

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

    def schedule(self, when, fun, unique=False):
        if unique:
            self.schedules = list(filter(lambda x: x[1]!=fun, self.schedules))

        self.schedules.append((when, fun))

    def checkSchedules(self):
        if len(self.schedules) > 0:
            now = time.time()
            to_run = [(t, fun) for t, fun in self.schedules if t <= now]
            for t, fun in to_run:
                fun()
                self.schedules.remove((t, fun))

    def run(self):
        try:
            while self.DISPLAY.loop_running():
                self.checkSchedules()

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

    def __as_time(self, secs):
        if secs:
            mins = (secs / 60) % 60
            secs = secs % 60
            frac = (secs - int(secs)) * 10
            # replace 0 with O because of dots in 0 in the chosen font
            return ("%.2d:%.2d.%.1d" % (mins, secs, frac)).replace("0", "O")
        else:
            return "--:--.-"

    def __get_time_since_last_goal(self):
        if self.countdown:
            s = self.__get_countdown()
        else:
            diff = None
            if self.state.lastGoal:
                diff = time.time() - self.state.lastGoal
                fract = diff - int(diff)

            s = "LG: %s" % self.__as_time(diff)

        return "{:^16.16}".format(s)

    def __get_countdown(self):
        if isinstance(self.countdown, str):
            return self.countdown

        diff = max(self.countdown - time.time(), 0)

        return "» %s «" % self.__as_time(diff)

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

    def is_pi(self):
        return pi3d.PLATFORM == pi3d.PLATFORM_PI


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
