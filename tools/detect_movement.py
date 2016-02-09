import time
import os
import sys
from inotify_simple import INotify, flags
import numpy as np
from PIL import Image

sx = 25

class EventGen:
    """Receive movement status from detector, dedup and send events"""
    def __init__(self, absence_timeout):
        self.absence_timeout = absence_timeout
        self.last_mv = 0
        self.movement = None

    def reportMovement(self, newmovement):
        if newmovement:
            self.last_mv = time.time()
        else:
            if self.last_mv + self.absence_timeout > time.time():
                # wait a bit before assuming people have left
                return

        if self.movement != newmovement:
            print(time.strftime("%H:%M:%S", time.localtime()),
                  "HOLA GENTE!!" if newmovement else "volveeeed cabroneeeees...")
            self.movement = newmovement


class MotionDetector:
    """Detect motion in a frame"""
    def __init__(self, vector_threshold, min_vectors):
        self.vector_threshold = vector_threshold
        self.min_vectors = min_vectors
        self.size = size

    def frame_has_movement(self, frame):
        arr = np.fromstring(frame, np.dtype("2<u2"))
        arr = arr[:, 1].astype('float')
        arr = np.reshape(arr, (size[1], size[0]))
        arr = arr [:,sx:size[0]-sx]
        arr = np.square(arr)
        avg = np.average(arr) 
        median = np.median(arr)
        mvs = len(arr[arr > self.vector_threshold])
        has_movement = (mvs > self.min_vectors)
        ind = 'M' if has_movement else '.'
        print('%10d %10d %5d %s'%(avg, median, mvs, ind), file=sys.stderr)
        return has_movement

def runs(l):
    runs=[]
    prev=l[0]
    n=1    
    for i in l[1:]:
        if prev==i:
            n+=1
        else:
            runs.append((prev, n))
            n=1
                
        prev=i
    runs.append((prev, n))
    return runs

def asImage(frame, name):
    #print("Converting to", name, file=sys.stderr)
    arr = np.fromstring(frame, np.dtype("2<u2"))
    arr = arr[:, 1]
    arr = np.reshape(arr / 2, (size[1], size[0]))

    arr = arr [:,sx:size[0]-sx]
    magnitudes = arr.astype('u1')

    im = Image.fromarray(magnitudes)
    im = im.resize(((size[0] - 2 * sx) * 16, size[1] * 16))
    im.save(name)


def readFrame(f):
    return f.read(size[0] * size[1] * 4)


def processFile(f, convert_to_images):
    #print("Using", f, file=sys.stderr)
    d = open(f, 'rb')
    i = 0

    #skip first frame
    frame = readFrame(d)
    ms = []
    while True:
        frame = readFrame(d)
        if len(frame) == 0:
            break
        if convert_to_images:
            asImage(frame, "%s%02d.png" % (f[:-4], i))
        i += 1
        has_movement = md.frame_has_movement(frame)
        ms.append(has_movement)

    rs = runs(ms)
    rs.append((True, 0))
    streak = max([r[1] for r in rs if r[0]])
    #print("Longest streak: ", streak)
    minstreak = 9
    mv = streak>=minstreak
    print("Detected movement: %6s %d/%d %s" % (mv, streak, minstreak, f))
    sys.stdout.flush()
    d.close()
    return mv


def processForMovement(filename):
    #print(filename, file=sys.stderr)
    has_movement = processFile(filename, False)
    eg.reportMovement(has_movement)


size = (82, 46)
md = MotionDetector(100000, 30)
eg = EventGen(30)
watch_dir = '/run/replay/fragments'
prefix = 'mv'

if len(sys.argv) == 1:
    inotify = INotify()
    watch_flags = flags.CLOSE_WRITE
    wd = inotify.add_watch(watch_dir, watch_flags)

    # And see the corresponding events:
    while True:
        events = inotify.read()
        matching = [f.name for f in events if f.name.startswith(prefix)]
        if len(matching) > 0:
            # take only the last file
            processForMovement(os.path.join(watch_dir, matching[-1]))

    inotify.close()
else:
    for f in sys.argv[1:]:
        processFile(f, True)
