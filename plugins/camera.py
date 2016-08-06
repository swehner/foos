from subprocess import call
from threading import Thread
import time
import foos.config as config


class Plugin:
    def __init__(self, bus):
        Thread(target=self.runCamera, daemon=True).start()

    # Run camera
    def runCamera(self):
        while True:
            call(["video/run-camera.sh", config.replay_path])
            time.sleep(30)
