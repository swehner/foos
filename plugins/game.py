#!/usr/bin/python3

from threading import Thread
import time
import logging

from foos.ui.ui import registerMenu

logger = logging.getLogger(__name__)


class Plugin:
    def __init__(self, bus):
        self.bus = bus
        self.bus.subscribe(self.process_event, thread=True)
        self.game_win_score = None
        self.check_win_time = None
        self.check_delay = 2
        self.current_score = {}
        self.party_timeout = None
        self.game_end_time = None
        self.timeout_close_time = None
        self.sudden_death = False
        self.timeout_close_secs = 15
        self.modes = [(None, None), (3, None), (5, None), (3, 121), (3, 181), (3, 241)]

        # Turn off party mode after this time in sudden death
        self.party_mode_auto_off = 600
        registerMenu(self.getMenuEntries)
        Thread(target=self.__run, daemon=True).start()

    def process_event(self, ev):
        now = time.time()
        if ev.name == "score_changed":
            self.check_win_time = now + self.check_delay
            self.current_score = ev.data
        if ev.name == "replay_start":
            # wait for replay_end rather than checking it with a specific delay
            self.check_win_time = None
        if ev.name == "replay_end":
            self.check_win_time = now + self.check_delay
        if ev.name == "set_game_mode":
            self.game_win_score = ev.data["mode"]
            self.party_timeout = ev.data.get("timeout", None)
            logger.info("Setting game mode %s %s", self.game_win_score, self.party_timeout)
            self.check_win_time = now + self.check_delay
            self.reset()
        if ev.name == "score_reset":
            self.reset()

    def reset(self):
        if self.party_timeout:
            self.game_end_time = time.time() + self.party_timeout
            self.timeout_close_time = self.game_end_time - self.timeout_close_secs
            self.bus.notify("countdown", {"end_time": self.game_end_time})
        else:
            self.game_end_time = None
            self.timeout_close_time = None

        self.sudden_death = False

    def notifyWinner(self, t):
        d = {'team': t}
        d.update(self.current_score)
        self.bus.notify('win_game', d)
        self.bus.notify('reset_score', d)

    def check_win(self):
        if self.game_win_score:
            for t in ['yellow', 'black']:
                if self.current_score.get(t, 0) >= self.game_win_score:
                    self.notifyWinner(t)

    def check_party_win(self):
        ys = self.current_score['yellow']
        yb = self.current_score['black']
        if ys > yb:
            self.notifyWinner('yellow')
        elif yb > ys:
            self.notifyWinner('black')
        else:
            logger.info("Timeout - No one wins yet. Sudden death activated")
            self.sudden_death = True
            self.bus.notify("sudden_death")

    def __run(self):
        while True:
            now = time.time()
            if self.check_win_time and now > self.check_win_time:
                self.check_win_time = None
                if self.sudden_death:
                    self.check_party_win()
                else:
                    self.check_win()

            # check party mode
            if self.game_end_time and not self.sudden_death and now > max(self.game_end_time, self.check_win_time if self.check_win_time else 0):
                self.check_party_win()

            # check timeout close
            if self.timeout_close_time and now > self.timeout_close_time:
                self.bus.notify("timeout_close")
                self.timeout_close_time = None

            if self.sudden_death and now > self.game_end_time + self.party_mode_auto_off:
                logger.info("Automatically turning off party mode")
                self.bus.notify("set_game_mode", {"mode": self.game_win_score, "timeout": None})

            time.sleep(0.1)

    def getMenuEntries(self):
        def q(ev, ev_data):
            def f():
                self.bus.notify(ev, ev_data)
                self.bus.notify("menu_hide")
            return f

        def check(string, mode, party_timeout):
            pre = "○ "  # ◌○
            if mode == self.game_win_score and party_timeout == self.party_timeout:
                pre = "◉ "  # ◉●

            return pre + string

        def name(mode, party_timeout):
            if mode is None:
                return "Free mode"
            if party_timeout is not None:
                return "Party-mode: %d min %d goals" % (party_timeout / 60, mode)
            else:
                return "%d goals" % mode

        return [(check(name(m, p), m, p),
                 q("set_game_mode", {"mode": m, "timeout": p}))
                for m, p in self.modes]

    def save(self):
        return (self.game_win_score, self.party_timeout)

    def load(self, p):
        game_win_score, timeout = p
        self.bus.notify("set_game_mode", {"mode": game_win_score, "timeout": timeout})
