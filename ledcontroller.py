#!/usr/bin/env python
import time
import sys
import threading
import queue
import collections
from bus import Event, Bus

class Pattern:
    def __init__(self, time, leds=[]):
        self.time = time
        self.leds = leds


def flatten(l):
    for el in l:
        if isinstance(el, collections.Iterable):
            for sub in flatten(el):
                yield sub
        else:
            yield el


class LedController:
    def __init__(self, bus):
        self.queue = queue.Queue()
        self.bus = bus
        self.bus.subscribe(self.process_event)
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()

    def run(self):
        while True:
            loop, m = self.queue.get()
            first = True
            while first or loop:
                first = False
                for p in flatten(m):
                    if self.__canRun():
                        self.setLeds(p.leds)
                        self.__safeSleep(p.time)
                    else:
                        loop = False
                        break

            #reset leds
            self.setLeds()

    def __safeSleep(self, t):
        start = time.time()
        while (time.time() < start + t) and self.__canRun():
            time.sleep(0.05)

    def __canRun(self):
        return self.queue.empty()

    def setLeds(self, leds=[]):
        self.bus.notify(Event("leds_enabled", leds))

    def setMode(self, mode, loop=False):
        self.stop = True
        self.queue.put((loop, mode))

    def process_event(self, ev):
        if ev.name == 'score_goal':
            self.setMode(pat_goal)
        if ev.name == 'upload_ok':
            self.setMode(pat_ok)
        if ev.name == 'leds_mode':
            self.setMode(ev.data)
        # all error conditions
        if ev.name in ['upload_error']:
            self.setMode(pat_error)

pat_reset = 3 * [Pattern(0.2, ["BI", "BD", "YI", "YD"]),
                 Pattern(0.1),
                 Pattern(0.2, ["BI", "BD", "YI", "YD"]),
                 Pattern(1)]

pat_poweredoff = [Pattern(0.5, ["OK"]),
                  Pattern(1)]

pat_goal = [[Pattern(0.1, ["BD", "YD"]),
             Pattern(0.1, ["OK"]),
             Pattern(0.1, ["BI", "YI"])],
            3 * [Pattern(0.1),
                 Pattern(0.1, ["BI", "BD", "OK", "YI", "YD"])]]

pat_ok = [Pattern(0.3, ["OK"])]

pat_error = 2 * [Pattern(0.3, ["YD", "BD"]),
                 Pattern(0.3)]

pat_demo = [Pattern(1, ["BD"]),
            Pattern(1, ["BI"]),
            Pattern(1, ["YD"]),
            Pattern(1, ["YI"]),
            Pattern(1, ["OK"])]


if __name__ == "__main__":
    def write_data(led_event):
        leds = led_event.data
        print("\r", end="")
        for led in ["BD", "BI", "OK", "YI", "YD"]:
            print("0" if led in leds else " ", end=" ")
        sys.stdout.flush()

    bus = Bus()
    bus.subscribe(write_data, thread=True)
    controller = LedController(bus)
    controller.setMode(pat_poweredoff, loop=True)
    time.sleep(5)
    controller.setMode(pat_goal)
    time.sleep(5)
