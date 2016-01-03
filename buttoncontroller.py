import time
from bus import Bus, Event
from ledcontroller import Pattern

class Buttons:
    # Class to manage the state of the buttons and the needed logic
    event_table = {}

    def __init__(self, bus, upload_delay=0.6):
        self.upload_delay = upload_delay
        self.bus = bus
        self.bus.subscribe(self.process_event, thread=True)

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
            if button == 'ok':
                # Set feedback for upload action
                pattern = [Pattern(self.upload_delay, []), Pattern(0.1, ["OK"])]
                self.bus.notify(Event("leds_mode", pattern))
            return

        if state == 'up':
            if button not in et:
               # ignore
               return

        delta = now - et[button]
        print("Press duration:", delta)

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
            self.bus.notify(Event("leds_mode", []))
            if delta < self.upload_delay:
                self.bus.notify(Event('replay_request'))
            else:
                self.bus.notify(Event('upload_request'))

        del et[button]


