import ubluetooth as bluetooth
import struct
import time
import Config

IRQ_CENTRAL_CONNECT = 1
IRQ_CENTRAL_DISCONNECT = 2
IRQ_GATTS_WRITE = 3

SERVICE_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
RX_UUID      = bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")
RX_CHAR      = (RX_UUID, bluetooth.FLAG_WRITE | bluetooth.FLAG_WRITE_NO_RESPONSE)
SERVICE      = (SERVICE_UUID, (RX_CHAR,))

DEVICE_NAME = "FossBox"

CMD_TIMER_START = 0x01
CMD_TIMER_STOP  = 0x02
CMD_LEFT_INC    = 0x03
CMD_LEFT_DEC    = 0x04
CMD_RIGHT_INC   = 0x05
CMD_RIGHT_DEC   = 0x06

def build_adv_payload(name):
    payload = bytearray()

    def append(adv_type, value):
        payload.extend(struct.pack("BB", len(value) + 1, adv_type))
        payload.extend(value)

    append(0x01, struct.pack("B", 0x06))  # flags: LE General Discoverable, BR/EDR not supported
    append(0x09, name.encode())            # complete local name

    return bytes(payload)

class BLEReceiver:
    def __init__(self):
        self._connected = False
        self._pending = []
        self._rx_handle = None

        self.ble = bluetooth.BLE()
        self.ble.active(True)
        time.sleep_ms(200)  # give CYW43 BLE stack time to fully start

        self.ble.irq(self.irq)

        handles = self.ble.gatts_register_services((SERVICE,))
        self._rx_handle = handles[0][0]
        print("BLE: registered, rx_handle =", self._rx_handle)

        name = f"{DEVICE_NAME}_{Config.BLUETOOTH_ID}"
        self._adv_payload = build_adv_payload(name)
        print("BLE: adv payload len =", len(self._adv_payload), "name =", name)

        self._advertise()

    def irq(self, event, data):
        if event == IRQ_CENTRAL_CONNECT:
            self._connected = True
            print("BLE: connected")
        elif event == IRQ_CENTRAL_DISCONNECT:
            self._connected = False
            print("BLE: disconnected, restarting adv")
            self._advertise()
        elif event == IRQ_GATTS_WRITE:
            conn_handle, attr_handle = data
            if attr_handle == self._rx_handle:
                value = self.ble.gatts_read(self._rx_handle)
                if value:
                    self._pending.append(value[0])

    def _advertise(self, interval_us=100_000):
        self.ble.gap_advertise(interval_us, adv_data=self._adv_payload)
        print("BLE: advertising")

    def poll(self):
        if self._pending:
            return self._pending.pop(0)
        return None

    @property
    def connected(self):
        return self._connected
