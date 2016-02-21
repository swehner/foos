#!/usr/bin/python3

import time
import logging
import json

from foos.bus import Bus, Event
from foos.ui.ui import registerMenu
import config
import random
import os
logger = logging.getLogger(__name__)


def flatten(x):
    if isinstance(x, list):
        for e in x:
            yield from flatten(e)
    else:
        yield x


class Plugin:
    def __init__(self, bus):
        self.bus = bus
        self.bus.subscribe(self.process_event, thread=True)
        self.games = []
        self.current_game = 0
        self.enabled = False
        self.points = {}
        self.teams = {}
        self.match = {}
        registerMenu(self.getMenuEntries)

    def setPlayers(self):
        g = self.games[self.current_game]
        self.teams = {"yellow": g[0],
                      "black": g[1]}
        self.bus.notify(Event("set_players", self.teams))

    def clearPlayers(self):
        self.teams = {"yellow": [], "black": []}
        self.bus.notify(Event("set_players", self.teams))

    def process_event(self, ev):
        now = time.time()
        if ev.name == "start_competition":
            p = ev.data['players']
            self.points = dict([(e, 0) for e in p])
            self.games = ev.data['submatches']
            self.match = ev.data
            self.match['start'] = int(time.time())
            self.current_game = 0
            self.enabled = True
            self.bus.notify(Event("reset_score"))
            self.bus.notify(Event("set_game_mode", {"mode": 5}))
            self.setPlayers()

        if ev.name == "win_game" and self.enabled:
            self.calcPoints(ev.data['team'])
            rs = self.match.get('results', [])
            self.match['results'] = rs + [[ev.data['yellow'], ev.data['black']]]
            self.current_game += 1
            if self.current_game < len(self.games):
                self.setPlayers()
            else:
                self.bus.notify(Event("end_competition", {'points': self.points}))
                self.match['end'] = int(time.time())
                self.enabled = False
                self.clearPlayers()
                self.writeResults()

        if ev.name == "cancel_competition":
            self.enabled = False
            self.clearPlayers()

    def _getResultFileFor(self, match):
        return os.path.join(config.league_results_dir,
                            'result_%d.json' % match.get('id', random.randint(0, 1000000)))

    def writeResults(self):
        try:
            os.makedirs(config.league_results_dir)
        except FileExistsError:
            pass

        fname = self._getResultFileFor(self.match)
        with open(fname, 'w') as f:
            json.dump(self.match, f, indent=2)

    def calcPoints(self, team):
        for p in self.teams.get(team, []):
            self.points[p] = self.points[p] + 1

    def getMenuEntries(self):
        def q(ev):
            def f():
                self.bus.notify(ev)
                self.bus.notify(Event("menu_hide"))
            return f

        if self.enabled:
            return [("Cancel official game", q(Event("cancel_competition")))]
        else:
            try:
                with open(config.league_file) as f:
                    comp = json.load(f)
                    menu = []
                    for div in comp:
                        name, matches = div['name'], div['matches']
                        mmatches = []
                        for m in matches:
                            if 'id' in m:
                                # skip match if a result already exists for it
                                if os.path.exists(self._getResultFileFor(m)):
                                    continue

                            players = list(set(flatten(m['submatches'])))
                            m['players'] = players
                            m['division'] = name
                            ev = Event('start_competition', m)
                            entry = "{:<14} {:<14} {:<14} {:<14}".format(*players)
                            mmatches.append((entry, q(ev)))

                        mmatches.append(("", None))
                        mmatches.append(("« Back", None))

                        menu.append((name, mmatches))

                    menu.append(("", None))
                    menu.append(("« Back", None))

                    return [("League", menu)]
            except Exception as e:
                logger.error(e)
                return []
