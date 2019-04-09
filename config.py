""" Override config values from config_base using this file """
from config_base import *


""" Configure the plugin set """

# -- Enable camera, replays and video motiondetector
#plugins.update(set(['replay', 'camera', 'motiondetector']))
#camera_preview = "-p 0,0,128,72"

# -- Modify this to tune your camera settings - see raspivid --help for more info
#camera_extra_params = "--ev 7"
#draw_bg_with_dispmanx = False

blank_console = False

# -- Enable league sync with server
#plugins.add('league_sync')

# -- Enable Youtube video upload
#plugins.add('upload')

# -- Enable hipchat bot
#plugins.add('hipbot')

# -- Enable Arduino serial input and led output
#plugins.add('io_serial')

# -- Enable auto-TV standby
#plugins.add('standby')

# -- Enable IO using Raspberry Pi. Change pin numbers according to your setup.
# -- PWM output for the IR led is BCM18 (hardware PWM pin)
plugins.add('io_raspberry')
io_raspberry_pins = {
    "irbarrier_team_black": 8,      # Physical pin 8
    "irbarrier_team_yellow": 26,    # Physical pin 26
    "yellow_plus" : 10,             # Physical pin 10
    "yellow_minus": 16,             # Physical pin 16
    "black_plus": 3,                # Physical pin 3
    "black_minus": 22,              # Physical pin 22
    "ok_button": 24,                # Physical pin 24
}

# -- Modify clock format: see strftime
#clock_format = "%-I:%M %p" # 12 hour format

""" Configure team names and colors """
team_names = {"yellow": "bleus", "black": "rouges"}
team_colors = {"yellow": (0.1, 0.1, 0.4), "black": (0.7, 0, 0)}

# game modes: tuples of (winning score, timeout in minutes)
game_modes = [(None, None), (5, None), (7, None), (10, None), (3, 120)]

# Customize winner strings
winner_strings = ["Victoire des {}!","Des kings les {}!","Les {} déchirent!","Trop forts les {}!","Faites place aux {}!","You rock !!!"]

""" Configure paths """

# -- replay path
replay_path = "./replay"
replay_fps = 25
save_replays = True

# -- or the location of the file_handler
#log["handlers"]["file_handler"]["filename"] = ""


""" Override tokens for plugins """

#hipchat_token = 'your_token'
#hipchat_room = 'your_room_id'

league_url = 'http://localhost:4567/api'
league_apikey = 'API_KEY_HERE'

#slack_webhook = 'https://hooks.slack.com/services/BLAW/BLAW'
