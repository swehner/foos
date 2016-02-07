import time
import os
import sys
from inotify_simple import INotify, flags
import numpy as np
import threading
from foos.bus import Event
import video_config
import multiprocessing as mp


class EventGen:
    """Receive movement status from detector, dedup and send events"""
    def __init__(self, absence_timeout, bus):
        self.absence_timeout = absence_timeout
        self.last_mv = 0
        self.movement = None
        self.bus = bus

    def reportMovement(self, newmovement):
        if newmovement:
            self.last_mv = time.time()
        else:
            if self.last_mv + self.absence_timeout > time.time():
                # wait a bit before assuming people have left
                return

        if self.movement != newmovement:
            event = "movement_detected" if newmovement else "movement_not_detected"
            print(time.strftime("%H:%M:%S", time.localtime()), event)
            self.bus.notify(Event(event))
            self.movement = newmovement


class MotionDetector:
    """Detect motion in a frame"""
    def __init__(self, vector_threshold, min_vectors):
        self.vector_threshold = vector_threshold
        self.min_vectors = min_vectors

    def frame_has_movement(self, frame):
        arr = np.fromstring(frame, np.dtype("2<u2"))
        arr = arr[:, 1].astype('float')
        arr = np.square(arr)
        mvs = len(arr[arr > self.vector_threshold])
        has_movement = (mvs > self.min_vectors)
        return has_movement


class Plugin:
    def __init__(self, bus):
        self.size = (82, 46)
        self.md = MotionDetector(100000, 30)
        self.eg = EventGen(5, bus)
        self.watch_dir = video_config.fragments_path
        self.prefix = 'mv'
        mp.Process(daemon=True, target=self.run).start()

    def run(self):
        inotify = INotify()
        watch_flags = flags.CLOSE_WRITE
        print("Watching", self.watch_dir)
        wd = inotify.add_watch(self.watch_dir, watch_flags)

        # And see the corresponding events:
        while True:
            events = inotify.read()
            matching = [f.name for f in events if f.name.startswith(self.prefix)]
            if len(matching) > 0:
                # take only the last file
                self.processForMovement(os.path.join(self.watch_dir, matching[-1]))

        inotify.close()

    def readFrame(self, f):
        return f.read(self.size[0] * self.size[1] * 4)

    def processFile(self, f):
        d = open(f, 'rb')

        #skip first frame
        frame = self.readFrame(d)
        has_movement = False
        while not has_movement:
            frame = self.readFrame(d)
            if len(frame) == 0:
                break

            has_movement = self.md.frame_has_movement(frame)

        d.close()
        return has_movement

    def processForMovement(self, filename):
        has_movement = self.processFile(filename)
        self.eg.reportMovement(has_movement)
