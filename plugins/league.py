#!/usr/bin/python3

import time
import logging
import json

from foos.bus import Bus, Event
from foos.ui.ui import registerMenu
import config
logger = logging.getLogger(__name__)


class Plugin:
    def __init__(self, bus):
        self.bus = bus
        self.bus.subscribe(self.process_event, thread=True)
        self.games = []
        self.current_game = 0
        self.enabled = False
        registerMenu(self.getMenuEntries)

    def setPlayers(self):
        g = self.games[self.current_game]
        self.bus.notify(Event("set_players", {"yellow": [g[0], g[1]],
                                              "black": [g[2], g[3]]}))

    def clearPlayers(self):
        self.bus.notify(Event("set_players", {"yellow": [],
                                              "black": []}))

    def process_event(self, ev):
        now = time.time()
        if ev.name == "start_competition":
            p = ev.data['players']
            # games is the full combination of players
            self.games = [p, [p[0], p[2], p[1], p[3]], [p[0], p[3], p[1], p[2]]]
            self.current_game = 0
            self.enabled = True
            self.bus.notify(Event("reset_score"))
            self.bus.notify(Event("set_game_mode", {"mode": 5}))
            self.setPlayers()

        if ev.name == "win_game" and self.enabled:
            self.current_game += 1
            if self.current_game < len(self.games):
                self.setPlayers()
            else:
                self.enabled = False
                self.clearPlayers()

    def getMenuEntries(self):
        def q(ev):
            def f():
                self.bus.notify(ev)
                self.bus.notify(Event("menu_hide"))
            return f

        try:
            with open(config.league_file) as f:
                comp = json.load(f)
                menu = []
                for div in comp:
                    name, games = div[0], div[1]
                    mgames = []
                    for g in games:
                        ev = Event('start_competition', {"players": g})
                        mgames.append((", ".join(g), q(ev)))

                    menu.append((name, mgames))

                return [("League", menu)]
        except Exception as e:
            logger.error(e)
            return []
