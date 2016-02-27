#!/usr/bin/python3

import os
from collections import namedtuple
import logging

from foos.clock import Clock
from foos.bus import Bus, Event

State = namedtuple('State', ['yellow_goals', 'black_goals', 'last_goal'])
logger = logging.getLogger(__name__)


class Plugin:
    def __init__(self, bus):
        self.last_goal_clock = Clock('last_goal_clock')
        self.scores = {'black': 0, 'yellow': 0}
        self.bus = bus
        fmap = {'goal_event': lambda d: self.score(d['team']),
                'increment_score': lambda d: self.increment(d['team']),
                'decrement_score': lambda d: self.decrement(d['team']),
                'reset_score': lambda d: self.reset()}
        self.bus.subscribe_map(fmap, thread=True)

    def score(self, team):
        d = self.last_goal_clock.get_diff()
        if d and d <= 3:
            logger.info("Ignoring goal command %s happening too soon", team)
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

    def load(self, state):
        self.scores['yellow'] = state.yellow_goals
        self.scores['black'] = state.black_goals
        self.last_goal_clock.set(state.last_goal)
        self.pushState()

    def save(self):
        return State(self.scores['yellow'], self.scores['black'], self.last_goal())

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
