#!/usr/bin/env python
import time
import queue
import threading
import subprocess
from gl.foos_gui import GuiState

class SoundController:
    # This map scores => sounds
    sounds = {
        (3, 0): 'perfect',
        (5, 0): 'humiliation',
        (0, 0): 'prepare',
        (4, 4): '1_frag'
    }

    def __init__(self):
        self.queue = queue.Queue()
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()

    def run(self):
        while True:
            score = self.queue.get()
            if score not in self.sounds:
                score = score[::-1]
                if score not in self.sounds:
                    continue

            sound = self.sounds[score]
            path = "sounds/{}.wav".format(sound)
            subprocess.call(['play', '-V0', '-G', '-q', path])

    def update(self, score):
        self.queue.put(score)

    def send_info(self, info):
        self.update((info.yScore, info.bScore))

if __name__ == "__main__":
    sc = SoundController()
    for i in range(6):
        score = (i, 0)
        print(score)
        sc.update(score)
        time.sleep(2)

    for i in range(6):
        score = (0, i)
        print(score)
        sc.update(score)
        time.sleep(2)
    sc.update((4, 4))
    time.sleep(3)
