import operator
from functools import partial
from threading import Timer

class Leds:
    on_leds = set()

    def on(self, led, time=None):
        """Turn on a led, optionally turning it off after time seconds"""
        self.on_leds.add(led)
        if time:
            t = Timer(time, partial(self.off, led))
            t.start()

    def off(self, led):
        self.on_leds.remove(led)

    def get_status(self):
        """Return the needed command for the arduino"""
        bits = reduce(operator.or_, self.on_leds, 0)
        return bits + ord('A')
