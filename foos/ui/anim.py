import math
import time
import numpy
import pi3d


class Delegate:
    def __init__(self, delegate):
        self.delegate = delegate

    def __getattr__(self, name):
        return getattr(self.delegate, name)


class Flashing(Delegate):
    def __init__(self, delegate):
        super().__init__(delegate)
        self.color = (1, 0, 0, 0)
        self.start = None
        self.end = None

    def flash(self, speed=3, times=3, color=(1, 0, 0, 0)):
        self.color = color
        self.start = time.time()
        self.speed = speed * 2 * math.pi
        self.end = self.start + times * 2 * math.pi / self.speed

    def draw(self):
        if self.start:
            now = time.time()
            if now > self.end:
                self.start = None
                self.end = None
                self.set_material((0.5, 0.5, 0.5, 0.5))
            else:
                d = (now - self.start) * self.speed
                r = math.sin(d) * 0.5
                # use color when making image lighter
                # use gray when it gets darker
                l = [((x * r) if r > 0 else r) + 0.5 for x in self.color]
                self.set_material(tuple(l))

        self.delegate.draw()


class Wiggle(Delegate):
    def __init__(self, shape, speed, maxAngle, duration):
        super().__init__(shape)
        self.speed = speed
        self.maxAngle = maxAngle
        self.duration = duration
        self.anim_start = None

    def draw(self):
        now = time.time()

        angle = 0
        if self.anim_start and (now - self.anim_start) <= self.duration:
            angle = self.__animValue(now) * self.maxAngle
        else:
            self.anim_start = None

        self.delegate.rotateToZ(angle)
        self.delegate.draw()

    def __animValue(self, now):
        x = now - self.anim_start
        return math.sin(2 * math.pi * x * self.speed) * math.pow(100., -x * x)

    def wiggle(self):
        self.anim_start = time.time()


class Disappear(Delegate):
    def __init__(self, shape, duration=2, fade=0.5, alpha=1):
        super().__init__(shape)
        self.shape = shape
        self.duration = duration
        self.fade = fade
        self.default_alpha = alpha
        self.ts_off = 0
        self.ts_fade = 0

    def draw(self):
        now = time.time()
        if now <= self.ts_off:
            ttime = self.ts_off - self.ts_fade
            diff = now - self.ts_fade
            if diff > 0:
                self.shape.set_alpha(self.alpha * (1 - diff / ttime))
            else:
                self.shape.set_alpha(self.alpha)

            self.shape.draw()

    def show(self, duration=None, fade=None, alpha=None):
        now = time.time()
        self.ts_off = now + (duration if duration else self.duration)
        self.ts_fade = self.ts_off - (fade if fade else self.fade)
        self.alpha = alpha if alpha else self.default_alpha

    def hide(self):
        self.ts_off = 0


class ShowHide(Delegate):
    def __init__(self, shape, visible=False, fade=0.5):
        super().__init__(shape)
        self.visible = visible
        self.shape = shape
        self.fade = fade
        self.ttime = 0

    def draw(self):
        now = time.time()
        diff = self.ttime - now
        if diff > 0:
            self.shape.set_alpha(self.alpha_for_diff(diff))
            self.shape.draw()
        else:
            if self.visible:
                self.shape.set_alpha(1)
                self.shape.draw()

    def alpha_for_diff(self, diff):
        if self.visible:
            return 1 - diff / self.fade
        else:
            return diff / self.fade

    def show(self):
        self.visible = True
        self.ttime = time.time() + self.fade

    def hide(self):
        self.visible = False
        self.ttime = time.time() + self.fade


class Move(Delegate):
    def __init__(self, shape, opos=(0, 0, 0), oscale=(1, 1, 1)):
        super().__init__(shape)
        self.tstart = 0
        self.duration = 0.3
        self.pos = opos
        self.scale, self.shape = oscale, shape
        self.tpos, self.tscale = self.pos, self.scale
        self.opos, self.oscale = self.pos, self.scale

    def draw(self):
        now = time.time()
        tdiff = now - self.tstart
        tdiff /= self.duration
        tdiff = math.pow(tdiff, 2)
        if tdiff > 1:
            self.tstart = 0
            self.pos, self.scale = self.tpos, self.tscale
        else:
            self.pos = numpy.add(self.opos, numpy.multiply(tdiff, numpy.subtract(self.tpos, self.opos)))
            self.scale = numpy.add(self.oscale, numpy.multiply(tdiff, numpy.subtract(self.tscale, self.oscale)))

        self.shape.position(*self.pos)
        self.shape.scale(*self.scale)
        self.shape.draw()

    def moveTo(self, tpos, tscale):
        self.opos = (self.shape.x(), self.shape.y(), self.shape.z())  # self.pos
        # extract current sx, sy, sz (no accessors defined)
        u = self.shape.unif
        self.oscale = (u[6], u[7], u[8])  # self.scale
        self.tpos, self.tscale = tpos, tscale
        self.tstart = time.time()


class ChangingTextures(Delegate):
    def __init__(self, shape, textures, interval):
        super().__init__(shape)
        self.idx = 0
        self.shape = shape
        self.shape.set_textures([textures[0]])
        self.textures = textures
        self.last_change = time.time()
        self.interval = interval
        self.do_change = False

    def draw(self):
        if self.interval > 0:
            self.__change_texture()

        self.shape.draw()

    def __change_texture(self):
        """Changes the bg if forced, or if the double interval time has passed"""
        now = time.time()
        if self.do_change or now > (self.last_change + self.interval * 2):
            self.do_change = False
            self.last_change = now
            self.idx = (self.idx + 1) % len(self.textures)
            self.shape.set_textures([self.textures[self.idx]])

    def encourage_change(self):
        """Call this at a good time to do the bg change"""
        if self.interval > 0 and time.time() > (self.last_change + self.interval):
            self.do_change = True


class ChangingText(Delegate):
    def __init__(self, shader, **kwargs):
        self.s = pi3d.String(**kwargs)
        self.s.set_shader(shader)
        self.newtext = None
        self.first = True
        super().__init__(self.s)

    def quick_change(self, s):
        self.newtext = s

    def draw(self):
        if self.newtext and not self.first:
            self.s.quick_change(self.newtext)
            self.newtext = None

        self.first = False
        self.s.draw()


class Multiline():
    def __init__(self, shader, font=None, string="", x=0, y=0, z=0, justify='C'):
        ls = string.splitlines()
        self.lines = []
        for s in ls:
            self.lines.append(ChangingText(shader, font=font, string=s,
                                           is_3d=False, x=x, y=y, z=z, justify=justify))
            y -= font.height

    def quick_change(self, string):
        for i, s in enumerate(string.splitlines()):
            self.lines[i].quick_change(s)

    def draw(self):
        for l in self.lines:
            l.draw()
