import config
import os
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
            call(["video/generate-replay.sh", config.replay_path,
                  str(config.ignore_recent_chunks),
                  str(config.long_chunks), str(config.short_chunks)])
            self.bus.notify('replay_start', extra)
            call(["video/replay.sh", os.path.join(config.replay_path, "replay_{}.h264".format(replay_type))])
            self.bus.notify('replay_end')
