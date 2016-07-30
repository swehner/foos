import time
import threading
import subprocess
import foos.config as config
import logging

logger = logging.getLogger(__name__)


class Plugin:
    def __init__(self, bus, standby_timeout=500):
        self.standby_timeout = config.standby_timeout_secs
        self.bus = bus
        self.activation_events = ["button_event", "movement_detected", "goal_event"]
        self.last_active = time.time()
        self.active = True

        # disable if standby_timeout is 0
        if self.standby_timeout != 0:
            self.bus.subscribe(self.process_event, subscribed_events=self.activation_events)
            threading.Thread(daemon=True, target=self.run).start()

    def run(self):
        while True:
            time.sleep(1)
            if self.active and time.time() > (self.last_active + self.standby_timeout):
                self.turn_off()

    def turn_off(self):
        logger.info("Turning TV off...")
        self.active = False
        subprocess.call("echo 'standby 0' | cec-client -s >/dev/null", shell=True)
        self.bus.notify("tv_standby")

    def turn_on(self):
        logger.info("Turning TV on...")
        self.active = True
        subprocess.call("echo 'on 0' | cec-client -s >/dev/null", shell=True)
        self.bus.notify("tv_on")

    def process_event(self, ev):
        self.last_active = time.time()
        if not self.active:
            self.turn_on()
