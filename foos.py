#!/usr/bin/env python3

import logging.config

logging.config.fileConfig('log.ini')
logger = logging.getLogger(__name__)

import sys
import getopt
import os
from subprocess import check_output, call

from foos.ui import ui
import plugins.io_keyboard
import config
from foos.bus import Bus, Event
from foos.plugin_handler import PluginHandler



def replay_handler(ev):
    replay_type = 'short'
    if ev.name == 'score_goal':
        pass
    elif ev.name == 'replay_request':
        replay_type = 'long'
    else:
        return

    if config.replay_enabled:
        call(["video/generate-replay.sh"])
        bus.notify(Event('replay_start'))
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
bus.subscribe(replay_handler, thread=True)

if gui.is_x11():
    logger.info("Running Keyboard")
    plugins.io_keyboard.IOKeyboard(bus)

# Load plugins
PluginHandler(bus)

# Run main gui main loop
logger.info("Run GUI")
gui.run()
gui.cleanup()
