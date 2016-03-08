import config
from subprocess import call

class Plugin:
    def __init__(self, bus):
        self.bus = bus
        bus.subscribe_map({'replay_request': lambda d: self.replay('long', 'manual', {}),
                           'score_goal': lambda d: self.replay('short', 'goal', d)},
                          thread=True)

    def replay(self, replay_type, trigger, extra={}):
        extra['type'] = trigger

        if config.replay_enabled:
            call(["video/generate-replay.sh"])
            self.bus.notify('replay_start', extra)
            call(["video/replay-last.sh", replay_type])
            self.bus.notify('replay_end')
