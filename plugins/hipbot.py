import config
import hipchat
import traceback
import logging

logger = logging.getLogger(__name__)


class Plugin(object):
    def __init__(self, bus):
        self.bus = bus
        self.bus.subscribe(self.process_event, thread=True)
        self.hc = hipchat.HipChat(token=config.hipchat_token)
        self.room = config.hipchat_room
        self.name = 'FoosBot'

    def send_message(self, msg, color='yellow', notify=False):
        logger.info("Sending Hipchat message: %s", msg)
        try:
            self.hc.message_room(self.room, self.name, msg, color=color, notify=notify)
        except Exception as e:
            logger.error("Hipbot error %s", e)

    def process_event(self, ev):
        if ev.name == 'people_start_playing':
            msg = "People start playing..."
        elif ev.name == 'people_stop_playing':
            msg = "People have left."
        elif ev.name == 'upload_ok':
            msg = "New replay uploaded: " + ev.data
        elif ev.name == "win_game":
            s = "%s wins %d-%d!"
            msg = (s % (ev.data.get('team', None).capitalize(),
                        ev.data.get('yellow', 0), ev.data.get('black', 0)))
        else:
            return

        self.send_message(msg)
