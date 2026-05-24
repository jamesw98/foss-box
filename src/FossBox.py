import Utils
import time
import Config

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

        self.bt = None
        self.bt_was_connected = False
        if Config.BLUETOOTH_ENABLED:
            try:
                self.bt = Bluetooth.BLEReceiver()
            except Exception as e:
                print("BLE init failed:", e)

    def check(self):
        return self.weapon_left() and not self.bell_right(), self.weapon_right() and not self.bell_left(), self.bell_left(), self.bell_right()

    def clear_lights(self):
        self.disp.fill_rect(0, 0, self.width, self.forth, Config.BLACK)
        self.disp.update()

    def clear_clock(self):
        text_width = self.disp.measure_text(self.clock, 1)
        starting_x = (self.width - text_width) // 2
        self.disp.fill_rect(starting_x, self.forth, text_width, self.eighth, Config.BLACK)
        self.disp.update()

    def clear_score(self, score, side):
        if score < 0:
            return
        text_width = self.disp.measure_text(str(score), 1)
        starting_x = Config.SIDE_PADDING if side == 'left' else self.width - text_width - Config.SIDE_PADDING
        self.disp.fill_rect(starting_x, self.forth + Config.TOP_PADDING, text_width, self.eighth, Config.BLACK)
        self.disp.update()

    def draw_bt_indicator(self):
        self.disp.fill_rect(self.width - 4, self.height - 4, 4, 4, Config.BT_CONNECTED_COLOR)
        self.disp.update()

    def clear_bt_indicator(self):
        self.disp.fill_rect(self.width - 4, self.height - 4, 4, 4, Config.BLACK)
        self.disp.update()

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
        elif cmd == Bluetooth.CMD_LEFT_DEC:
            if self.left_score > 0:
                self.clear_score(self.left_score, 'left')
                self.left_score -= 1
        elif cmd == Bluetooth.CMD_RIGHT_INC:
            self.clear_score(self.right_score, 'right')
            self.right_score += 1
        elif cmd == Bluetooth.CMD_RIGHT_DEC:
            if self.right_score > 0:
                self.clear_score(self.right_score, 'right')
                self.right_score -= 1
        elif cmd == Bluetooth.CMD_SET_TIME and len(data) >= 3:
            self.clock_running = False
            self.clear_clock()
            self.clock_seconds = (data[1] << 8) | data[2]
            self.clock = Utils.format_clock(self.clock_seconds)

    def run(self):
        while True:
            # If Bluetooth is enabled, check if a command was sent.
            if self.bt:
                cmd = self.bt.poll()
                if cmd is not None:
                    self.handle_bt_cmd(cmd)

                now_connected = self.bt.connected
                if now_connected != self.bt_was_connected:
                    self.bt_was_connected = now_connected
                    if now_connected:
                        self.draw_bt_indicator()
                    else:
                        self.clear_bt_indicator()

            # Check to see if a button was pressed.
            left_valid, right_valid, left_bell, right_bell = self.check()
            double = left_valid and right_valid
            any_valid = left_valid or right_valid

            # Display orange ground indicator when bell is pressed.
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
                        double = True
                        break

                    if Utils.ticks_diff(Utils.ticks_ms(), start) >= Config.DOUBLE_LOCKOUT:
                        break

            if any_valid:
                # If we have any valid touches, light up the box.
                if left_valid or double:
                    self.disp.fill_rect(0, 0, self.half, self.forth, Config.LEFT_COLOR)
                    self.left_score += 1
                if right_valid or double:
                    self.disp.fill_rect(self.half, 0, self.half, self.forth, Config.RIGHT_COLOR)
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
                time.sleep(Config.ILLUM_TIME)
                self.last_tick = Utils.ticks_ms()
                self.clear_lights()
                self.clear_score(self.left_score - 1, 'left')
                self.clear_score(self.right_score - 1, 'right')

            # Update the clock every second.
            if self.clock_running and Utils.ticks_diff(Utils.ticks_ms(), self.last_tick) >= 1000 and self.clock_seconds > 0:
                self.clear_clock()
                self.clock_seconds -= 1
                self.last_tick = Utils.ticks_add(self.last_tick, 1000)
                self.clock = Utils.format_clock(self.clock_seconds)

            # Show the clock if it's enabled.
            if Config.CLOCK_ENABLED:
                clock_x = (self.width - self.disp.measure_text(self.clock, 1)) // 2
                self.disp.draw_text(self.clock, clock_x, self.forth, Config.TIMER_COLOR)

            # Show the scores if they're enabled.
            if Config.SCORE_ENABLED:
                left_num = str(self.left_score)
                right_num = str(self.right_score)
                right_x = self.width - self.disp.measure_text(right_num, 1) - Config.SIDE_PADDING
                self.disp.draw_text(left_num, Config.SIDE_PADDING, self.forth + Config.TOP_PADDING, Config.SCORE_COLOR)
                self.disp.draw_text(right_num, right_x, self.forth + Config.TOP_PADDING, Config.SCORE_COLOR)

            self.disp.update()
