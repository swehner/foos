import config
import hipchat
import traceback


class HipBot(object):
    def __init__(self, bus):
        self.bus = bus
        self.bus.subscribe(self.process_event, thread=True)
        self.hc = hipchat.HipChat(token=config.hipchat_token)
        self.room = config.hipchat_room
        self.name = 'FoosBot'

    def send_message(self, msg, color='yellow', notify=False):
        print("Sending Hipchat message:", msg)
        if config.hipchat_enabled:
            self.hc.message_room(self.room, self.name, msg, color=color, notify=notify)

    def process_event(self, ev):
        if ev.name == 'score_goal':
            msg = "Goal {}! Score: Yellow {} - {} Black".format(ev.data['team'], ev.data['yellow'], ev.data['black'])
        elif ev.name == 'score_reset':
            msg = "New match!"
        elif ev.name == 'upload_ok':
            msg = "New replay uploaded: " + ev.data
        else:
            return

        self.send_message(msg)
