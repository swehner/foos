import foos.config as config
import hipchat
import logging
from foos import utils
import plugins.bot

logger = logging.getLogger(__name__)


class Plugin(plugins.bot.Plugin):
    def __init__(self, bus):
        super().__init__(bus)
        self.hc = hipchat.HipChat(token=config.hipchat_token)
        self.room = config.hipchat_room
        self.name = 'FoosBot'

    def send_message(self, msg, color='yellow', notify=False):
        logger.info("Sending Hipchat message: %s" % msg)
        try:
            self.hc.message_room(self.room, self.name, msg, color=color, notify=notify)
        except Exception as e:
            logger.error(e)
