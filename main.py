from interstate75 import Interstate75
from bluetooth import BLEReceiver
from machine import Pin
import time

i75 = Interstate75(display=Interstate75.DISPLAY_INTERSTATE75_64X32, color_order=Interstate75.COLOR_ORDER_RGB)
graphics = i75.display

# Colors
SCORE = graphics.create_pen(89, 6, 200)
BLACK = graphics.create_pen(0, 0, 0)
TIMER = graphics.create_pen(255, 255, 255)
RIGHT = graphics.create_pen(0,255,0)
LEFT = graphics.create_pen(255,0,0)

# Buttons
B_LEFT_WEAPON = 1
B_RIGHT_WEAPON = 0

# Config
DOUBLE_LOCKOUT = 40  # milliseconds
WIDTH = 64
HEIGHT = 32
SCORE_PADDING = 5
CLOCK_ENABLED = True

W_HALF = WIDTH // 2
W_FORTH = WIDTH // 4
W_EIGHTH = WIDTH // 8

graphics.set_font('bitmap8')

BUTTON_LEFT = Pin(21, Pin.IN, Pin.PULL_UP)
BUTTON_RIGHT = Pin(19, Pin.IN, Pin.PULL_UP)

left_score = 0
right_score = 0
clock_seconds = 180
last_tick = time.ticks_ms()

def format_clock(seconds):
    return "{:d}:{:02d}".format(seconds // 60, seconds % 60)

clock = format_clock(clock_seconds)

btn_custom = Pin(20, Pin.IN, Pin.PULL_UP)

class ButtonPress:
    def __init__(self, left, right):
        self.left = left
        self.right = right
        pass
    
    def get_button(self, button_num):
        return self.left if button_num is B_LEFT_WEAPON else self.right

def check_buttons(left, right) -> ButtonPress:
    return ButtonPress(not left.value(), not right.value())

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
    graphics.rectangle(SCORE_PADDING, W_FORTH, w, W_EIGHTH)
    i75.update()

def clear_right_score():
    w = graphics.measure_text(right_num, 1)
    x = WIDTH - w - SCORE_PADDING
    graphics.set_pen(BLACK)
    graphics.rectangle(x, W_FORTH, w, W_EIGHTH)
    i75.update()

def clear_text():
    graphics.set_pen(BLACK)
    graphics.rectangle(0, W_FORTH, WIDTH, W_FORTH)
    i75.update()

while True:

    left_num = str(left_score)
    right_num = str(right_score)

    left_x = SCORE_PADDING
    clock_x = (WIDTH - graphics.measure_text(clock, 1)) // 2
    right_x = WIDTH - graphics.measure_text(right_num, 1) - SCORE_PADDING

    pressed = check_buttons(BUTTON_LEFT, BUTTON_RIGHT)
    double = pressed.left and pressed.right
    any_pressed = pressed.left or pressed.right

    if any_pressed and not double:
        waiting_for = B_LEFT_WEAPON if pressed.right else B_RIGHT_WEAPON 
        start = time.ticks_ms()
        while True:
            hit = check_buttons(BUTTON_LEFT, BUTTON_RIGHT).get_button(waiting_for)
            # If a double was hit, register it
            if hit:
                double = True
                break

            # If we're over the double lockout time, stop checking for doubles.
            if time.ticks_diff(time.ticks_ms(), start) >= DOUBLE_LOCKOUT:
                break
    
    if any_pressed:
        if pressed.left or double:
            graphics.set_pen(LEFT)
            graphics.rectangle(0, 0, W_HALF, W_FORTH)
            left_score += 1

        if pressed.right or double:
            graphics.set_pen(RIGHT)
            graphics.rectangle(W_HALF, 0, W_HALF, W_FORTH)
            right_score += 1
    
        i75.update()
        time.sleep(3)
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
    left_x = SCORE_PADDING
    right_x = WIDTH - graphics.measure_text(right_num, 1) - SCORE_PADDING
    clock_x = (WIDTH - graphics.measure_text(clock, 1)) // 2

    if CLOCK_ENABLED:
        graphics.set_pen(TIMER)
        graphics.text(clock, clock_x, W_FORTH, scale=1)

    graphics.set_pen(SCORE)
    graphics.text(left_num, left_x, W_FORTH, scale=1)
    graphics.text(right_num, right_x, W_FORTH, scale=1)

    i75.update()


