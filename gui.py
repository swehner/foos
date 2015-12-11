import os
import pygame


class pyscope:
    screen = None

    def __init__(self, fullscreen=True):
        "Ininitializes a new pygame screen using the framebuffer"
        disp_no = os.getenv("DISPLAY")
        if disp_no:
            print "I'm running under X display = {0}".format(disp_no)

        # Check which frame buffer drivers are available
        drivers = ['fbcon', 'x11']
        found = False
        for driver in drivers:
            # Make sure that SDL_VIDEODRIVER is set
            if not os.getenv('SDL_VIDEODRIVER'):
                os.putenv('SDL_VIDEODRIVER', driver)
            try:
                pygame.display.init()
            except pygame.error:
                print 'Driver: {0} failed.'.format(driver)
                continue
            found = True
            break

        if not found:
            raise Exception('No suitable video driver found!')

        if fullscreen:
            size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
            print "Framebuffer size: %d x %d" % (size[0], size[1])
        else:
            # Hardcoding size since the code is not ready for a random resolution
            size = 1920, 1080

        self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN if fullscreen else 0)
        # Initialise font support
        pygame.font.init()
        # Render the screen
        pygame.display.update()
        pygame.mouse.set_visible(False)
        self.bg_yellow = pygame.image.load("bg_yellow.png")
        self.bg_yellow.convert()
        self.bg_black = pygame.image.load("bg_black.png")
        self.bg_black.convert()
        bg = self.bg_black
        self.screen.blit(bg, (0, 0))
        pygame.display.update()


    def clear(self):
        pass

    def drawScore(self, info):
        self.clear()
        font = pygame.font.Font(None, 500)
        top = info.black_goals % 10
        bottom = info.yellow_goals % 10
        bg = self.bg_black
        offsetx = -95
        offsety = -160

        # Clean background area
        x, y = (1170 + offsetx, 360 + offsety)
        self.screen.blit(bg, (x, y), (x, y, 190, 290))
        x2, y2 = (1170 + offsetx, 730 + offsety)
        self.screen.blit(bg, (x2, y2), (x2, y2, 190, 290))
        x3, y3 = (700, 70)
        self.screen.blit(bg, (x3 + 400, y3), (x3 + 400, y3, 300, 70))

        ttop = font.render(str(top), True, (255, 255, 255))
        tbottom = font.render(str(bottom), True, (255, 255, 255))

        self.screen.blit(ttop, (x, y))
        self.screen.blit(tbottom, (x2, y2))

        small_font = pygame.font.Font(None, 100)
        last_goal = small_font.render(str(info.time_goal), True, (255, 255, 255))
        self.screen.blit(last_goal, (700, 70))

        # Update the display
        pygame.display.update()
