# Dependency: pip install python-simple-hipchat
import config
import hipchat
from gl.foos_gui import GuiState

class HipBot(object):
    def __init__(self):
        try:
            self.hc = hipchat.HipChat(token=config.hipchat_token)
            self.room = config.hipchat_room
            self.name = 'FoosBot'
        except:
            pass


    def send_message(self, msg, color='yellow', notify=False):
        self.hc.message_room(self.room, self.name, msg, color=color, notify=notify)

    def send_info(self, state):
        try:
            if state.bScore == state.yScore == 0:
                msg = "New match!"
            else:
                msg = "Goal! Score: Black {} - {} Yellow".format(state.bScore, state.yScore)
            self.send_message(msg)
        except:
            pass
