import time
import pygame
from iohandler.io_base import IOBase

class IOKeyboard(IOBase):

    key_map = {
        pygame.K_z: 'YD',
        pygame.K_q: 'YI',
        pygame.K_c: 'BD',
        pygame.K_e: 'BI',
        pygame.K_s: 'OK',
        pygame.K_KP1: 'YD',
        pygame.K_KP7: 'YI',
        pygame.K_KP3: 'BD',
        pygame.K_KP9: 'BI',
        pygame.K_KP5: 'OK'
    }

    def reader_thread(self):
        while True:
            e = pygame.event.wait()
            if e.type == pygame.QUIT:
                self.read_queue.put({'type': 'quit'})
            elif e.type == pygame.KEYDOWN or e.type == pygame.KEYUP:
                if e.key in self.key_map:
                    command = self.key_map[e.key]
                    if e.type == pygame.KEYDOWN:
                        command += '_D'
                    else:
                        command += '_U'
                    self.read_queue.put({'type': 'input_command', 'source': 'keyboard', 'value': command})

    def writer_thread(self):
        while True:
            self.write_queue.get()
            # FIXME: What to do here? Make the num/caps/scroll lock keys blink? :P
            pass
