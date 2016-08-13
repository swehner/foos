#!/usr/bin/python
from __future__ import absolute_import, division, print_function, unicode_literals

import pi3d
import ctypes
from pi3d.constants import *
import time

vh = ctypes.CDLL("video_helper.so")
FINIFUNC = ctypes.CFUNCTYPE(None)
# keep a global reference to the callback
callback = None
start_callback = None

class EGLTexture():
    def __init__(self, t):
        self.t = t
        self.blend = False
        
    def tex(self):
        return self.t

    def load_opengl(self):
        return


def init(display, size):
    tex = ctypes.c_int()
    vh.init_textures(display.opengl.display, display.opengl.context, size[0], size[1], ctypes.byref(tex))
    return EGLTexture(tex)

def playVideo(filename, start_cb, cb):
    global callback, start_callback
    if cb:
        callback = FINIFUNC(cb)
    else:
        callback = None

    if start_cb:
        start_callback = FINIFUNC(start_cb)
    else:
        start_callback = None

    vh.run_video(filename.encode("ascii"), start_callback, callback)

def stop():
    vh.run_video("quit", None)
