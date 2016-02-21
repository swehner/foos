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
        self.current_game = 0
        self.enabled = False
        self.match = {}
        registerMenu(self.getMenuEntries)

    def save(self):
        return {'match': self.match,
                'current_game': self.current_game,
                'enabled': self.enabled}

    def load(self, state):
        self.current_game = state['current_game']
        self.match = state['match']
        self.enabled = state['enabled']
        if self.enabled:
            self.setPlayers()

    def setPlayers(self):
        g = self.match['submatches'][self.current_game]
        teams = {"yellow": g[0],
                 "black": g[1]}
        self.bus.notify(Event("set_players", teams))

    def clearPlayers(self):
        teams = {"yellow": [], "black": []}
        self.bus.notify(Event("set_players", teams))

    def process_event(self, ev):
        now = time.time()
        if ev.name == "start_competition":
            p = ev.data['players']
            self.points = dict([(e, 0) for e in p])
            self.match = ev.data
            self.match['start'] = int(time.time())
            self.current_game = 0
            self.enabled = True
            self.bus.notify(Event("reset_score"))
            self.bus.notify(Event("set_game_mode", {"mode": 5}))
            self.setPlayers()

        if ev.name == "win_game" and self.enabled:
            rs = self.match.get('results', [])
            self.match['results'] = rs + [[ev.data['yellow'], ev.data['black']]]
            self.current_game += 1
            if self.current_game < len(self.match['submatches']):
                self.setPlayers()
            else:
                self.bus.notify(Event("end_competition", {'points': self.calcPoints()}))
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

    def calcPoints(self):
        points = {}
        for i, g in enumerate(self.match['submatches']):
            result = self.match['results'][i]
            wteam = 0 if result[0] > result[1] else 1
            for p in g[wteam]:
                points[p] = points.get(p, 0) + 1

        return points

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
