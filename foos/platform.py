import pi3d

def is_x11():
    return pi3d.PLATFORM != pi3d.PLATFORM_PI and pi3d.PLATFORM != pi3d.PLATFORM_ANDROID

def is_pi():
    return pi3d.PLATFORM == pi3d.PLATFORM_PI
