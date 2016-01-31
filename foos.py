#!/usr/bin/env python3

import sys
import getopt
import os
from subprocess import check_output, call

from foos.ui import ui
from foos.iohandler.io_serial import IOSerial
from foos.iohandler.io_debug import IODebug
from foos.iohandler.io_keyboard import IOKeyboard
import config
from foos.bus import Bus, Event

from foos import hipbot
from foos import uploader
from foos import scoreboard, ledcontroller, soundcontroller, buttoncontroller, standby, game


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
sounds_dir = root + "/sounds"
ui.media_path = root + "/img"

bus = Bus()
gui = ui.Gui(sf, frames, bus, show_leds=config.onscreen_leds_enabled,
             bg_change_interval=config.bg_change_secs,
             bg_amount=config.bg_amount)
bus.subscribe(replay_handler, thread=True)

hipbot.HipBot(bus)
soundcontroller.SoundController(bus, sounds_dir)
scoreboard.ScoreBoard(bus)
uploader.Uploader(bus)
ledcontroller.LedController(bus)
standby.Standby(bus, config.standby_timeout_secs)
game.Game(bus)

# IO
buttoncontroller.GameButtons(bus, long_press_delay=0.6)
buttoncontroller.MenuButtons(bus, long_press_delay=0.3, enabled=False)
if config.serial_enabled:
    serial = IOSerial(bus)
IODebug(bus)

if gui.is_x11():
    print("Running Keyboard")
    IOKeyboard(bus)

# Run main gui main loop
print("Run GUI")
gui.run()
gui.cleanup()
