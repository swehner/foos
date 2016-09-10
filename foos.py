#!/usr/bin/env python3
__version__ = 20160814

import foos.config as config

import logging.config
import sys
import getopt
import os

from foos.platform import is_x11
from foos.ui import ui
import plugins.io_keyboard
from foos.bus import Bus
from foos.plugin_handler import PluginHandler


logging.config.dictConfig(config.log)
logger = logging.getLogger(__name__)
logger.info("Foos v%s starting", __version__)

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
             bg_change_interval=config.bg_change_secs)

if is_x11():
    logger.info("Running Keyboard")
    plugins.io_keyboard.Plugin(bus)

# Load plugins
PluginHandler(bus)

# Run main gui main loop
logger.info("Run GUI")
gui.run()
gui.cleanup()
