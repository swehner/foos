import foos.config as config
import hipchat
import logging
import requests
import json
from foos import utils

logger = logging.getLogger(__name__)


class Plugin(object):
    def __init__(self, bus):
        self.bus = bus
        self.bus.subscribe(self.process_event, thread=True)
        self.players = {}

    def send_message(self, msg, color='yellow', notify=False):
        logger.info("Sending Slack message: %s" % msg)
        try:
            payload = {"text": msg}
            post_data = {"payload": json.dumps(payload)}
            r = requests.post(config.slack_webhook, data=post_data)
        except Exception as e:
            logger.error(e)

    def get_players(self, team):
        return self.players.get(team, [])

    def get_team_name(self, team):
        players = self.get_players(team)
        if len(players) > 0:
            p = " (" + ", ".join(players) + ")"
        else:
            p = ""

        return utils.teamName(team).capitalize() + p

    def process_event(self, ev):
        msg = None
        if ev.name == 'people_start_playing':
            msg = "People start playing..."
        elif ev.name == 'people_stop_playing':
            msg = "People have left."
        elif ev.name == 'upload_ok':
            msg = "New replay uploaded: " + ev.data
        elif ev.name == "set_players":
            self.players = ev.data
        elif ev.name == "start_competition":
            msg = "%s game starts now: %s" % (ev.data.get("division", ""),
                                              ", ".join(ev.data.get("players", [])))
        elif ev.name == "end_competition":
            ps = sorted(ev.data.get('points', {}).items(), key=lambda x: x[1], reverse=True)
            text = ', '.join(map(lambda x: "%s: %s" % tuple(x), ps))
            msg = "Official game ends, points: " + text
        elif ev.name == "win_game":
            s = "%s wins! %s %d-%d %s!"
            msg = (s % (utils.teamName(ev.data.get('team', "")).capitalize(),
                        self.get_team_name('yellow'), ev.data.get('yellow', 0),
                        ev.data.get('black', 0), self.get_team_name('black')))
        elif ev.name == "cancel_competition":
            msg = "Official game cancelled"
        else:
            return

        if msg:
            self.send_message(msg)
