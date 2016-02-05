import sys
import binascii
import numpy as np
from PIL import Image
import os
import time
import glob

size = (82, 46)

def asImage(arr):
    arr = np.reshape(arr, (size[1], size[0]))
    magnitudes = arr.astype('u1')

    im = Image.fromarray(magnitudes)
    im.save("img_%s_%02d.png" % (os.path.basename(f)[:-4], i))


f = None
threshold = 10000
movement = None
while True:
    time.sleep(0.1)
    all = sorted(glob.iglob('/run/replay/fragments/mv*'), reverse=True, key=os.path.getmtime)
    #skip the last one
    newest = all[1]
    if newest == f:
        time.sleep(0.1)
        continue

    f = newest
    print("Using", f, file=sys.stderr)
    d = open(f, 'rb')
    i = 0

    #skip first frame
    frame = d.read(size[0] * size[1] * 4)
    while True:
        frame = d.read(size[0] * size[1] * 4)
        if len(frame) == 0:
            break
        arr = np.fromstring(frame, np.dtype("2<u2"))
        arr = arr[:, 1].astype('float')
        arr = np.square(arr)
        mvs =len(arr[ arr>100000])
        m = np.max(arr)
        avg = np.sum(arr) / (size[0] * size[1])
        print("%10d %10d %10d" % (m,avg,mvs), file=sys.stderr)
        #newmovement = (avg > threshold)
        newmovement = (mvs>50)
        if movement != newmovement:
            print("HOLA GENTE!!" if newmovement else "volveeeed cabroneeeees...")
            print("%10d %10d %10d" % (m,avg,mvs))
            movement = newmovement
        
        #asImage(arr)

        i += 1
