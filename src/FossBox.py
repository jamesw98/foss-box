import Utils
import time
import Config
import random

try:
    import uos as uos
except ImportError:
    import os as uos

if Config.BLUETOOTH_ENABLED:
    import Bluetooth

class FossBox:
    def __init__(self, disp, weapon_left, weapon_right, bell_left, bell_right):
        self.disp = disp
        self.weapon_left = weapon_left
        self.weapon_right = weapon_right
        self.bell_left = bell_left
        self.bell_right = bell_right

        self.width = self.disp.width
        self.height = self.disp.height
        self.half = self.width // 2
        self.forth = self.width // 4
        self.eighth = self.width // 8

        self.left_score = 0
        self.right_score = 0
        self.clock_seconds = Config.CLOCK_SECONDS
        self.clock = Utils.format_clock(self.clock_seconds)
        self.last_tick = Utils.ticks_ms()
        self.clock_running = False
        self.current_period = 0
        self.priority = False

        self.bt = None
        self.bt_was_connected = False
        if Config.BLUETOOTH_ENABLED:
            try:
                self.bt = Bluetooth.BLEReceiver()
            except Exception as e:
                print("BLE init failed:", e)

        self.mode = Utils.json_mode_check()

    """
    Checks for valid touches and bell guard touches. 
    """
    def check(self):
        return self.weapon_left() and not self.bell_right(), self.weapon_right() and not self.bell_left(), self.bell_left(), self.bell_right()

    """
    Clears the touche indicator lights. 
    """
    def clear_lights(self):
        self.disp.fill_rect(0, 0, self.width, self.forth, Config.BLACK)
        self.disp.update()

    """
    Clears the clock.
    """
    def clear_clock(self):
        text_width = self.disp.measure_text(self.clock, 1)
        starting_x = (self.width - text_width) // 2
        self.disp.fill_rect(starting_x, self.forth + Config.TOP_PADDING, text_width, self.eighth, Config.BLACK)
        self.disp.update()

    """
    Clears the period indicator below the clock.
    """
    def clear_period(self):
        self.disp.fill_rect(0, self.height - 3, Config.MAX_PERIODS * 4, 2, Config.BLACK)
        self.disp.update()

    """
    Clears the left or right score.
    """
    def clear_score(self, score, side):
        if score < 0:
            return
        text_width = self.disp.measure_text(str(score), 1)
        starting_x = Config.SIDE_PADDING if side == 'left' else self.width - text_width - Config.SIDE_PADDING
        self.disp.fill_rect(starting_x, self.forth + Config.TOP_PADDING, text_width, self.eighth, Config.BLACK)
        self.disp.update()

    """
    Draws the Bluetooth connected indicator.
    """
    def draw_bt_indicator(self):
        self.disp.fill_rect(self.width - 2, self.height - 2, 2, 2, Config.BT_CONNECTED_COLOR)
        self.disp.update()

    """
    Clears the Bluetooth connected indicator.
    """
    def clear_bt_indicator(self):
        self.disp.fill_rect(self.width - 2, self.height - 2, 2, 2, Config.BLACK)
        self.disp.update()

    """
    Draws the Bluetooth ID in the bottom right corner. Shown until a device connects.
    """
    def draw_bt_id(self):
        if not Config.BT_ID_ENABLED or self.mode == Utils.SelfRef:
            return

        text_width = self.disp.measure_text(Config.BLUETOOTH_ID, 1, font='bitmap6')
        x = self.width - text_width + 1
        y = self.height - 6
        self.disp.draw_text(Config.BLUETOOTH_ID, x, y, Config.BT_CONNECTED_COLOR, font='bitmap6')
        self.disp.update()

    """
    Clears the Bluetooth ID from the bottom right corner.
    """
    def clear_bt_id(self):
        text_width = self.disp.measure_text(Config.BLUETOOTH_ID, 1, font='bitmap6')
        x = self.width - text_width + 1
        y = self.height - 6
        self.disp.fill_rect(x, y, text_width, 6, Config.BLACK)
        self.disp.update()

    """
    Handles all the Bluetooth communication from the PWA.
    """
    def sync_bt(self):
        hi = (self.clock_seconds >> 8) & 0xFF
        lo = self.clock_seconds & 0xFF
        self.bt.notify([Bluetooth.EVT_STATE_SYNC, self.left_score, self.right_score, hi, lo])

    """
    Handles any BT commands sent by the PWA
    """
    def handle_bt_cmd(self, data):
        cmd = data[0]
        if cmd == Bluetooth.CMD_TIMER_START:
            self.clock_running = True
            self.last_tick = Utils.ticks_ms()
        elif cmd == Bluetooth.CMD_TIMER_STOP:
            self.clock_running = False
        elif cmd == Bluetooth.CMD_LEFT_INC:
            self.clear_score(self.left_score, 'left')
            self.left_score += 1
            self.sync_bt()
        elif cmd == Bluetooth.CMD_LEFT_DEC:
            if self.left_score > 0:
                self.clear_score(self.left_score, 'left')
                self.left_score -= 1
                self.sync_bt()
        elif cmd == Bluetooth.CMD_RIGHT_INC:
            self.clear_score(self.right_score, 'right')
            self.right_score += 1
            self.sync_bt()
        elif cmd == Bluetooth.CMD_RIGHT_DEC:
            if self.right_score > 0:
                self.clear_score(self.right_score, 'right')
                self.right_score -= 1
                self.sync_bt()
        elif cmd == Bluetooth.CMD_SET_TIME and len(data) >= 3:
            self.clock_running = False
            self.clear_clock()
            self.clock_seconds = (data[1] << 8) | data[2]
            self.clock = Utils.format_clock(self.clock_seconds)
        elif cmd == Bluetooth.CMD_SET_MODE and len(data) >= 2:
            self.mode = data[1]
            Utils.json_update_prop("mode", self.mode)

    """
    Polls for any BT messages. 
    """
    def bt_check(self):
        # Drain the full BLE queue so all pending commands are applied before redrawing.
        if self.bt:
            cmd = self.bt.poll()
            while cmd is not None:
                self.handle_bt_cmd(cmd)
                cmd = self.bt.poll()

            now_connected = self.bt.connected
            if now_connected != self.bt_was_connected:
                self.bt_was_connected = now_connected
                if now_connected:
                    self.clear_bt_id()
                    self.draw_bt_indicator()
                else:
                    self.clear_bt_indicator()
                    self.draw_bt_id()

    """
    Does what it says, updates the scores and the clock
    """
    def update_score_and_clock(self):
        # Show the clock if it's enabled.
        if Config.CLOCK_ENABLED:
            clock_x = (self.width - self.disp.measure_text(self.clock, 1)) // 2
            self.disp.draw_text(self.clock, clock_x, self.forth + Config.TOP_PADDING, Config.TIMER_COLOR)

        # Show the scores if they're enabled.
        if Config.SCORE_ENABLED:
            left_num = str(self.left_score)
            right_num = str(self.right_score)
            right_x = self.width - self.disp.measure_text(right_num, 1) - Config.SIDE_PADDING
            self.disp.draw_text(left_num, Config.SIDE_PADDING, self.forth + Config.TOP_PADDING, Config.SCORE_COLOR)
            self.disp.draw_text(right_num, right_x, self.forth + Config.TOP_PADDING, Config.SCORE_COLOR)

        # Show the period indicator as 2x2 squares in the bottom-left: elapsed/current
        # periods are LIT_PIP_COLOR, upcoming periods are UNLIT_PIP_COLOR.
        for i in range(Config.MAX_PERIODS):
            color = Config.LIT_PIP_COLOR if i < self.current_period else Config.UNLIT_PIP_COLOR
            self.disp.fill_rect(i * 4, self.height - 3, 2, 2, color)

        self.disp.update()

    """
    Beeps: "En guarde. Ready? Fence!" 
    """
    def enguarde_ready_fence(self):
        self.disp.beeper_on()   # en
        time.sleep(0.1)
        self.disp.beeper_off()
        time.sleep(0.05)
        self.disp.beeper_on()   # garde
        time.sleep(0.1)
        self.disp.beeper_off()
        time.sleep(0.35)
        self.disp.beeper_on()   # ready
        time.sleep(0.15)
        self.disp.beeper_off()
        time.sleep(0.3)
        self.disp.beeper_on()   # fence
        time.sleep(0.6)
        self.disp.beeper_off()

    """
    Draws the splash text, using the given max score/periods for the self reffing line.
    """
    def draw_splash_text(self, max_score, max_periods):
        mode_name = "sr" if self.mode == Utils.SelfRef else ("r" if self.mode == Utils.Ref else "s")
        splash = f"{Config.VERSION}\nmode: {mode_name}\n"

        if self.mode == Utils.SelfRef:
            splash += f"ms: {max_score} | mp: {max_periods}"

        self.disp.fill_rect(0, 0, self.width, self.height, Config.BLACK)
        self.disp.draw_text(splash, 0, 0, Config.GROUND_COLOR, font="bitmap6")

    def display_splash_screen(self):
        max_score = Config.SELF_REF_SCORE_MAX
        max_periods = Config.MAX_PERIODS
        preset_index = None

        self.draw_splash_text(max_score, max_periods)
        self.disp.update()

        start = Utils.ticks_ms()
        duration_ms = Config.SPLASH_DURATION * 1000
        bar_h = Config.SPLASH_COUNTDOWN_HEIGHT
        bar_y = self.height - bar_h
        prev_left = False
        prev_right = False
        last_cycle = Utils.ticks_add(start, -Config.SPLASH_CYCLE_DELAY)

        while True:
            now = Utils.ticks_ms()
            elapsed = Utils.ticks_diff(now, start)
            if elapsed >= duration_ms:
                break

            bar_width = self.width * (duration_ms - elapsed) // duration_ms
            self.disp.fill_rect(0, bar_y, self.width, bar_h, Config.BLACK)
            self.disp.fill_rect(0, bar_y, bar_width, bar_h, Config.GROUND_COLOR)
            self.disp.update()

            if self.mode == Utils.SelfRef:
                left_valid, right_valid, _, _ = self.check()
                touched = (left_valid and not prev_left) or (right_valid and not prev_right)
                if touched and Utils.ticks_diff(now, last_cycle) >= Config.SPLASH_CYCLE_DELAY:
                    preset_index = 0 if preset_index is None else (preset_index + 1) % len(Config.SELF_REF_PRESETS)
                    max_score, max_periods = Config.SELF_REF_PRESETS[preset_index]
                    self.draw_splash_text(max_score, max_periods)
                    last_cycle = now
                prev_left, prev_right = left_valid, right_valid

        if self.mode == Utils.SelfRef and preset_index is not None:
            Config.SELF_REF_SCORE_MAX = max_score
            Config.MAX_PERIODS = max_periods

        self.disp.fill_rect(0, 0, self.width, self.height, Config.BLACK)
        self.disp.update()

    def light(self, side):
        if side == "left":
            self.disp.fill_rect(0, 0, self.half, self.forth, Config.LEFT_COLOR)
        else:
            self.disp.fill_rect(self.half, 0, self.half, self.forth, Config.RIGHT_COLOR)

    """
    Main logic of the box. 
    """
    def main_loop(self, self_reffed=False):
        # Check to see if a button was pressed.
        left_valid, right_valid, left_bell, right_bell = self.check()
        double = left_valid and right_valid
        any_valid = left_valid or right_valid

        # Display orange ground indicator when bell is pressed (one frame, then clear).
        if left_bell or right_bell:
            if left_bell:
                self.disp.fill_rect(0, 0, 3, self.forth, Config.GROUND_COLOR)
            if right_bell:
                self.disp.fill_rect(self.width - 3, 0, 3, self.forth, Config.GROUND_COLOR)
            self.disp.update()
            self.clear_lights()

        # If we have a touch, but not a double, start waiting for the other weapon to determine a double.
        if any_valid and not double:
            waiting_for = 'left' if right_valid else 'right'
            start = Utils.ticks_ms()
            while True:
                left, right, _, _ = self.check()
                if (waiting_for == 'left' and left) or (waiting_for == 'right' and right):
                    left_valid = True
                    right_valid = True
                    double = True
                    break

                if Utils.ticks_diff(Utils.ticks_ms(), start) >= Config.DOUBLE_LOCKOUT:
                    break

        if any_valid:
            should_score = True
            if self_reffed and double and self.left_score == Config.SELF_REF_SCORE_MAX - 1 and self.right_score == Config.SELF_REF_SCORE_MAX - 1 and self.current_period == Config.MAX_PERIODS:
                should_score = False

            # Remember the pre-increment scores so the old digit's width is
            # used when clearing below, since clearing with the new digit's
            # width can leave old pixels behind if the two widths differ.
            old_left_score = self.left_score
            old_right_score = self.right_score

            # If we have any valid touches, light up the box.
            if left_valid or double:
                self.light("left")
                if should_score:
                    self.left_score += 1
            if should_score and right_valid or double:
                self.light("right")
                if should_score:
                    self.right_score += 1

            # Stop the clock.
            self.clock_running = False
            # If we have BT enabled, send the clock info to the PWA.
            if self.bt:
                hi = (self.clock_seconds >> 8) & 0xFF
                lo = self.clock_seconds & 0xFF
                self.bt.notify([Bluetooth.EVT_STATE_SYNC, self.left_score, self.right_score, hi, lo])

            # Update the display and score.
            self.disp.update()
            self.disp.beeper_on()
            time.sleep(Config.ILLUM_TIME)
            self.disp.beeper_off()

            self.last_tick = Utils.ticks_ms()
            self.clear_lights()

            if self_reffed:
                # check_for_self_deny() already resolves any deny decision and
                # resyncs the display before it returns (see resolve_self_deny()),
                # since wait_for_ready() may redraw the score mid-pause.
                self.check_for_self_deny(left_valid, right_valid, old_left_score, old_right_score)
            else:
                self.clear_score(old_left_score, 'left')
                self.clear_score(old_right_score, 'right')

        # Update the clock every second.
        if self.clock_running and Utils.ticks_diff(Utils.ticks_ms(), self.last_tick) >= 1000 and self.clock_seconds > 0:
            self.clear_clock()
            self.clock_seconds -= 1
            self.last_tick = Utils.ticks_add(self.last_tick, 1000)
            self.clock = Utils.format_clock(self.clock_seconds)

        self.update_score_and_clock()
        return any_valid

    """
    Draws the pips for self denying touches or starting the bout.
    """
    def draw_pips(self, left_presses, right_presses, pip_y, show_left=True, show_right=True):
        pip_size = 4
        pip_gap = 2
        left_pip_x = (self.half - (pip_size * 2 + pip_gap)) // 2
        right_pip_x = self.half + (self.half - (pip_size * 2 + pip_gap)) // 2
        if show_left:
            for i in range(2):
                color = Config.LIT_PIP_COLOR if i < left_presses else Config.UNLIT_PIP_COLOR
                self.disp.fill_rect(left_pip_x + i * (pip_size + pip_gap), pip_y, pip_size, pip_size, color)
        if show_right:
            for i in range(2):
                color = Config.LIT_PIP_COLOR if i < right_presses else Config.UNLIT_PIP_COLOR
                self.disp.fill_rect(right_pip_x + i * (pip_size + pip_gap), pip_y, pip_size, pip_size, color)

    """
    Checks if a weapon has been pressed, ignores bells. 
    """
    def poll_weapon_presses(self, left_presses, right_presses, prev_left, prev_right):
        left, right, _, _ = self.check()
        if left and not prev_left:
            left_presses = min(left_presses + 1, 2)
        if right and not prev_right:
            right_presses = min(right_presses + 1, 2)
        return left_presses, right_presses, left, right

    """
    Checks if a fencer wants to self deny a touch. If a fencer holds their
    weapon down continuously for SELF_DENY_HOLD_PAUSE_DELAY ms after reaching
    their second (denying) press, pauses the bout and re-enters the waiting
    for ready flow.
    """
    def check_for_self_deny(self, left_valid, right_valid, old_left_score, old_right_score):
        deny_elapsed = 0
        last_tick = Utils.ticks_ms()
        left_presses = 0
        right_presses = 0
        prev_left = False
        prev_right = False
        left_hold_start = None
        right_hold_start = None
        bar_h = Config.SELF_DENY_COUNTDOWN_HEIGHT
        bar_y = self.height - bar_h
        hold_bar_h = Config.SELF_DENY_HOLD_PAUSE_HEIGHT
        deny_ms = Config.SELF_DENY_DELAY
        hold_ms = Config.SELF_DENY_HOLD_PAUSE_DELAY
        pip_y = self.forth - 4 - 2

        while True:
            now = Utils.ticks_ms()
            deny_delta = Utils.ticks_diff(now, last_tick)
            last_tick = now

            self.draw_pips(left_presses, right_presses, pip_y, show_left=left_valid, show_right=right_valid)

            left_presses, right_presses, prev_left, prev_right = self.poll_weapon_presses(left_presses, right_presses, prev_left, prev_right)
            left_hold_start, right_hold_start, hold_elapsed = self.track_hold_pause(left_presses, right_presses, prev_left, prev_right, left_hold_start, right_hold_start, now)

            # Only advance the deny countdown while a fencer isn't building up a hold pause.
            if hold_elapsed == 0:
                deny_elapsed += deny_delta

            if deny_elapsed >= deny_ms:
                self.disp.fill_rect(0, 0, self.width, self.forth, Config.BLACK)
                self.disp.fill_rect(0, bar_y, self.width, bar_h, Config.BLACK)
                self.disp.update()
                return self.resolve_self_deny(left_valid, right_valid, left_presses, right_presses, old_left_score, old_right_score)

            bar_width = self.width * (deny_ms - deny_elapsed) // deny_ms
            self.disp.fill_rect(0, bar_y, self.width, bar_h, Config.BLACK)
            self.disp.fill_rect(0, bar_y, bar_width, bar_h, Config.GROUND_COLOR)

            self.disp.fill_rect(0, 0, self.width, hold_bar_h, Config.BLACK)
            if hold_elapsed > 0:
                hold_bar_width = self.width * min(hold_elapsed, hold_ms) // hold_ms
                self.disp.fill_rect(0, 0, hold_bar_width, hold_bar_h, Config.SELF_DENY_HOLD_PAUSE_COLOR)

            self.disp.update()

            if hold_elapsed >= hold_ms:
                self.disp.fill_rect(0, 0, self.width, self.forth, Config.BLACK)
                self.disp.fill_rect(0, bar_y, self.width, bar_h, Config.BLACK)
                self.disp.update()

                left_deny, right_deny = self.resolve_self_deny(left_valid, right_valid, left_presses, right_presses, old_left_score, old_right_score)

                self.clock_running = False
                self.wait_for_ready()
                return left_deny, right_deny

    """
    Resolves a self-deny decision: reverts the score for any denied side and
    resyncs the display to the final values immediately, before wait_for_ready()
    (or anything else) redraws the score again without clearing first.
    """
    def resolve_self_deny(self, left_valid, right_valid, left_presses, right_presses, old_left_score, old_right_score):
        left_deny = left_valid and left_presses >= 2
        right_deny = right_valid and right_presses >= 2

        # Clear using the pre-increment scores: the screen still shows the old
        # digit at this point (nothing redraws it during the deny/hold wait),
        # so clearing with the already-incremented self.*_score would size the
        # clear rect for the new digit while the old (possibly wider) digit is
        # what's actually on screen, leaving remnants behind.
        self.clear_score(old_left_score, 'left')
        self.clear_score(old_right_score, 'right')
        if left_deny:
            self.left_score -= 1
        if right_deny:
            self.right_score -= 1
        self.update_score_and_clock()

        return left_deny, right_deny

    """
    Tracks how long a fencer has continuously held their weapon down since
    reaching two self deny presses. Returns the updated hold start times and
    the longest continuous hold duration in ms (0 if neither side is holding).
    """
    def track_hold_pause(self, left_presses, right_presses, left_now, right_now, left_hold_start, right_hold_start, now):
        if left_presses >= 2 and left_now:
            if left_hold_start is None:
                left_hold_start = now
        else:
            left_hold_start = None

        if right_presses >= 2 and right_now:
            if right_hold_start is None:
                right_hold_start = now
        else:
            right_hold_start = None

        left_elapsed = Utils.ticks_diff(now, left_hold_start) if left_hold_start is not None else 0
        right_elapsed = Utils.ticks_diff(now, right_hold_start) if right_hold_start is not None else 0

        return left_hold_start, right_hold_start, max(left_elapsed, right_elapsed)

    """
    Main loop for the reffed version of the box. This is the default loop and assumes that a Bluetooth PWA remote is
    connected to the box. It is technically functional without a ref, but I would recommend switching to "DumbBox" mode
    or disabling the clock and score if you don't have a ref. 
    """
    def run_reffed(self):
        if self.bt:
            self.draw_bt_id()

        while True:
            self.bt_check()
            self.main_loop()

    """
    Waits for both fencers to double-press their weapon to signal ready.
    Shows two pips per side that fill in as each press is registered,
    then "ready" text once a fencer reaches two presses.
    """
    def wait_for_ready(self):
        # Drain: wait for any held weapons to release before counting presses,
        # so contacts left over from the deny window don't count as ready presses.
        while True:
            left_valid, right_valid, _, _ = self.check()
            if not left_valid and not right_valid:
                break

        left_presses = 0
        right_presses = 0
        prev_left = False
        prev_right = False

        pip_y = (self.forth - 4) // 2 - 4
        ready_y = pip_y + 4 + 2

        while left_presses < 2 or right_presses < 2:
            self.bt_check()
            left_presses, right_presses, prev_left, prev_right = self.poll_weapon_presses(left_presses, right_presses, prev_left, prev_right)
            self.draw_pips(left_presses, right_presses, pip_y)

            if left_presses >= 2:
                text_width = self.disp.measure_text(Config.SELF_REF_READY, 1, font='bitmap6')
                self.disp.draw_text(Config.SELF_REF_READY, (self.half - text_width) // 2, ready_y, Config.LEFT_COLOR, font='bitmap6')

            if right_presses >= 2:
                text_width = self.disp.measure_text(Config.SELF_REF_READY, 1, font='bitmap6')
                self.disp.draw_text(Config.SELF_REF_READY, self.half + (self.half - text_width) // 2, ready_y, Config.RIGHT_COLOR, font='bitmap6')

            self.update_score_and_clock()

        # Drain again: a weapon still touching from the 2nd ready press must
        # release before we return, or the very next main_loop() call reads
        # that lingering contact as a brand-new touch (phantom score + beep).
        while True:
            left_valid, right_valid, _, _ = self.check()
            if not left_valid and not right_valid:
                break

        # Clear the full touch area once both are ready.
        time.sleep(Config.SELF_DENY_DELAY / 1000)
        self.disp.fill_rect(0, 0, self.width, self.forth, Config.BLACK)
        self.disp.update()

    """
    Displays the end of bout message and resets the bout. 
    """
    def end_bout(self):
        msg = Config.END_OF_BOUT_MSG
        msg_width = self.disp.measure_text(msg, 1, font='bitmap6')
        self.disp.fill_rect(0, 0, self.width, self.forth, Config.BLACK)
        self.disp.draw_text(msg, (self.width - msg_width) // 2, (self.forth - 6) // 2, Config.GROUND_COLOR,
                            font='bitmap6')
        self.disp.update()
        time.sleep(Config.END_OF_BOUT_DELAY_SECONDS)

        self.disp.fill_rect(0, 0, self.width, self.height, Config.BLACK)
        self.disp.update()
        self.left_score = 0
        self.right_score = 0
        self.clock_seconds = Config.CLOCK_SECONDS
        self.clock = Utils.format_clock(self.clock_seconds)
        self.current_period = 1
        self.wait_for_ready()
        self.enguarde_ready_fence()
        self.last_tick = Utils.ticks_ms()
        self.clock_running = True

    """
    Randomly chooses priority. 
    """
    def pick_priority(self):
        sides = ["left", "right"]
        choice = "left"
        for i in range(random.randint(Config.PRIORITY_LOWER_BOUND, Config.PRIORITY_UPPER_BOUND)):
            choice = sides[i % 2]
            self.light(choice)
            self.disp.update()
            time.sleep(0.3)
            self.clear_lights()
            self.disp.update()

        self.light(choice)
        self.disp.update()
        time.sleep(1)
        self.clear_lights()
        self.disp.update()

    """
    Self-reffing main loop.
    """
    def run_self_reffed(self):
        self.current_period = 1
        # Wait for the fencers to be ready. (Display the 2 unpipped pips)
        self.wait_for_ready()

        # Beep en guarde, ready? fence.
        self.enguarde_ready_fence()
        self.last_tick = Utils.ticks_ms()
        self.clock_running = True

        while True:
            self.bt_check()
            any_valid = self.main_loop(self_reffed=True)

            # If there were any valid touches, sound the beep and restart the timer.
            if any_valid:
                if self.left_score == Config.SELF_REF_SCORE_MAX or self.right_score == Config.SELF_REF_SCORE_MAX:
                    self.end_bout()
                    continue

                self.enguarde_ready_fence()
                self.last_tick = Utils.ticks_ms()
                self.clock_running = True

            # If the timer runs out, give a break period, then start the next period
            if self.clock_seconds == 0:
                self.clock_running = False
                self.disp.beeper_on()
                time.sleep(Config.PERIOD_OVER_BUZZER_SECONDS)
                self.disp.beeper_off()

                # If we're at the end of the bout via time, display the end of bout message and restart.
                if self.current_period >= Config.MAX_PERIODS:
                    if self.priority or self.left_score != self.right_score:
                        self.end_bout()
                        continue

                    self.priority = True
                    self.pick_priority()
                    self.clock_seconds = Config.PRIORITY_SECONDS

                if not self.priority:
                    self.clock_seconds = Config.PERIOD_BREAK
                    self.clock_running = True

                    self.last_tick = Utils.ticks_ms()
                    while self.clock_seconds > 0:
                        if Utils.ticks_diff(Utils.ticks_ms(), self.last_tick) >= 1000:
                            self.clear_clock()
                            self.clock_seconds -= 1
                            self.last_tick = Utils.ticks_add(self.last_tick, 1000)
                            self.clock = Utils.format_clock(self.clock_seconds)
                        self.update_score_and_clock()

                    self.clock_running = False
                    self.clock_seconds = Config.CLOCK_SECONDS
                    self.clear_period()
                    self.current_period += 1

                self.wait_for_ready()
                self.last_tick = Utils.ticks_ms()
                self.clock_running = True

                self.enguarde_ready_fence()
                self.clock_running = True

    """
    Runs the selected mode. 
    """
    def run(self):
        # self.pick_priority()
        if Config.SPLASH_ENABLED:
            self.display_splash_screen()

        if self.mode == Utils.Ref:
            self.run_reffed()
        elif self.mode == Utils.SelfRef:
            self.run_self_reffed()
        elif self.mode == Utils.DumbBox:
            # Python lets me do this? Wacky.
            Config.SCORE_ENABLED = False
            Config.CLOCK_ENABLED = False
            Config.BT_ID_ENABLED = False
            self.run_reffed()
        else:
            self.disp.draw_text(random.choice(Config.EASTER_EGG_QUOTES), 0, 0, Config.LEFT_COLOR, font="bitmap6")
            self.disp.update()
