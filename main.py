from interstate75 import Interstate75
from bluetooth import BLEReceiver
from machine import Pin
import time

i75 = Interstate75(display=Interstate75.DISPLAY_INTERSTATE75_64X32, color_order=Interstate75.COLOR_ORDER_RGB)
graphics = i75.display
graphics.set_font('bitmap8')

# Colors
SCORE = graphics.create_pen(89, 6, 200)
BLACK = graphics.create_pen(0, 0, 0)
TIMER = graphics.create_pen(255, 255, 255)
RIGHT = graphics.create_pen(0,255,0)
LEFT = graphics.create_pen(255,0,0)
GROUND = graphics.create_pen(255, 100, 0)

# Config
DOUBLE_LOCKOUT = 40 # In milliseconds
ILLUMINATED_TIME = 3 # How long the lights stay on, in seconds
WIDTH = 64 # Width, in pixels, of the matrix
HEIGHT = 32 # Height, in pixels of the matrix
SCORE_SIDE_PADDING = 5 # Padding from the edges of the matrix for the score numbers
SCORE_TOP_PADDING = 3 # Padding from the bottom of the scoring lights, in pixels
CLOCK_ENABLED = False 
SCORE_ENABLED = True

# Pin setup - Change pin numbers here if needed
WEAPON_LEFT = Pin(21, Pin.IN, Pin.PULL_UP)
WEAPON_RIGHT = Pin(19, Pin.IN, Pin.PULL_UP)
BELL_LEFT = Pin(27, Pin.IN, Pin.PULL_UP)
BELL_RIGHT = Pin(26, Pin.IN, Pin.PULL_UP)

# Text related constants
W_HALF = WIDTH // 2
W_FORTH = WIDTH // 4
W_EIGHTH = WIDTH // 8

left_score = 0
right_score = 0
clock_seconds = 180
last_tick = time.ticks_ms()

class ButtonPress:
    def __init__(self, left, right, bell_left, bell_right):
        self.left = left
        self.right = right
        self.bell_left = bell_left
        self.bell_right = bell_right
        pass
    
    def get_button(self, button_num):
        return self.left if button_num is WEAPON_LEFT else self.right

def format_clock(seconds):
    return "{:d}:{:02d}".format(seconds // 60, seconds % 60)

clock = format_clock(clock_seconds)

def check_buttons(left, right, bell_left, bell_right) -> ButtonPress:
    return ButtonPress(not left.value() and bell_right.value(), not right.value() and bell_left.value(), not bell_left.value(), not bell_right.value())

def clear_lights():
    graphics.set_pen(BLACK)
    graphics.rectangle(0, 0, WIDTH, W_FORTH)
    i75.update()

def clear_clock():
    text_width = graphics.measure_text(clock, 1)
    x = (WIDTH - text_width) // 2
    graphics.set_pen(BLACK)
    graphics.rectangle(x, W_FORTH, text_width, W_EIGHTH)
    i75.update()

def clear_left_score():
    w = graphics.measure_text(left_num, 1)
    graphics.set_pen(BLACK)
    graphics.rectangle(SCORE_SIDE_PADDING, W_FORTH + SCORE_TOP_PADDING, w, W_EIGHTH)
    i75.update()

def clear_right_score():
    w = graphics.measure_text(right_num, 1)
    x = WIDTH - w - SCORE_SIDE_PADDING
    graphics.set_pen(BLACK)
    graphics.rectangle(x, W_FORTH + SCORE_TOP_PADDING, w, W_EIGHTH)
    i75.update()

def clear_text():
    graphics.set_pen(BLACK)
    graphics.rectangle(0, W_FORTH, WIDTH, W_FORTH)
    i75.update()

while True:

    left_num = str(left_score)
    right_num = str(right_score)

    left_x = SCORE_SIDE_PADDING
    clock_x = (WIDTH - graphics.measure_text(clock, 1)) // 2
    right_x = WIDTH - graphics.measure_text(right_num, 1) - SCORE_SIDE_PADDING

    pressed = check_buttons(WEAPON_LEFT, WEAPON_RIGHT, BELL_LEFT, BELL_RIGHT)
    double = pressed.left and pressed.right
    any_valid = pressed.left or pressed.right
    any_bell = pressed.bell_left or pressed.bell_right

    if any_bell:
        if pressed.bell_right:
            graphics.set_pen(GROUND)
            graphics.rectangle(0, 0, 3, W_FORTH)

        if pressed.bell_left:
            graphics.set_pen(GROUND)
            graphics.rectangle(WIDTH - 3, 0, 3, W_FORTH)
        i75.update()
        clear_lights()

    if any_valid and not double:
        waiting_for = WEAPON_LEFT if pressed.right else WEAPON_RIGHT
        start = time.ticks_ms()
        while True:
            hit = check_buttons(WEAPON_LEFT, WEAPON_RIGHT, BELL_LEFT, BELL_RIGHT).get_button(waiting_for)
            # If a double was hit, register it
            if hit:
                double = True
                break

            # If we're over the double lockout time, stop checking for doubles.
            if time.ticks_diff(time.ticks_ms(), start) >= DOUBLE_LOCKOUT:
                break
    
    if any_valid:
        if pressed.left or double:
            graphics.set_pen(LEFT)
            graphics.rectangle(0, 0, W_HALF, W_FORTH)
            left_score += 1

        if pressed.right or double:
            graphics.set_pen(RIGHT)
            graphics.rectangle(W_HALF, 0, W_HALF, W_FORTH)
            right_score += 1
    
        i75.update()
        time.sleep(ILLUMINATED_TIME)
        last_tick = time.ticks_ms()
        clear_lights()
        clear_left_score()
        clear_right_score()

    if CLOCK_ENABLED and time.ticks_diff(time.ticks_ms(), last_tick) >= 1000 and clock_seconds > 0:
        clear_clock()
        clock_seconds -= 1
        last_tick = time.ticks_add(last_tick, 1000)
        clock = format_clock(clock_seconds)

    left_num = str(left_score)
    right_num = str(right_score)
    left_x = SCORE_SIDE_PADDING
    right_x = WIDTH - graphics.measure_text(right_num, 1) - SCORE_SIDE_PADDING
    clock_x = (WIDTH - graphics.measure_text(clock, 1)) // 2

    if CLOCK_ENABLED:
        graphics.set_pen(TIMER)
        graphics.text(clock, clock_x, W_FORTH, scale=1)

    if SCORE_ENABLED:
        graphics.set_pen(SCORE)
        graphics.text(left_num, left_x, W_FORTH + SCORE_TOP_PADDING, scale=1)
        graphics.text(right_num, right_x, W_FORTH + SCORE_TOP_PADDING, scale=1)

    i75.update()