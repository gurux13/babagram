import time

import smbus

class I2C:
    def __init__(self):
        try:
            self.bus = smbus.SMBus(1)
        except:
            print("SMBus is not available - assuming a non-Pi device")
            self.bus = None
        self.address = 42
    def send_byte(self, byte: int) -> None:
        if self.bus is None:
            return
        for _ in range(10):
            try:
                self.bus.write_byte(self.address, byte)
                time.sleep(0.001)
                break
            except OSError:
                pass

    def send(self, cmd: int,  payload: bytes) -> None:

        self.send_byte(42) # magic
        self.send_byte(cmd)
        self.send_byte(len(payload))
        for byte in payload:
            self.send_byte(byte)

    def recv(self, count: int) -> bytearray:
        if self.bus is None:
            return bytearray([1] * count)
        rv = bytearray(count)
        for i in range(count):
            rv[i] = self.bus.read_byte(self.address)
            time.sleep(0.01)

        return rv