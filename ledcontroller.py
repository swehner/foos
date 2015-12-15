#/usr/bin/env python
import time
import sys
from threading import Thread
import queue
import collections


class Pattern():
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
            
class LedRunner(Thread):
    def __init__(self):
        super(LedRunner, self).__init__()
        self.queue = queue.Queue()

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
        print("\r", end="")
        for led in ["BD", "BI", "OK", "YI", "YD"]:
            print("0" if led in leds else " ", end=" ")
        sys.stdout.flush()

    def setMode(self, mode, loop=False):
        self.stop = True
        self.queue.put((loop, mode))

if __name__=="__main__":
    reset = 3 * [Pattern(0.2, ["BI", "BD", "YI", "YD"]),
                 Pattern(0.1),
                 Pattern(0.2, ["BI", "BD", "YI", "YD"]),
                 Pattern(1)]

    poweredoff = [Pattern(0.5, ["OK"]),
                  Pattern(1)]

    goal = 2 * [ 3 * [Pattern(0.2, ["BI", "BD", "OK", "YI", "YD"]),
                      Pattern(0.2)],
                 [Pattern(0.2, ["BD", "YD"]),
                  Pattern(0.2, ["OK"]),
                  Pattern(0.2, ["BI", "YI"])]]


    runner = LedRunner()
    runner.start()
    runner.setMode(poweredoff, loop=True)
    time.sleep(5)
    runner.setMode(goal)
