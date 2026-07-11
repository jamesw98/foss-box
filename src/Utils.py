import time
import json
import Config

try:
    import uos as uos
except ImportError:
    import os as uos

# MicroPython doesn't have enums apparently, sad!
Ref = 0
SelfRef = 1
DumbBox = 2

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

def json_load_runtime_config():
    if "runtime_config.json" in uos.listdir():
        with open("runtime_config.json", "rb") as f:
            return json.loads(f.read().decode("utf-8").strip())
    return {}

def json_save_runtime_config(config):
    with open("runtime_config.json", "w") as f:
        json.dump(config, f)

def json_mode_check():
    config = json_load_runtime_config()
    return config.get("mode", Ref)

def json_update_prop(prop_name, prop_val):
    config = json_load_runtime_config()
    config[prop_name] = prop_val
    json_save_runtime_config(config)

def config_check():
    updated = False
    config = json_load_runtime_config()
    if "weapon_left" not in config or Config.RT_CONF_OVERWRITE:
        config["weapon_left"] = Config.WEAPON_LEFT_PIN
        updated = True
    if "weapon_right" not in config or Config.RT_CONF_OVERWRITE:
        config["weapon_right"] = Config.WEAPON_RIGHT_PIN
        updated = True
    if "bell_left" not in config or Config.RT_CONF_OVERWRITE:
        config["bell_left"] = Config.BELL_LEFT_PIN
        updated = True
    if "bell_right" not in config or Config.RT_CONF_OVERWRITE:
        config["bell_right"] = Config.BELL_RIGHT_PIN
        updated = True
    if "buzzer" not in config or Config.RT_CONF_OVERWRITE:
        config["buzzer"] = Config.BUZZER_PIN
        updated = True

    if updated:
        json_save_runtime_config(config)

    return config