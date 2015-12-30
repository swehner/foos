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

    def __init__(self, bus):
        self.bus = bus
        self.bus.subscribe(self.process_event, thread=True)
        
    def process_event(self, ev):
        if ev.name == 'score_goal':
            score = (ev.data['yellow'], ev.data['black'])
            if score not in self.sounds:
                score = score[::-1]
                if score not in self.sounds:
                    return
                
        elif ev.name == 'score_reset':
            score = (0,0)
        else:
            return
            
        sound = self.sounds[score]
        path = "sounds/{}.wav".format(sound)
        subprocess.call(['play', '-V0', '-G', '-q', path])


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
