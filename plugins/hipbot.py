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
        self.players = {}

    def send_message(self, msg, color='yellow', notify=False):
        logger.info("Sending Hipchat message: %s" % msg)
        try:
            self.hc.message_room(self.room, self.name, msg, color=color, notify=notify)
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

        return team.capitalize() + p

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
        elif ev.name == "win_game":
            s = "%s wins %d-%d against %s!"
            winners = self.get_team_name(ev.data.get('team', None))
            lname = 'black' if ev.data.get('team', None) == 'yellow' else 'yellow'
            losers = self.get_team_name(lname)

            msg = (s % (winners, ev.data.get('yellow', 0), ev.data.get('black', 0), losers))
        else:
            return

        if msg:
            self.send_message(msg)
