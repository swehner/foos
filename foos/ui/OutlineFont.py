from __future__ import absolute_import, division, print_function, unicode_literals

import ctypes
import numpy as np
import itertools
import os.path
import sys
if sys.version_info[0] == 3:
  unichr = chr

# NB PIL must be available to use Font. Otherwise use Pngfont
from PIL import Image, ImageDraw, ImageFont

from pi3d.constants import *
from pi3d.Texture import Texture

MAX_SIZE = 1920

class OutlineFont(Texture):
  """
  A Font contains a TrueType font ready to be rendered in OpenGL.

  A font is just a mapping from codepoints (single Unicode characters) to glyphs
  (graphical representations of those characters).

  Font packs one whole font into a single Texture using PIL.ImageFont,
  then creates a table mapping codepoints to subrectangles of that Texture."""

  def __init__(self, font, color=(255,255,255,255), outline=(0,0,0,255), outline_size=0, codepoints=None,
               add_codepoints=None, font_size=42, image_size=512,
               italic_adjustment=1.1, background_color=None, mipmap=True, filter=None):
    """Arguments:
    *font*:
      File path/name to a TrueType font file.

    *color*:
      Color in standard hex format #RRGGBB

    *font_size*:
      Point size for drawing the letters on the internal Texture

    *codepoints*:
      Iterable list of characters. All these formats will work:

        'ABCDEabcde '
        [65, 66, 67, 68, 69, 97, 98, 99, 100, 101, 145, 148, 172, 32]
        [c for c in range(65, 173)]

      Note that Font will ONLY use the codepoints in this list - if you
      forget to list a codepoint or character here, it won't be displayed.
      If you just want to add a few missing codepoints, you're probably better
      off using the *add_codepoints* parameter.

      If the string version is used then the program file might need to
      have the coding defined at the top:  # -*- coding: utf-8 -*-

      The default is *codepoints*=range(256).

    *add_codepoints*:
      If you are only wanting to add a few codepoints that are missing, you
      should use the *add_codepoints* parameter, which just adds codepoints or
      characters to the default list of codepoints (range(256). All the other
      comments for the *codepoints* parameter still apply.

    *image_size*:
      Width and height of the Texture that backs the image.
      Since the introduction of PointText using Point drawing image_size is
      no longer used - all Font Textures are 1024.

    *italic_adjustment*:
      Adjusts the bounding width to take italics into account.  The default
      value is 1.1; you can get a tighter bounding if you set this down
      closer to 1, but italics might get cut off at the right. Since PointText
      this isn't used.
    """
    super(OutlineFont, self).__init__(font, mipmap=mipmap, filter=filter)
    self.row_margin = 2
    self.font = font
    try:
      imgfont = ImageFont.truetype(font, font_size)
    except IOError:
      abspath = os.path.abspath(font)
      msg = "Couldn't find font file '%s'" % font
      if font != abspath:
        msg = "%s - absolute path is '%s'" % (msg, abspath)

      raise Exception(msg)

    ascent, descent = imgfont.getmetrics()
    self.height = ascent + descent

    if codepoints is not None:
      codepoints = list(codepoints)
    else:
      codepoints = list(range(256))
    if add_codepoints is not None:
      add_codepoints = list(add_codepoints)
      if (len(codepoints) + len(add_codepoints)) > 256: # make room at end
        codepoints = codepoints[:(256 - len(add_codepoints))]
      codepoints += add_codepoints

    self.im = Image.new("RGBA", (image_size, image_size), background_color)
    self.ix, self.iy = image_size, image_size

    self.glyph_table = {}

    draw = ImageDraw.Draw(self.im)

    curX = 0.0
    curY = 0.0
    characters = []
    s_inc = outline_size * 2
    self.height += s_inc

    for i in itertools.chain([0], codepoints):
      try:
        ch = unichr(i)
      except TypeError:
        ch = i

      chwidth, chheight = imgfont.getsize(ch)
      chwidth += s_inc
      chheight += s_inc

      if (curX + chwidth) > self.ix:
          curX = 0
          if (curY + self.height + self.row_margin) > self.ix:
              # some chars will be cropped)
              raise Exception("Font image too small (%dx%d) for all characters - got to codepoint %d" % (self.ix, self.iy, i))

          curY += self.height + self.row_margin


      offset = 0
      # draw the outline by drawing the displaced text repeatedly
      if outline_size > 0:
          for xi in range(s_inc + 1):
              for yi in range(s_inc + 1):
                  if xi == 0 or xi == s_inc or yi == 0 or yi == s_inc:
                      draw.text((curX + xi, curY + yi), ch, font=imgfont, fill=outline)

      draw.text((curX + outline_size, curY + outline_size), ch, font=imgfont, fill=color)
      x = (curX + 0.0) / self.ix
      y = (curY + self.height + 0.0) / self.iy
      tw = (chwidth + 0.0) / self.ix
      th = (self.height + 0.0) / self.iy

      table_entry = [
        chwidth - s_inc,
        chheight - s_inc,
        [[x + tw, y - th], [x, y - th], [x, y], [x + tw, y]],
        [[chwidth, 0, 0], [0, 0, 0], [0, -self.height, 0], [chwidth, -self.height, 0]],
        float(curX) / self.ix,
        float(curY) / self.iy
        ]

      self.glyph_table[ch] = table_entry

      curX = curX + chwidth

    self.image = np.array(self.im)
    self._tex = ctypes.c_uint()

  def _load_disk(self):
    """
    we need to stop the normal file loading by overriding this method
    """
