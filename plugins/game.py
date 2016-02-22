#!/usr/bin/python3

from threading import Thread
import time
import logging

from foos.bus import Bus, Event
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
        self.modes = [None, 3, 5]
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
            logger.info("Setting game mode %s", self.game_win_score)
            self.check_win_time = now + self.check_delay

    def check_win(self):
        if self.game_win_score:
            for t in ['yellow', 'black']:
                if self.current_score.get(t, 0) >= self.game_win_score:
                    d = {'team': t}
                    d.update(self.current_score)
                    self.bus.notify(Event('win_game', d))
                    self.bus.notify(Event('reset_score', d))

    def __run(self):
        while True:
            if self.check_win_time and time.time() > self.check_win_time:
                self.check_win_time = None
                self.check_win()

            time.sleep(0.1)

    def getMenuEntries(self):
        def q(ev):
            def f():
                self.bus.notify(ev)
                self.bus.notify(Event("menu_hide"))
            return f

        def check(string, mode):
            pre = "◌ "  # ◌○
            if mode == self.game_win_score:
                pre = "◉ "  # ◉●

            return pre + string

        return [(check("%d goals" % m if m else "Free mode", m),
                 q(Event("set_game_mode", {"mode": m})))
                for m in self.modes]

    def save(self):
        return self.game_win_score

    def load(self, game_win_score):
        self.bus.notify(Event("set_game_mode", {"mode": game_win_score}))
