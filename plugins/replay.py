import foos.config as config
import os
import time

from foos.process import call_and_log
from foos.platform import is_pi
from shutil import copyfile

class Plugin:
    def __init__(self, bus):
        self.bus = bus
        bus.subscribe_map({'replay_request': lambda d: self.replay('long', 'manual', {}),
                           'score_goal': lambda d: self.replay('short', 'goal', d)},
                          thread=True)

    def replay(self, replay_type, trigger, extra={}):
        extra['type'] = trigger

        call_and_log(["video/generate-replay.sh", config.replay_path,
              str(config.ignore_recent_chunks),
              str(config.long_chunks), str(config.short_chunks)])

        # If we want to keep replays, make a copy of the files with a timestamp.
        if config.save_replays == True:
            copyfile(os.path.join(config.replay_save_path, "replay_short.h264"),
                     os.path.join(config.replay_save_path, "{}_replay_short.h264".format(int(time.time()))))
            copyfile(os.path.join(config.replay_save_path, "replay_long.h264"),
                     os.path.join(config.replay_save_path, "{}_replay_long.h264".format(int(time.time()))))
            
        self.bus.notify('replay_start', extra)
        if is_pi():
            call_and_log(["video/replay.sh", os.path.join(config.replay_path, "replay_{}.h264".format(replay_type)), str(config.replay_fps)])
        else:
            time.sleep(3)
            
        self.bus.notify('replay_end')
