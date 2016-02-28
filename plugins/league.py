#!/usr/bin/python3

import time
import logging
import json
import random
import os
import glob
import shutil

from foos.ui.ui import registerMenu
import config

logger = logging.getLogger(__name__)

league_results_dir = os.path.join(config.league_dir, 'results')
league_file = os.path.join(config.league_dir, 'league.json')
processed_dir = os.path.join(config.league_dir, 'processed')


class DiskBackend:
    def __init__(self):
        os.makedirs(league_results_dir, exist_ok=True)
        os.makedirs(processed_dir, exist_ok=True)

    def get_games(self):
        with open(league_file) as f:
            competition = json.load(f)
            return self.filter_played_games(competition)

    def write_games(self, competition):
        # avoid rewriting the same content
        if os.path.exists(league_file):
            with open(league_file) as f:
                if competition == json.load(f):
                    logger.info('Not writing league file')
                    return

        logger.info('Writing league file')
        tmpfile = league_file + "_tmp"
        with open(tmpfile, 'w') as f:
            json.dump(competition, f, indent=2)

        os.rename(tmpfile, league_file)

    def filter_played_games(self, competition):
        for div in competition:
            div['matches'] = [m for m in div['matches']
                              if not os.path.exists(self._get_result_file_for(m))]

        return competition

    def write_results(self, match):
        fname = self._get_result_file_for(match)
        with open(fname, 'w') as f:
            json.dump(match, f, indent=2)

    def get_result_files(self):
        pattern = os.path.join(league_results_dir, 'result_*.json')
        return glob.glob(pattern)

    def _get_result_file_for(self, match):
        return os.path.join(league_results_dir,
                            'result_%d.json' % match.get('id', random.randint(0, 10000)))

    def mark_result_as_processed(self, name):
        target = os.path.join(processed_dir, os.path.basename(name))
        shutil.move(name, target)

diskbackend = DiskBackend()


class Plugin:
    def __init__(self, bus):
        self.bus = bus
        self.bus.subscribe_map({"start_competition": self.start_competition,
                                "win_game": self.win_game,
                                "cancel_competition": self.cancel_competition},
                               thread=True)
        self.current_game = 0
        self.match = None
        self.backend = diskbackend
        registerMenu(self.get_menu_entries)

    def save(self):
        return {'match': self.match,
                'current_game': self.current_game}

    def load(self, state):
        self.current_game = state['current_game']
        self.match = state['match']
        if self.match:
            self.update_players()

    def update_players(self):
        g = self.match['submatches'][self.current_game]
        teams = {"yellow": g[0],
                 "black": g[1]}
        self.bus.notify("set_players", teams)

    def clear_players(self):
        teams = {"yellow": [], "black": []}
        self.bus.notify("set_players", teams)

    def start_competition(self, data):
        self.match = data
        self.match['start'] = int(time.time())
        self.current_game = 0
        self.bus.notify("reset_score")
        self.bus.notify("set_game_mode", {"mode": 5})
        self.update_players()

    def win_game(self, data):
        if self.match:
            rs = self.match.get('results', [])
            self.match['results'] = rs + [[data['yellow'], data['black']]]
            self.current_game += 1
            if self.current_game < len(self.match['submatches']):
                self.update_players()
            else:
                # small delay to allow other threads to process events
                time.sleep(0.2)
                self.bus.notify("end_competition", {'points': self.calc_points()})
                self.match['end'] = int(time.time())
                self.clear_players()
                self.backend.write_results(self.match)
                self.bus.notify("results_written")
                self.match = None

    def cancel_competition(self, data):
        self.match = None
        self.clear_players()

    def calc_points(self):
        players = self.match['players']
        points = dict([(p, 0) for p in players])
        for i, g in enumerate(self.match['submatches']):
            result = self.match['results'][i]
            wteam = 0 if result[0] > result[1] else 1
            for p in g[wteam]:
                points[p] = points.get(p, 0) + 1

        return points

    def get_menu_entries(self):
        def q(ev, data=None):
            def f():
                self.bus.notify(ev, data)
                self.bus.notify("menu_hide")
            return f

        if self.match:
            return [("Cancel official game", q("cancel_competition"))]
        else:
            try:
                comp = self.backend.get_games()
                menu = []
                for div in comp:
                    name, matches = div['name'], div['matches']
                    mmatches = []
                    for m in matches:
                        m['division'] = name
                        entry = "{:<14} {:<14} {:<14} {:<14}".format(*m['players'])
                        mmatches.append((entry, q('start_competition', m)))

                    mmatches.append(("", None))
                    mmatches.append(("« Back", None))

                    menu.append((name, mmatches))

                menu.append(("", None))
                menu.append(("« Back", None))

                return [("League", menu)]
            except Exception as e:
                logger.error(e)
                return []
