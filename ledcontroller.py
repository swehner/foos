#/usr/bin/env python
import time
import sys
from threading import Thread
import queue
import collections

BD=0b00001
BI=0b00010
YD=0b00100
YI=0b01000
OK=0b10000

names = {BD: "BD", BI: "BI", YD: "YD", YI: "YI", OK: "OK"}

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
            
class LedController(Thread):
    def __init__(self, ledWriter, debugWriter):
        super(LedController, self).__init__(daemon=True)
        self.queue = queue.Queue()
        self.ledWriter = ledWriter
        self.debugWriter = debugWriter
        
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

    def __getArduinoValueFor(self, leds):
        value = sum(leds)
        return chr(value + ord('A'))
    
    def writeLedsSerial(self, leds=[]):
        self.ledWriter.writeline(self.__getArduinoValueFor(leds))
        
    def writeLedsDebug(self, leds=[]):
        arduinoVal = self.__getArduinoValueFor(leds)
        debug = [names.get(x, "ERR") for x in leds]
        self.debugWriter.writeline("Leds: %s -> arduino '%s'" % (debug, arduinoVal))
            
    def setLeds(self, leds=[]):
        """
        print("\r", end="")
        for led in ["BD", "BI", "OK", "YI", "YD"]:
            print("0" if led in leds else " ", end=" ")
        sys.stdout.flush()
        """
        self.writeLedsSerial(leds)
        self.writeLedsDebug(leds)

    def setMode(self, mode, loop=False):
        self.stop = True
        self.queue.put((loop, mode))


pat_reset = 3 * [Pattern(0.2, [BI, BD, YI, YD]),
                 Pattern(0.1),
                 Pattern(0.2, [BI, BD, YI, YD]),
                 Pattern(1)]

pat_poweredoff = [Pattern(0.5, [OK]),
                  Pattern(1)]

pat_goal = 2 * [ 3 * [Pattern(0.2, [BI, BD, OK, YI, YD]),
                      Pattern(0.2)],
                 [Pattern(0.2, [BD, YD]),
                  Pattern(0.2, [OK]),
                  Pattern(0.2, [BI, YI])]]

pat_demo = [Pattern(1, [BD]),
            Pattern(1, [BI]),
            Pattern(1, [YD]),
            Pattern(1, [YI]),
            Pattern(1, [OK])]

if __name__=="__main__":
    controller = LedController()
    controller.start()
    controller.setMode(pat_poweredoff, loop=True)
    time.sleep(5)
    controller.setMode(pat_goal)
