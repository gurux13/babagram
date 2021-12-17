import threading


import time

from i2c import I2C
is_pi = True
try:
    import RPi.GPIO as GPIO
except:
    is_pi = False
    import Mock.GPIO as GPIO
# import RPi.GPIO as GPIO
from enum import Enum, unique
import numpy as np

from recording import Recording


class Hardware:
    @unique
    class Led (Enum):
        Sos = 0
        Dir1 = 1
        Dir2 = 2
        Dir3 = 3
        Dir4 = 4
        Rec = 5

        WiFi = 6
        Ok = 7
        Paper = 8

    @unique
    class LedMode (Enum):
        Off = 1,
        On = 2,
        Blink = 3

    @unique
    class Buttons (Enum):
        Sos = 25
        Dir1 = 24
        Dir2 = 23
        Dir3 = 18
        Dir4 = 15
        Rec = 14

    def __init__(self):
        self.i2c_lock = threading.RLock()
        self.leds = 0
        self.led_blinks = 0
        self.led_mapping = [-1]*6 + [8, 7, 12]
        self.i2c = I2C()
        self.last_interrupt = 0
        self.last_btn = -1
        self._on_btnpress = None
        GPIO.setmode(GPIO.BCM)
        for pin in filter(lambda x: x != -1, self.led_mapping):
            # print(pin)
            GPIO.setup(pin, GPIO.OUT)
        for btn in self.Buttons:
            GPIO.setup(btn.value, GPIO.IN, pull_up_down = GPIO.PUD_UP)
            GPIO.add_event_detect(btn.value, GPIO.FALLING, callback=self._btn_callback, bouncetime=200)
        self.all_leds_off()
        self.recording:Recording = None

    def set_recording(self, recording):
        self.recording = recording

    def cleanup(self):
        GPIO.cleanup()

    def on_btn_press(self, callback):
        self._on_btnpress = callback

    def _btn_callback(self, gpio):
        # if time.time() - self.last_interrupt < 0.5 and gpio == self.last_btn:
        #     return
        # self.last_interrupt = time.time()
        # self.last_btn = gpio
        button = [x for x in self.Buttons if x.value == gpio][0]
        self._on_btnpress(button)
        print("Callback for", gpio, "btn:", button)



    def simple_command(self, cmd: int, payload: bytes) -> bool:
        self.i2c_lock.acquire()
        self.i2c.send(cmd, payload)
        received = self.i2c.recv(1)
        now = time.time()
        while received[0] == 0 and time.time() < now + 1:
            received = self.i2c.recv(1)
        self.i2c_lock.release()
        return  received[0] == 1

    def lock(self):
        self.i2c_lock.acquire()

    def unlock(self):
        self.i2c_lock.release()

    def btn_pressed(self, btn: Buttons):
        return GPIO.input(btn.value) == GPIO.LOW

    def scroll(self, steps: int) -> bool:
        return self.simple_command(4, steps.to_bytes(4, "little", signed=True))

    def line(self, data: bytes) -> bool:
        if len(data) != 16:
            raise Exception("Line data is not 16 - something terribly broke!")
        return self.simple_command(5, data)

    def fire(self, delay: int) -> bool:
        return self.simple_command(2, delay.to_bytes(4, "little"))

    def buzz(self, freq1: int, freq2: int, duration: int, freq_duration: int) -> bool:
        return self.simple_command(6, bytes([freq1, freq2, duration, freq_duration]))

    def get_paper_status(self):
        self.lock()
        try:
            self.i2c.send(8, b'\001')
            received = self.i2c.recv(1)
            return received[0]
        finally:
            self.unlock()


    def _send_leds(self) -> bool:
        return self.simple_command(7, bytes([self.leds, self.led_blinks]))

    def led(self, led: Led, mode: LedMode):
        if self.led_mapping[led.value] == -1:
            shifted = 1 << led.value
            if mode == self.LedMode.Blink:
                self.led_blinks |= shifted
            else:
                self.led_blinks &= ~shifted
            if mode == self.LedMode.On:
                self.leds |= shifted
            else:
                self.leds &= ~shifted
            return self._send_leds()
        else:
            GPIO.output(self.led_mapping[led.value], GPIO.HIGH if mode == self.LedMode.On else GPIO.LOW)
            return True

    def all_leds_off(self):
        self.leds = self.led_blinks = 0
        for pin in filter(lambda x: x != -1, self.led_mapping):
            GPIO.output(pin, GPIO.LOW)
        return self._send_leds()
    def all_volatile_leds_off(self):
        self.leds = self.led_blinks = 0
        return self._send_leds()

# i2c = Hardware()
# print(i2c.scroll(4))
# last_choice = None
# print(i2c.buzz(128, 140, 4, 1))
# # exit(0)
# while True:
#     time.sleep(1)
#
# while True:
#     values = list(Hardware.Led)
#     chosen = np.random.choice(values, 1)[0]
#     while chosen == last_choice:
#         chosen = np.random.choice(values, 1)[0]
#     last_choice = chosen
#     i2c.all_leds_off()
#     time.sleep(1)
    # break
    # i2c.led(I2C.Led.Sos, I2C.LedMode.Blink)
#
#
