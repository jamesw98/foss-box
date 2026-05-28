import sys
import Config

"""
Here be dragons. 
I am ashamed to admit it, but this code is 90% Claude. 
"""

DEVICE_NAME = "FossBox"

CMD_TIMER_START  = 0x01
CMD_TIMER_STOP   = 0x02
CMD_LEFT_INC     = 0x03
CMD_LEFT_DEC     = 0x04
CMD_RIGHT_INC    = 0x05
CMD_RIGHT_DEC    = 0x06
CMD_SET_TIME     = 0x07
CMD_SET_MODE     = 0x08
EVT_STATE_SYNC   = 0x10

if sys.implementation.name == 'circuitpython':
    from adafruit_ble import BLERadio
    from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
    from adafruit_ble.services.nordic import UARTService

    class BLEReceiver:
        def __init__(self):
            self._ble = BLERadio()
            self._ble.name = f"{DEVICE_NAME}_{Config.BLUETOOTH_ID}"
            self._uart = UARTService()
            self._advertisement = ProvideServicesAdvertisement(self._uart)
            self._pending = []
            self._was_connected = False
            self._ble.start_advertising(self._advertisement)
            if Config.BLUETOOTH_DEBUG:
                print("BLE: advertising as", self._ble.name)

        def poll(self):
            now_connected = self._ble.connected
            if not self._was_connected and now_connected:
                try:
                    self._ble.connections[0].connection_interval = 15
                    if Config.BLUETOOTH_DEBUG:
                        print("BLE: set interval to 15ms")
                except Exception as e:
                    if Config.BLUETOOTH_DEBUG:
                        print("BLE: interval set failed:", e)
            if self._was_connected and not now_connected:
                self._ble.start_advertising(self._advertisement)
                if Config.BLUETOOTH_DEBUG:
                    print("BLE: disconnected, restarting adv")
            self._was_connected = now_connected

            if now_connected:
                n = self._uart.in_waiting
                data = self._uart.read(n) if n else None
                if data:
                    if Config.BLUETOOTH_DEBUG:
                        print("BLE: received", list(data))
                    # Parse the byte stream into individual commands.
                    # CMD_SET_TIME is 3 bytes, CMD_SET_MODE is 2 bytes, all others are 1.
                    i = 0
                    while i < len(data):
                        cmd = data[i]
                        if cmd == CMD_SET_TIME and i + 3 <= len(data):
                            self._pending.append(bytes(data[i:i + 3]))
                            i += 3
                        elif cmd == CMD_SET_MODE and i + 2 <= len(data):
                            self._pending.append(bytes(data[i:i + 2]))
                            i += 2
                        else:
                            self._pending.append(bytes([cmd]))
                            i += 1

            if self._pending:
                return self._pending.pop(0)
            return None

        def notify(self, data):
            try:
                self._uart.write(bytes(data))
                if Config.BLUETOOTH_DEBUG:
                    print("BLE: notified", list(data))
            except Exception as e:
                if Config.BLUETOOTH_DEBUG:
                    print("BLE: notify failed:", e)

        @property
        def connected(self):
            return self._ble.connected

else:
    import ubluetooth as bluetooth
    import struct
    import time

    _NUS_BASE    = "B5A3-F393-E0A9-E50E24DCCA9E"
    SERVICE_UUID = bluetooth.UUID(f"6E400001-{_NUS_BASE}")
    RX_UUID      = bluetooth.UUID(f"6E400002-{_NUS_BASE}")
    TX_UUID      = bluetooth.UUID(f"6E400003-{_NUS_BASE}")
    RX_CHAR = (RX_UUID, bluetooth.FLAG_WRITE | bluetooth.FLAG_WRITE_NO_RESPONSE)
    TX_CHAR = (TX_UUID, bluetooth.FLAG_NOTIFY)
    SERVICE = (SERVICE_UUID, (RX_CHAR, TX_CHAR))

    def _build_adv_payload(name):
        payload = bytearray()

        def append(adv_type, value):
            payload.extend(struct.pack("BB", len(value) + 1, adv_type))
            payload.extend(value)

        append(0x01, struct.pack("B", 0x06))
        append(0x09, name.encode())
        return bytes(payload)

    class BLEReceiver:
        def __init__(self):
            self._connected = False
            self._conn_handle = None
            self._pending = []
            self._rx_handle = None
            self._tx_handle = None

            self.ble = bluetooth.BLE()
            self.ble.active(True)
            time.sleep_ms(200)  # give CYW43 BLE stack time to fully start

            self.ble.irq(self.irq)

            handles = self.ble.gatts_register_services((SERVICE,))
            self._rx_handle = handles[0][0]
            self._tx_handle = handles[0][1]
            if Config.BLUETOOTH_DEBUG:
                print("BLE: registered, rx_handle =", self._rx_handle, "tx_handle =", self._tx_handle)

            name = f"{DEVICE_NAME}_{Config.BLUETOOTH_ID}"
            self._adv_payload = _build_adv_payload(name)
            if Config.BLUETOOTH_DEBUG:
                print("BLE: adv payload len =", len(self._adv_payload), "name =", name)

            self._advertise()

        def irq(self, event, data):
            if event == 1:  # IRQ_CENTRAL_CONNECT
                self._conn_handle, _, _ = data
                self._connected = True
                if Config.BLUETOOTH_DEBUG:
                    print("BLE: connected, handle =", self._conn_handle)
            elif event == 2:  # IRQ_CENTRAL_DISCONNECT
                self._conn_handle = None
                self._connected = False
                if Config.BLUETOOTH_DEBUG:
                    print("BLE: disconnected, restarting adv")
                self._advertise()
            elif event == 3:  # IRQ_GATTS_WRITE
                conn_handle, attr_handle = data
                if attr_handle == self._rx_handle:
                    value = self.ble.gatts_read(self._rx_handle)
                    if value:
                        self._pending.append(bytes(value))

        def _advertise(self, interval_us=100_000):
            self.ble.gap_advertise(interval_us, adv_data=self._adv_payload)
            if Config.BLUETOOTH_DEBUG:
                print("BLE: advertising")

        def notify(self, data):
            if not self._connected or self._conn_handle is None:
                return
            try:
                self.ble.gatts_notify(self._conn_handle, self._tx_handle, bytes(data))
            except Exception as e:
                if Config.BLUETOOTH_DEBUG:
                    print("BLE: notify failed:", e)

        def poll(self):
            if self._pending:
                return self._pending.pop(0)
            return None

        @property
        def connected(self):
            return self._connected
