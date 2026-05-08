from interstate75 import Interstate75
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
B_LEFT = 1
B_RIGHT = 0

# Config
DOUBLE_LOCKOUT = 40  # milliseconds
WIDTH = 64
HEIGHT = 32
SCORE_PADDING = 5

W_HALF = WIDTH // 2
W_FORTH = WIDTH // 4
W_EIGHTH = WIDTH // 8

graphics.set_font('bitmap8')

left_score = 0
right_score = 0
clock = "3:00"

class ButtonPress:
    def __init__(self, left, right):
        self.left = left
        self.right = right
        pass
    
    def get_button(self, button_num):
        return self.left if button_num is B_LEFT else self.right

def check_buttons() -> ButtonPress:
    left = i75.switch_pressed(B_LEFT)
    right = i75.switch_pressed(B_RIGHT)
    return ButtonPress(left, right)

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

    pressed = check_buttons()
    double = pressed.left and pressed.right
    any_pressed = pressed.left or pressed.right

    if (not double and any_pressed):
        waiting_for = B_LEFT if pressed.right else B_RIGHT 
        start = time.ticks_ms()
        while True:
            hit = check_buttons().get_button(waiting_for)
            # If a double was hit, register it
            if (hit):
                double = True
                break

            # If we're over the double lockout time, stop checking for doubles.
            if time.ticks_diff(time.ticks_ms(), start) > DOUBLE_LOCKOUT:
                break
    
    if (any_pressed):
        print(pressed.left, pressed.right, double)
        if (pressed.left or double):
            graphics.set_pen(LEFT)
            graphics.rectangle(0, 0, W_HALF, W_FORTH)
            left_score += 1

        if (pressed.right or double):
            graphics.set_pen(RIGHT)
            graphics.rectangle(W_HALF, 0, W_HALF, W_FORTH)
            right_score += 1
    
        i75.update()
        time.sleep(1)
        clear_lights()        
        clear_left_score()
        clear_right_score()

    left_num = str(left_score)
    right_num = str(right_score)
    left_x = SCORE_PADDING
    right_x = WIDTH - graphics.measure_text(right_num, 1) - SCORE_PADDING

    graphics.set_pen(TIMER)
    graphics.text(clock, clock_x, W_FORTH, scale=1)

    graphics.set_pen(SCORE)
    graphics.text(left_num, left_x, W_FORTH, scale=1)
    graphics.text(right_num, right_x, W_FORTH, scale=1)
    i75.update()


