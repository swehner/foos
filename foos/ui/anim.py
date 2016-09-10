import math
import time
import numpy
import pi3d

shaders={}

def Shader(name):
    if name not in shaders:
        shaders[name] = pi3d.Shader(name)

    return shaders[name]

class Delegate:
    def __init__(self, delegate):
        self.delegate = delegate

    def __getattr__(self, name):
        return getattr(self.delegate, name)


class Flashing(Delegate):
    def __init__(self, delegate):
        super().__init__(delegate)
        self.start = None
        self.end = None

    def flash(self, speed=3, times=3, color=(1, 0, 0, 0.5), color2=(-0.5, -0.5, -0.5, 0.5)):
        self.color = color
        self.color2 = color2
        self.start = time.time()
        self.speed = speed * 2 * math.pi
        self.end = self.start + times * 2 * math.pi / self.speed

    def draw(self):
        if self.start:
            now = time.time()
            if now > self.end:
                self.start = None
                self.end = None
                self.set_material((0, 0, 0))
                self.set_alpha(0)
            else:
                d = (now - self.start) * self.speed
                r = math.sin(d)

                color = self.color if r > 0 else self.color2
                if color is None:
                    self.set_alpha(0)
                else:
                    self.set_material((color[0], color[1], color[2]))
                    self.set_alpha(abs(r) * color[3])

        self.delegate.draw()


class Wiggle(Delegate):
    def __init__(self, shape, speed, maxAngle, duration):
        super().__init__(shape)
        self.speed = speed
        self.maxAngle = maxAngle
        self.duration = duration
        self.anim_start = None
        self.angle = 0

    def draw(self):
        now = time.time()

        oldangle = self.angle
        if self.anim_start and (now - self.anim_start) <= self.duration:
            self.angle = self.__animValue(now) * self.maxAngle
        else:
            self.angle = 0
            self.anim_start = None

        if self.angle != oldangle:
            self.delegate.rotateToZ(self.angle)

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
    def __init__(self, shape, opos=(0, 0, 0), oscale=(1, 1, 1), duration=0.3):
        super().__init__(shape)
        self.tstart = 0
        self.duration = duration
        self.pos = opos
        self.scale, self.shape = oscale, shape
        self.tpos, self.tscale = self.pos, self.scale
        self.opos, self.oscale = self.pos, self.scale

    def draw(self):
        now = time.time()
        tdiff = now - self.tstart
        tdiff /= self.duration
        oldpos, oldscale = self.pos, self.scale
        if tdiff > 1:
            self.tstart = 0
            self.pos, self.scale = self.tpos, self.tscale
        else:
            tdiff = math.pow(tdiff, 2)
            self.pos = tuple(numpy.add(self.opos, numpy.multiply(tdiff, numpy.subtract(self.tpos, self.opos))))
            self.scale = tuple(numpy.add(self.oscale, numpy.multiply(tdiff, numpy.subtract(self.tscale, self.oscale))))

        if self.pos != oldpos:
            self.shape.position(*self.pos)
        if self.scale != oldscale:
            self.shape.scale(*self.scale)

        self.shape.draw()

    def moveTo(self, tpos, tscale):
        self.opos = (self.shape.x(), self.shape.y(), self.shape.z())  # self.pos
        # extract current sx, sy, sz (no accessors defined)
        u = self.shape.unif
        self.oscale = (u[6], u[7], u[8])  # self.scale
        self.tpos, self.tscale = tpos, tscale
        self.tstart = time.time()


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
