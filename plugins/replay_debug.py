import config
import os
from subprocess import call
import time


class Plugin:
    """Dummy plugin that sleeps to simulate replays used for dev"""
    def __init__(self, bus):
        self.bus = bus
        bus.subscribe_map({'replay_request': lambda d: self.replay('long', 'manual', {}),
                           'score_goal': lambda d: self.replay('short', 'goal', d)},
                          thread=True)

    def replay(self, replay_type, trigger, extra={}):
        extra['type'] = trigger

        self.bus.notify('replay_start', extra)
        time.sleep(2)
        self.bus.notify('replay_end')
