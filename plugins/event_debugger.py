import logging
import json

from foos.bus import Bus, Event
logger = logging.getLogger(__name__)


class Plugin:
    def __init__(self, bus):
        self.log_events = ['decrement_score',
                           'people_start_playing', 'people_stop_playing']
        bus.subscribe(self.process_event, thread=True)

    def process_event(self, ev):
        do_log = ev.name in self.log_events
        do_log |= (ev.name == 'button_event' and ev.data['btn'] == 'goal')

        if do_log:
            logger.debug("%s: %s", ev.name, str(ev.data))
