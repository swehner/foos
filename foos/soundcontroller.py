#!/usr/bin/env python
import time
import queue
import threading
import subprocess
import random


class SoundController:
    # This map scores => sounds
    sounds = {
        (0, 3): 'perfect',
        (0, 5): 'humiliation',
        (4, 4): '1_frag'
    }
    generic_goal_sounds = ['crowd1', 'crowd2']

    def __init__(self, bus, sounds_dir):
        self.bus = bus
        self.bus.subscribe(self.process_event, thread=True)
        self.rand = random.Random()
        self.sounds_dir = sounds_dir

    def process_event(self, ev):
        sounds = []
        if ev.name == 'score_goal':
            score = (ev.data['yellow'], ev.data['black'])
            score = tuple(sorted(score))
            if score in self.sounds:
                sounds.append(self.sounds[score])

            sounds.append(self.rand.choice(self.generic_goal_sounds))

        elif ev.name == 'score_reset':
            sounds = ['whistle_2short1long']
        else:
            return

        sounds = [self.sounds_dir + "/{}.wav".format(sound) for sound in sounds]

        # if more than one sound, mix
        if len(sounds) > 1:
            sounds.insert(0, '-m')

        subprocess.call(['echo', 'play', '-V0', '-G', '-q'] + sounds)


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
