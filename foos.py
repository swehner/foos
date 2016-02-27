#!/usr/bin/env python3

import logging.config

logging.config.fileConfig('log.ini')
logger = logging.getLogger(__name__)

import sys
import getopt
import os
from subprocess import call

from foos.ui import ui
import plugins.io_keyboard
import config
from foos.bus import Bus, Event
from foos.plugin_handler import PluginHandler


class ReplayHandler:
    def __init__(self, bus):
        bus.subscribe_map({'replay_request': lambda d: self.replay('long', 'manual', {}),
                           'score_goal': lambda d: self.replay('short', 'goal', d)},
                          thread=True)

    def replay(self, replay_type, trigger, extra={}):
        extra['type'] = trigger

        if config.replay_enabled:
            call(["video/generate-replay.sh"])
            bus.notify(Event('replay_start', extra))
            call(["video/replay-last.sh", replay_type])
            bus.notify(Event('replay_end'))

try:
    opts, args = getopt.getopt(sys.argv[1:], "s:f:")
except getopt.GetoptError:
    print('usage: ./foos.py [-sf]')
    print('-s: scale')
    print('-f: framerate (default: 25)')
    sys.exit(2)

sf = 0
frames = 25
for opt, arg in opts:
    if opt == '-f':
        frames = int(arg)
    if opt == '-s':
        sf = float(arg)

root = os.path.abspath(os.path.dirname(__file__))
ui.media_path = root + "/img"

bus = Bus()
gui = ui.Gui(sf, frames, bus, show_leds=config.onscreen_leds_enabled,
             bg_change_interval=config.bg_change_secs,
             bg_amount=config.bg_amount)
ReplayHandler(bus)

if gui.is_x11():
    logger.info("Running Keyboard")
    plugins.io_keyboard.Plugin(bus)

# Load plugins
PluginHandler(bus)

# Run main gui main loop
logger.info("Run GUI")
gui.run()
gui.cleanup()
