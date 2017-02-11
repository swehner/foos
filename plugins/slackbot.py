import foos.config as config
import hipchat
import logging
import requests
import json
from foos import utils
import plugins.bot

logger = logging.getLogger(__name__)


class Plugin(plugins.bot.Plugin):
    def send_message(self, msg, color='yellow', notify=False):
        logger.info("Sending Slack message: %s" % msg)
        try:
            payload = {"text": msg}
            post_data = {"payload": json.dumps(payload)}
            r = requests.post(config.slack_webhook, data=post_data)
        except Exception as e:
            logger.error(e)
