import ubluetooth as bluetooth
import struct

_IRQ_CENTRAL_CONNECT = 1
_IRQ_CENTRAL_DISCONNECT = 2

_SERVICE_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_SERVICE = (_SERVICE_UUID, ())

DEVICE_NAME = "FossBox"


def _build_adv_payload(name, service_uuid):
    payload = bytearray()

    def _append(adv_type, value):
        payload.extend(struct.pack("BB", len(value) + 1, adv_type))
        payload.extend(value)

    _append(0x01, struct.pack("B", 0x06))
    _append(0x09, name.encode())
    _append(0x07, bytes(service_uuid))

    return bytes(payload)


class BLEReceiver:
    def __init__(self):
        self._ble = bluetooth.BLE()
        self._ble.active(True)
        self._ble.irq(self._irq)
        self._ble.gatts_register_services((_SERVICE,))
        self._connected = False
        self._adv_payload = _build_adv_payload(DEVICE_NAME, _SERVICE_UUID)
        self._advertise()

    def _irq(self, event, data):
        if event == _IRQ_CENTRAL_CONNECT:
            self._connected = True
            self._ble.gap_advertise(None)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            self._connected = False
            self._advertise()

    def _advertise(self, interval_us=100_000):
        self._ble.gap_advertise(interval_us, adv_data=self._adv_payload)

    @property
    def connected(self):
        return self._connected
