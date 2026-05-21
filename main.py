from FossBox import FossBox
from PimoroniI75 import PimoroniI75

def micro_python_button(pin_num):
    from machine import Pin
    return lambda: not Pin(pin_num, Pin.IN, Pin.PULL_UP).value()

disp = PimoroniI75(width=64, height=32)
w_left = micro_python_button(21)
w_right = micro_python_button(19)
b_left = micro_python_button(27)
b_right = micro_python_button(26)

FossBox(disp, w_left, w_right, b_left, b_right).run()