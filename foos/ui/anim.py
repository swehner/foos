import math
import time
import numpy


class Delegate:
    def __init__(self, delegate):
        self.delegate = delegate

    def __getattr__(self, name):
        return getattr(self.delegate, name)


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

    def draw(self):
        if self.interval > 0:
            self.__change_texture()

        self.shape.draw()

    def __change_texture(self):
        now = time.time()
        if now > (self.last_change + self.interval):
            self.last_change = now
            self.idx = (self.idx + 1) % len(self.textures)
            self.shape.set_textures([self.textures[self.idx]])
