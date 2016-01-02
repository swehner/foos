#!/usr/bin/python3

import os
import atexit
import pickle
from collections import namedtuple
import traceback

from clock import Clock
from bus import Bus, Event

State = namedtuple('State', ['yellow_goals', 'black_goals', 'last_goal'])


class ScoreBoard:
    status_file = '.status'

    def __init__(self, bus):
        # Register save status on exit
        atexit.register(self.save_info)
        self.last_goal_clock = Clock('last_goal_clock')
        self.scores = {'black': 0, 'yellow': 0}
        self.bus = bus
        self.bus.subscribe(self.process_event, thread=True)
        if not self.__load_info():
            self.reset()

    def score(self, team):
        d = self.last_goal_clock.get_diff()
        if d and d <= 3:
            print("Ignoring goal command {} happening too soon".format(team))
            return

        self.last_goal_clock.reset()
        self.increment(team)
        data = self.__get_event_data()
        data['team'] = team
        self.bus.notify(Event('score_goal', data))

    def increment(self, team):
        s = self.scores.get(team, 0)
        self.scores[team] = (s + 1) % 10
        self.pushState()

    def decrement(self, team):
        s = self.scores.get(team, 0)
        self.scores[team] = max(s - 1, 0)
        self.pushState()

    def __load_info(self):
        loaded = False
        try:
            if os.path.isfile(self.status_file):
                with open(self.status_file, 'rb') as f:
                    state = pickle.load(f)
                    self.scores['yellow'] = state.yellow_goals
                    self.scores['black'] = state.black_goals
                    self.last_goal_clock.set(state.last_goal)
                    self.pushState()
                    loaded = True
        except:
            print("State loading failed")
            traceback.print_exc()

        return loaded

    def save_info(self):
        state = State(self.scores['yellow'], self.scores['black'], self.last_goal())
        with open(self.status_file, 'wb') as f:
            pickle.dump(state, f)

    def reset(self):
        self.scores = {'black': 0, 'yellow': 0}
        self.last_goal_clock.reset()
        self.bus.notify(Event('score_reset', self.__get_event_data()))
        self.pushState()

    def last_goal(self):
        return self.last_goal_clock.get()

    def __get_event_data(self):
        return {'yellow': self.scores['yellow'],
                'black': self.scores['black'],
                'last_goal': self.last_goal()}

    def pushState(self):
        self.bus.notify(Event("score_changed", self.__get_event_data()))

    def process_event(self, ev):
        if ev.name == 'button_event' and ev.data['btn'] == 'goal':
            # process goals
            self.score(ev.data['team'])
        if ev.name == 'increment_score':
            self.increment(ev.data['team'])
        if ev.name == 'decrement_score':
            self.decrement(ev.data['team'])
        if ev.name == 'reset_score':
            self.reset()
