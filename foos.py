#!/usr/bin/python3

from gl.foos_gui import Gui
import os
import sys
import getopt
from subprocess import check_output, call

from iohandler.io_serial import IOSerial
from iohandler.io_debug import IODebug
from iohandler.io_keyboard import IOKeyboard
import config
from bus import Bus, Event

import hipbot
import uploader
import scoreboard
import ledcontroller
import soundcontroller
import buttoncontroller
import standby


def replay_handler(ev):
    regenerate = True
    manual = False
    if ev.name == 'score_goal':
        pass
    elif ev.name == 'replay_request':
        manual = True
    else:
        return

    if config.replay_enabled:
        bus.notify(Event('replay_start'))
        call(["./replay.sh", "manual" if manual else "auto", "true" if regenerate else "false"])
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
        sf = int(arg)

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/gl/")

bus = Bus()
gui = Gui(sf, frames, bus, show_leds=config.onscreen_leds_enabled,
          bg_change_interval=config.bg_change_secs)
bus.subscribe(replay_handler, thread=True)

hipbot.HipBot(bus)
soundcontroller.SoundController(bus)
scoreboard.ScoreBoard(bus)
uploader.Uploader(bus)
ledcontroller.LedController(bus)
standby.Standby(bus, config.standby_timeout_secs)

# IO
buttons = buttoncontroller.Buttons(bus)
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
