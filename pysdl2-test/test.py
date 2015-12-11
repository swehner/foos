import sys
import sdl2
import sdl2.ext
import sdl2.sdlimage
from sdl2.surface import SDL_Rect
import time
def run():
    sdl2.ext.init()
    window = sdl2.ext.Window("The Pong Game", size=(1920, 1080))
    print sdl2.SDL_GetCurrentVideoDriver()
    window.show()
    running = True
    bg = sdl2.ext.load_image("bg_black.png")
    bg = sdl2.surface.SDL_ConvertSurface(bg, window.get_surface().format, 0)
    window.refresh()
    start = time.time()
    n = 5
    for i in xrange(0,n):
        
        sdl2.surface.SDL_BlitSurface(bg, SDL_Rect(0,0,1920,1080),
                                     window.get_surface(), SDL_Rect(0,0,1920,1080))
        window.refresh()

    print "Per blit:", (time.time()-start)*1000/n, "ms"
    

if __name__ == "__main__":
    sys.exit(run())
