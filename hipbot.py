import config
import hipchat
import traceback
from gl.foos_gui import GuiState

class HipBot(object):
    def __init__(self):
        self.hc = hipchat.HipChat(token=config.hipchat_token)
        self.room = config.hipchat_room
        self.name = 'FoosBot'

    def send_message(self, msg, color='yellow', notify=False):
        print("Sending Hipchat message:", msg)
        if config.hipchat_enabled:
            self.hc.message_room(self.room, self.name, msg, color=color, notify=notify)

    def send_info(self, state):
        try:
            if state.bScore == state.yScore == 0:
                msg = "New match!"
            else:
                msg = "Goal! Score: Yellow {} - {} Black".format(state.yScore, state.bScore)
            self.send_message(msg)
        except:
            print("Error sending hipchat message")
            traceback.print_exc()
