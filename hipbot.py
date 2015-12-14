# Dependency: pip install python-simple-hipchat
import config
import hipchat
from gl.foos_gui import GuiState

class HipBot(object):
    def __init__(self):
        self.init = False
        try:
            self.hc = hipchat.HipChat(token=config.hipchat_token)
            self.room = config.hipchat_room
            self.name = 'FoosBot'
            self.init = True
        except:
            pass


    def send_message(self, msg, color='yellow', notify=False):
        self.hc.message_room(self.room, self.name, msg, color=color, notify=notify)

    def send_info(self, state):
        if not self.init:
            return
        if state.bScore == state.yScore == 0:
            msg = "New match!"
        else:
            msg = "Goal! Score: Black {} - {} Yellow".format(state.bScore, state.yScore)
        self.send_message(msg)
