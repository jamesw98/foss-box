"""
GPIO Pin Config
Update these to match whatever GPIO pins you're using
"""
WEAPON_LEFT_PIN = 21
WEAPON_RIGHT_PIN = 19
BELL_LEFT_PIN = 27
BELL_RIGHT_PIN = 26
BUZZER_PIN = 17

"""
Bluetooth Config
"""
# Bluetooth box ID. The box will appear as "FossBox_<id>" in the PWA Bluetooth menu. This can *technically* be anything
# but, it will appear on the box in the bottom right corner until a BT connection is made, so don't make it too long.
BLUETOOTH_ID = "315"
# Should BT be enabled? I would not recommend disabling this.
BLUETOOTH_ENABLED = True
# Should we log debug messages?
BLUETOOTH_DEBUG = False
# Should we display the ID of the box on the box until a ref connects? Useful if you have multiple in the same room.
BT_ID_ENABLED = True

"""
General Config - You should not need to mess with any of this. 
"""
# How long the lights stay illuminated after a touch.
ILLUM_TIME = 2
# Double lockout time, default is 1/25 of a second/40ms. Don't mess with this unless you're trying some wacky fencing.
DOUBLE_LOCKOUT = 40
# Side padding for the score, in pixels.
SIDE_PADDING = 5
# Top padding for the score, in pixels.
TOP_PADDING = 3
# Should the clock be enabled?
CLOCK_ENABLED = True
# Should the scores be enabled?
SCORE_ENABLED = True
# Clock start time, in seconds.
CLOCK_SECONDS = 180

"""
Color Config
"""
BLACK = (0, 0, 0)
LEFT_COLOR = (255, 0, 0)
RIGHT_COLOR = (0, 255, 0)
SCORE_COLOR = (255, 255, 255)
TIMER_COLOR = (255, 255, 255)
GROUND_COLOR = (255, 100, 0)
BT_CONNECTED_COLOR = (0, 80, 255)

"""
:)
"""
EASTER_EGG_QUOTES = [
    "Fire!\nWalk with me!",
    "Damn fine\ncup of\ncoffee!",
    "There was a\nfish, in the\npercolator!",
    "The owls are\nnot what\nthey seem.",
    "I told them\nto fix their\nhearts or\ndie.",
    "It is\nhappening\nagain.",
    "That gum you\nlike is\ncoming back\nin style.",
]