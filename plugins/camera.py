from foos.process import long_running
from threading import Thread
import time
import foos.config as config


class Plugin:
    def __init__(self, bus):
        Thread(target=self.runCamera, daemon=True).start()

    # Run camera
    def runCamera(self):
        while True:
            long_running(["video/run-camera.sh"])
                              
            time.sleep(30)
