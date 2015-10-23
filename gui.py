import os
import pygame
import time
import random
 
class pyscope :
    screen = None;
    
    def __init__(self):
        "Ininitializes a new pygame screen using the framebuffer"
        # Based on "Python GUI in Linux frame buffer"
        # http://www.karoltomala.com/blog/?p=679
        disp_no = os.getenv("DISPLAY")
        if disp_no:
            print "I'm running under X display = {0}".format(disp_no)
        
        # Check which frame buffer drivers are available
        # Start with fbcon since directfb hangs with composite output
        drivers = ['fbcon', 'directfb', 'svgalib']
        found = False
        for driver in drivers:
            # Make sure that SDL_VIDEODRIVER is set
            if not os.getenv('SDL_VIDEODRIVER'):
                os.putenv('SDL_VIDEODRIVER', driver)
            #try:
            pygame.display.init()
            #except pygame.error:
            #    print 'Driver: {0} failed.'.format(driver)
            #    continue
            found = True
            break
    
        if not found:
            raise Exception('No suitable video driver found!')
        
        size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        print "Framebuffer size: %d x %d" % (size[0], size[1])
        self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
        # Clear the screen to start
        self.screen.fill((0, 0, 0))        
        # Initialise font support
        pygame.font.init()
        # Render the screen
        pygame.display.update()
        pygame.mouse.set_visible(False)
        self.bg_white = pygame.image.load("bg_white.png")
        self.bg_white.convert()
        self.bg_black = pygame.image.load("bg_black.png")
        self.bg_black.convert()
 
    def __del__(self):
        "Destructor to make sure pygame shuts down, etc."
 
    def clear(self):
        pass


    def drawScore(self, score):
        self.clear()
        font = pygame.font.Font(None, 500)
        top = score["BLACK"]
        bottom = score["WHITE"]
        bg = self.bg_black
        if score["WHITE"] > score["BLACK"]:
          (top, bottom) = (bottom, top)  
          bg = self.bg_white

    	self.screen.blit(bg, (0,0))
        ttop = font.render(str(top), True, (255, 255, 255))
        tbottom = font.render(str(bottom), True, (255, 255, 255))
	
        offsetx=-95
        offsety=-160
        self.screen.blit(ttop, (1170 + offsetx, 360 + offsety))
        self.screen.blit(tbottom, (1170 + offsetx, 730 + offsety))
        # Update the display
        pygame.display.update()
  
