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
    def __init__(self, shape, duration=2, fade=0.5):
        super().__init__(shape)
        self.shape = shape
        self.duration = duration
        self.ts_requested = 0
        self.fade = fade

    def draw(self):
        now = time.time()
        diff = now - self.ts_requested
        fading = self.duration - diff
        if diff <= self.duration:
            if fading <= self.fade:
                self.shape.set_alpha(fading / self.fade)
            else:
                self.shape.set_alpha(1)

            self.shape.draw()

    def show(self):
        self.ts_requested = time.time()

    def hide(self):
        self.ts_requested = 0


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
