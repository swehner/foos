import time
import threading
import subprocess

from .bus import Event, Bus


class Standby:
    def __init__(self, bus, standby_timeout=500):
        self.standby_timeout = standby_timeout
        self.bus = bus
        self.activation_events = ["button_event"]
        self.last_active = time.time()
        self.active = True

        # disable if standby_timeout is 0
        if self.standby_timeout != 0:
            self.bus.subscribe(self.process_event)
            threading.Thread(daemon=True, target=self.run).start()

    def run(self):
        while True:
            time.sleep(1)
            if self.active and time.time() > (self.last_active + self.standby_timeout):
                self.turn_off()

    def turn_off(self):
        print("Turning TV off...")
        self.active = False
        subprocess.call("echo 'standby 0' | cec-client -s", shell=True)
        self.bus.notify(Event("tv_standby"))

    def turn_on(self):
        print("Turning TV on...")
        self.active = True
        subprocess.call("echo 'on 0' | cec-client -s", shell=True)
        self.bus.notify(Event("tv_on"))

    def process_event(self, ev):
        if ev.name in self.activation_events:
            self.last_active = time.time()
            if not self.active:
                self.turn_on()
