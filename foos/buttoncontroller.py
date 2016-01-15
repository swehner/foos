import time
import queue
from threading import Thread
from .bus import Bus, Event

class Buttons:
    """Class to manage the state of the buttons and the needed logic"""

    def __init__(self, bus, upload_delay=0.6):
        self.upload_delay = upload_delay
        self.queue = queue.Queue(maxsize=20)
        self.bus = bus
        self.bus.subscribe(self.enqueue, thread=False)
        self.event_table = {}
        self.is_upload = False
        Thread(daemon=True, target=self.run).start()
        
    def enqueue(self, ev):
        try:
            self.queue.put_nowait(ev)
        except queue.Full:
            pass

    def run(self):
        while True:
            while not self.queue.empty():
                ev = self.queue.get_nowait()
                self.process_event(ev)

            if 'ok' in self.event_table:
                delta = time.time() - self.event_table['ok']
                if delta > self.upload_delay:
                    if not self.is_upload:
                        self.bus.notify(Event('button_will_upload'))
                        
                    self.is_upload = True
                else:
                    self.is_upload = False

            time.sleep(0.01)
                       
    def process_event(self, ev):
        if ev.name != 'button_event' or 'state' not in ev.data:
            return

        button, state = (ev.data['btn'], ev.data['state'])

        et = self.event_table
        print("New event:", ev, et)

        now = time.time()
        if state == 'down':
            # Actions are executed on button release
            et[button] = now

        elif state == 'up':
            if button in et:
                if button != 'ok':
                    color, what = button.split('_')

                    if ('yellow_minus' in et and 'yellow_plus' in et) or ('black_minus' in et and 'black_plus' in et):
                        self.bus.notify(Event('reset_score'))
                        for key in ['yellow_minus', 'yellow_plus', 'black_minus', 'black_plus']:
                            if key in et:
                                del et[key]
                        return

                    if what == 'minus':
                        gen_event = 'decrement_score'
                    else:
                        gen_event = 'increment_score'

                    self.bus.notify(Event(gen_event, {'team': color}))
                else:
                    if self.is_upload:
                        self.bus.notify(Event('upload_request'))
                    else:
                        self.bus.notify(Event('replay_request'))

                del et[button]


