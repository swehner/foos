import logging

logger = logging.getLogger(__name__)


class Plugin:
    def __init__(self, bus):
        self.log_events = ['decrement_score', 'goal_event',
                           'people_start_playing', 'people_stop_playing']
        bus.subscribe(self.process_event, thread=True, subscribed_events=self.log_events)

    def process_event(self, ev):
        logger.debug("%s: %s", ev.name, str(ev.data))
