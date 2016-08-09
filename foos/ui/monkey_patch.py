#!/usr/bin/python
import ctypes
from pi3d.util.Ctypes import c_ints
import numpy as np
from PIL import Image
import pi3d

from pi3d.constants import *

from pi3d.Display import Display

def patched_create_surface(self, x=0, y=0, w=0, h=0, layer=0):
  #Set the viewport position and size
  dst_rect = c_ints((x, y, w, h))
  src_rect = c_ints((x, y, w << 16, h << 16))

  self.dispman_display = bcm.vc_dispmanx_display_open(0) #LCD setting
  self.dispman_update = bcm.vc_dispmanx_update_start(0)
  alpha = ctypes.byref(c_ints((1<<16, 0, 0)))

  self.dispman_element = bcm.vc_dispmanx_element_add(
    self.dispman_update,
    self.dispman_display,
    layer, ctypes.byref(dst_rect),
    0, ctypes.byref(src_rect),
    DISPMANX_PROTECTION_NONE,
    alpha, 0, 0)

  nativewindow = c_ints((self.dispman_element, w, h + 1))
  bcm.vc_dispmanx_update_submit_sync(self.dispman_update)

  nw_p = ctypes.pointer(nativewindow)
  self.nw_p = nw_p
    
  self.surface = openegl.eglCreateWindowSurface(self.display, self.config, self.nw_p, 0)

  assert self.surface != EGL_NO_SURFACE
  r = openegl.eglMakeCurrent(self.display, self.surface, self.surface,
                             self.context)
  assert r

  #Create viewport
  opengles.glViewport(0, 0, w, h)


def monkey_patch():
  if PLATFORM == PLATFORM_PI:
    print("Patching create surface to fix alpha")
    pi3d.util.DisplayOpenGL.DisplayOpenGL.create_surface = patched_create_surface
