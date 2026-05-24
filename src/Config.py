"""
GPIO Pin Config
Update these to match whatever GPIO pins you're using
"""
WEAPON_LEFT_PIN = 21
WEAPON_RIGHT_PIN = 19
BELL_LEFT_PIN = 27
BELL_RIGHT_PIN = 26

"""
General Config
"""
# Double lockout time, default is 1/25 of a second/40ms. Don't mess with this unless you're trying some wacky fencing.
DOUBLE_LOCKOUT = 40
# How long the lights stay illuminated after a touch.
ILLUM_TIME = 2
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
Bluetooth Config
"""
# Should BT be enabled?
BLUETOOTH_ENABLED = True
# Should we log debug messages?
BLUETOOTH_DEBUG = False
# Bluetooth box ID. The box will appear as "FossBox_<id>" in the PWA Bluetooth menu. 
BLUETOOTH_ID = "237"
