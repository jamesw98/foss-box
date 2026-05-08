from interstate75 import Interstate75
import time

i75 = Interstate75(display=Interstate75.DISPLAY_INTERSTATE75_64X32, color_order=Interstate75.COLOR_ORDER_RGB)
graphics = i75.display

# Colors 
PURPLE = graphics.create_pen(2, 0, 255)
BLACK = graphics.create_pen(0, 0, 0)
WHITE = graphics.create_pen(255, 255, 255)
GREEN = graphics.create_pen(0,255,0)
RED = graphics.create_pen(255,0,0)

# Buttons
LEFT = 1
RIGHT = 0

# Config
# !!! Do not edit this unless you're doing some wacky experimental fencing. 
DOUBLE_LOCKOUT = 40  # milliseconds

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
        return self.left if button_num is LEFT else self.right

def check_buttons() -> ButtonPress:
    left = i75.switch_pressed(LEFT)
    right = i75.switch_pressed(RIGHT)
    return ButtonPress(left, right)

def clear_lights():
    graphics.set_pen(BLACK)
    graphics.rectangle(0,0,64,16)
    i75.update()

def clear_clock():
    w = graphics.measure_text(clock, 1)
    x = (64 - w) // 2
    graphics.set_pen(BLACK)
    graphics.rectangle(x, 16, w, 8)
    i75.update()

def clear_left_score():
    w = graphics.measure_text(left_num, 1)
    graphics.set_pen(BLACK)
    graphics.rectangle(5, 16, w, 8)
    i75.update()

def clear_right_score():
    w = graphics.measure_text(right_num, 1)
    x = 64 - w - 5
    graphics.set_pen(BLACK)
    graphics.rectangle(x, 16, w, 8)
    i75.update()

def clear_text():
    graphics.set_pen(BLACK)
    graphics.rectangle(0, 16, 64, 16)
    i75.update()

while True:

    left_num = str(left_score)
    right_num = str(right_score)

    left_x = 5
    clock_x = (64 - graphics.measure_text(clock, 1)) // 2
    right_x = 64 - graphics.measure_text(right_num, 1) - 5

    pressed = check_buttons()
    double = pressed.left and pressed.right
    any_pressed = pressed.left or pressed.right

    if (not double and any_pressed):
        waiting_for = LEFT if pressed.right else RIGHT 
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
            graphics.set_pen(RED)
            graphics.rectangle(0,0,32,16)
            left_score += 1

        if (pressed.right or double):
            graphics.set_pen(GREEN)
            graphics.rectangle(32,0,32,16)
            right_score += 1
    
        i75.update()
        time.sleep(1)
        clear_lights()        
        clear_left_score()
        clear_right_score()

    left_num = str(left_score)
    right_num = str(right_score)
    left_x = 5
    right_x = 64 - graphics.measure_text(right_num, 1) - 5

    graphics.set_pen(WHITE)
    graphics.text(clock, clock_x, 16, scale=1)

    graphics.set_pen(PURPLE)
    graphics.text(left_num, left_x, 16, scale=1)
    graphics.text(right_num, right_x, 16, scale=1)
    i75.update()


