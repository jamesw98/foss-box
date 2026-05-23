import time

def format_clock(s):
   return "{:d}:{:02d}".format(s // 60, s % 60)

def ticks_ms():
    try:
        return time.ticks_ms()           # MicroPython
    except AttributeError:
        return int(time.monotonic() * 1000)  # CircuitPython

def ticks_diff(new, old):
    try:
        return time.ticks_diff(new, old)  # MicroPython (handles wraparound)
    except AttributeError:
        return new - old

def ticks_add(t, delta):
    try:
        return time.ticks_add(t, delta)   # MicroPython
    except AttributeError:
        return t + delta

