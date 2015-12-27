import ctypes
import platform
import time

from ctypes import c_int, c_float
from six.moves import xrange

import pi3d
from pi3d.constants import *

from pi3d.util.Ctypes import c_ints

if pi3d.USE_PYGAME:
  import pygame
elif PLATFORM != PLATFORM_PI and PLATFORM != PLATFORM_ANDROID:
  from pyxlib import xlib
  from pyxlib.x import *


from functools import partial

pi3dlayer = 100


def create_surface(self, x=0, y=0, w=0, h=0):
    #Set the viewport position and size
    dst_rect = c_ints((x, y, w, h))
    src_rect = c_ints((x, y, w << 16, h << 16))

    if PLATFORM == PLATFORM_ANDROID:
      self.surface = openegl.eglGetCurrentSurface(EGL_DRAW)
      # Get the width and height of the screen - TODO, this system returns 100x100
      time.sleep(0.2) #give it a chance to find out the dimensions
      w = c_int()
      h = c_int()
      openegl.eglQuerySurface(self.display, self.surface, EGL_WIDTH, ctypes.byref(w))
      openegl.eglQuerySurface(self.display, self.surface, EGL_HEIGHT, ctypes.byref(h))
      self.width, self.height = w.value, h.value
    elif PLATFORM == PLATFORM_PI:
      self.dispman_display = bcm.vc_dispmanx_display_open(0) #LCD setting
      self.dispman_update = bcm.vc_dispmanx_update_start(0)
      print("Using layer ", pi3dlayer)
      self.dispman_element = bcm.vc_dispmanx_element_add(
        self.dispman_update,
        self.dispman_display,
        pi3dlayer, ctypes.byref(dst_rect),
        0, ctypes.byref(src_rect),
        DISPMANX_PROTECTION_NONE,
        0, 0, 0)

      nativewindow = c_ints((self.dispman_element, w, h + 1))
      bcm.vc_dispmanx_update_submit_sync(self.dispman_update)

      nw_p = ctypes.pointer(nativewindow)
      self.nw_p = nw_p

      self.surface = openegl.eglCreateWindowSurface(self.display, self.config, self.nw_p, 0)

    elif pi3d.USE_PYGAME:
      import pygame
      flags = pygame.RESIZABLE | pygame.OPENGL
      wsize = (w, h)
      if w == self.width and h == self.height: # i.e. full screen
        flags = pygame.FULLSCREEN | pygame.OPENGL | pygame.NOFRAME
        wsize = (0, 0)
      self.width, self.height = w, h
      self.d = pygame.display.set_mode(wsize, flags)
      self.window = pygame.display.get_wm_info()["window"]
      self.surface = openegl.eglCreateWindowSurface(self.display, self.config, self.window, 0)

    else:
      print("I'm running in an X window")
      self.width, self.height = w, h

      # Set some WM info
      root = xlib.XRootWindowOfScreen(self.screen)
      self.window = xlib.XCreateSimpleWindow(self.d, root, x, y, w, h, 1, 0, 0)

      s = ctypes.create_string_buffer(b'WM_DELETE_WINDOW')
      self.WM_DELETE_WINDOW = ctypes.c_ulong(xlib.XInternAtom(self.d, s, 0))
      #TODO add functions to xlib for these window manager libx11 functions
      #self.window.set_wm_name('pi3d xlib window')
      #self.window.set_wm_icon_name('pi3d')
      #self.window.set_wm_class('draw', 'XlibExample')

      xlib.XSetWMProtocols(self.d, self.window, ctypes.byref(self.WM_DELETE_WINDOW), 1)
      #self.window.set_wm_hints(flags = Xutil.StateHint,
      #                         initial_state = Xutil.NormalState)

      #self.window.set_wm_normal_hints(flags = (Xutil.PPosition | Xutil.PSize
      #                                         | Xutil.PMinSize),
      #                                min_width = 20,
      #                                min_height = 20)

      xlib.XSelectInput(self.d, self.window, KeyPressMask)
      xlib.XMapWindow(self.d, self.window)
      self.surface = openegl.eglCreateWindowSurface(self.display, self.config, self.window, 0)

    assert self.surface != EGL_NO_SURFACE
    r = openegl.eglMakeCurrent(self.display, self.surface, self.surface,
                               self.context)
    assert r

    #Create viewport
    opengles.glViewport(0, 0, w, h)


def patch():
    print("Monkey patching")
    print(pi3d.util.DisplayOpenGL.DisplayOpenGL.create_surface)
    pi3d.util.DisplayOpenGL.DisplayOpenGL.create_surface = create_surface


def fixX11KeyEvents(display):
    print("Careful! Mangling pi3d X stuff")
    old = display._loop_begin

    # register for all key events
    xlib.XSelectInput(display.opengl.d, display.opengl.window, KeyPressMask | KeyReleaseMask)

    def my_begin(self):
        n = xlib.XEventsQueued(self.opengl.d, xlib.QueuedAfterFlush)
        for i in range(0, n):
            if xlib.XCheckMaskEvent(self.opengl.d, KeyPressMask | KeyReleaseMask, self.ev):
                self.event_list.append(self.ev)

        # continue with the old code (which processes events - so this might not work 100%)
        old()

    display._loop_begin = partial(my_begin, display)
