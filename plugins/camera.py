from subprocess import call
from threading import Thread
import time


class Plugin:
    def __init__(self, bus):
        Thread(target=self.runCamera, daemon=True).start()

    # Run camera
    def runCamera(self):
        while True:
            call("video/run-camera.sh")
            time.sleep(30)
