#!/usr/bin/python

import pi3d
from .anim import Delegate


class Menu:
    def __init__(self, font, arrow, n=10, options=[], wchar=20, z=5, title="Menu"):
        self.selectpos = 0
        self.offset = 0
        self.options = options
        self.n = n
        self.lheight = 65
        arrow_size = 32
        self.width = wchar * 25 + arrow_size * 2
        self.shapes = []
        self.starty = self.lheight * (n - 1) / 2
        self.wchar = wchar
        self.title = title
        py = self.starty
        px = -300

        flat_uv = pi3d.Shader("uv_flat")
        flat_mat = pi3d.Shader("mat_flat")
        self.select = pi3d.shape.Sprite.Sprite(w=self.width, h=self.lheight,
                                               y=py + self.lheight / 2, z=z + 1)
        self.select.set_material((0.8, 0.56, 0))
        self.select.set_shader(flat_mat)

        self.bg = pi3d.shape.Sprite.Sprite(w=self.width, h=self.lheight * n,
                                           y=py - self.lheight * n / 2, z=z + 2)
        self.bg.set_shader(flat_mat)
        self.bg.set_material((0, 0, 0))
        self.bg.set_alpha(0.9)
        self.bg_t = pi3d.shape.Sprite.Sprite(w=self.width, h=self.lheight,
                                             y=py + self.lheight / 2, z=z + 2)
        self.bg_t.set_shader(flat_mat)
        self.bg_t.set_material((0, 0, 0))

        self.title_shape = pi3d.String(font=font, string=" " * wchar,
                                       is_3d=False, x=-arrow_size, y=py + self.lheight / 2, z=z)

        self.title_shape.set_shader(flat_uv)

        self.down_i = pi3d.ImageSprite(arrow, flat_uv, x=self.width / 2 - arrow_size, y=py - self.lheight * (n - 0.5), z=z, w=arrow_size, h=arrow_size, rz=180)
        self.up_i = pi3d.ImageSprite(arrow, flat_uv, x=self.width / 2 - arrow_size, y=py - self.lheight / 2, z=z, w=arrow_size, h=arrow_size)

        for i in range(0, n):
            s = pi3d.String(font=font, string=" " * wchar,
                            is_3d=False, x=-arrow_size, y=py - self.lheight / 2, z=z)
            py -= self.lheight

            s.set_shader(flat_uv)
            self.shapes.append(s)

        self.changed = True

    def setText(self):
        for i, s in enumerate(self.shapes):
            idx = self.offset + i
            t, id = self.options[idx] if idx < len(self.options) else ("", 0)
            t = t.ljust(self.wchar)
            # changed selected element text color to black
            # texrgb += materialrgb - (0.5,)*3 - see std_main_uv.inc
            if i == self.selectpos:
                s.set_material((-1.5,) * 3)
            else:
                s.set_material((0.5,) * 3)
            s.quick_change(t)

        self.select.positionY(self.starty - self.lheight * (self.selectpos + 0.5))
        self.title_shape.quick_change(self.title)

    def selIndex(self):
        return self.offset + self.selectpos

    def _up(self):
        if self.selectpos > 0:
            self.selectpos -= 1
        else:
            if self.offset > 0:
                self.offset -= 1

        self.changed = True

    def _down(self):
        if self.selectpos < min(self.n, len(self.options)) - 1:
            self.selectpos += 1
        else:
            if (self.offset + self.selectpos) < len(self.options) - 1:
                self.offset += 1

        self.changed = True

    def up(self):
        self._mv(True)

    def down(self):
        self._mv(False)

    def _mv(self, up=True):
        idx = self.selIndex()
        i = 1
        idx += -1 if up else 1
        while idx >= 0 and idx < len(self.options) and self.options[idx][0] == "":
            idx += -1 if up else 1
            i += 1

        for x in range(i):
            if up:
                self._up()
            else:
                self._down()

    def setTitle(self, title):
        self.title = title
        self.changed = True

    def draw(self):
        self.select.draw()
        self.bg_t.draw()
        self.bg.draw()
        self.title_shape.draw()

        if self.offset > 0:
            self.up_i.draw()

        if len(self.options) > self.offset + self.n:
            self.down_i.draw()

        for s in self.shapes:
            s.draw()

        if self.changed:
            self.setText()
            self.changed = False

    def selected(self):
        idx = self.offset + self.selectpos
        return (idx, self.options[idx])

    def setOptions(self, options):
        self.offset = 0
        self.selectpos = 0
        self.options = options
        self.changed = True


class MenuTree(Delegate):
    def __init__(self, tree, menu, rootTitle="Menu"):
        super().__init__(menu)
        self.tree = tree
        self.menu = menu
        self.rootTitle = rootTitle
        self.reset()

    def reset(self, tree=None):
        if tree:
            self.tree = tree

        self.breadcrumb = []
        self.menu.setOptions(self.tree)
        self.setTitle()

    def goBack(self):
        self.breadcrumb.pop(-1)
        menu = self.tree
        for b in self.breadcrumb:
            menu = menu[b][1]
        self.menu.setOptions(self.tree)

    def setTitle(self):
        menu = self.tree
        if len(self.breadcrumb) > 0:
            for b in self.breadcrumb[:-1]:
                menu = menu[b][1]
            t = menu[self.breadcrumb[-1]][0]
        else:
            t = self.rootTitle

        self.menu.setTitle(t)

    def select(self):
        idx, (txt, elem) = self.menu.selected()
        if isinstance(elem, list):
            self.breadcrumb.append(idx)
            self.menu.setOptions(elem)
        else:
            if elem is None:
                self.goBack()
            if callable(elem):
                elem()

        self.setTitle()
