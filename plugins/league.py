#!/usr/bin/python3

import time
import logging
import json
import random
import os
import requests
import glob
import threading
import shutil

from foos.bus import Bus, Event
from foos.ui.ui import registerMenu
import config

logger = logging.getLogger(__name__)


def flatten(x):
    if isinstance(x, list):
        for e in x:
            yield from flatten(e)
    else:
        yield x


class DiskBackend:
    def __init__(self):
        self.league_results_dir = os.path.join(config.league_dir, 'results')
        self.league_file = os.path.join(config.league_dir, 'league.json')
        os.makedirs(self.league_results_dir, exist_ok=True)

    def get_games(self):
        with open(self.league_file) as f:
            competition = json.load(f)
            return self.filterGames(competition)

    def write_games(self, competition):
        with open(self.league_file, 'w') as f:
            json.dump(competition, f)

    def filterGames(self, competition):
        for div in competition:
            div['matches'] = [m for m in div['matches']
                              if not os.path.exists(self._getResultFileFor(m))]

        return competition

    def write_results(self, match):
        fname = self._getResultFileFor(match)
        with open(fname, 'w') as f:
            json.dump(match, f, indent=2)

    def _getResultFileFor(self, match):
        return os.path.join(self.league_results_dir,
                            'result_%d.json' % match.get('id', random.randint(0, 10000)))


class APIBackend:
    def __init__(self):
        self.diskbe = DiskBackend()
        self.timeout = 1
        self.upload_url = config.league_upload_url
        self.games_url = config.league_games_url
        self.process_interval = 5
        self.processed_dir = os.path.join(config.league_dir, 'processed')
        self.league_results_dir = os.path.join(config.league_dir, 'results')

        self.lock = threading.Lock()

        os.makedirs(self.processed_dir, exist_ok=True)

        threading.Thread(daemon=True, target=self.retry_loop).start()

    def get_games(self):
        return self.diskbe.get_games()

    def request_games(self):
        try:
            r = requests.get(self.games_url, timeout=self.timeout)
            r.raise_for_status()
            competition = r.json()
            self.diskbe.write_games(competition)
            # load through diskbe to filter games
            return self.diskbe.get_games()
        except Exception as e:
            logger.error("API get games error: %s", e)

    def write_results(self, match):
        with self.lock:
            try:
                r = requests.post(self.upload_url, json=match, timeout=self.timeout)
                r.raise_for_status()
                # reload games from api
                self.request_games()
            except:
                # store and process later
                self.diskbe.write_results(match)
                logger.error("Syncing result failed - storing to disk...")

    def process_failures(self):
        with self.lock:
            pattern = os.path.join(self.league_results_dir, 'result_*.json')
            files = glob.glob(pattern)
            logger.info("Processing files %s", files)
            try:
                for fname in files:
                    with open(fname, 'r') as f:
                        r = requests.post(self.upload_url, json=json.load(f), timeout=self.timeout)
                    r.raise_for_status()

                # reload games from api
                self.request_games()

                # move all files to processed dir
                for fname in files:
                    shutil.move(fname, os.path.join(self.league_results_dir, 'processed'))
            except Exception as e:
                logger.error("Error processing results %s", e)

    def retry_loop(self):
        while True:
            time.sleep(self.process_interval)
            self.process_failures()


class Plugin:
    def __init__(self, bus):
        self.bus = bus
        self.bus.subscribe(self.process_event, thread=True)
        self.current_game = 0
        self.enabled = False
        self.match = {}
        self.backend = APIBackend()  # DiskBackend()
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
                self.backend.write_results(self.match)

        if ev.name == "cancel_competition":
            self.enabled = False
            self.clearPlayers()

    def calcPoints(self):
        players = self.match['players']
        points = dict(zip(players, [0] * len(players)))
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
                comp = self.backend.get_games()
                menu = []
                for div in comp:
                    name, matches = div['name'], div['matches']
                    mmatches = []
                    for m in matches:
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
