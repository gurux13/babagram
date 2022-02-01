import fake_gpio
from hardware import Hardware
from threaded import Threaded
import sys
import Mock.GPIO as GPIO
class FakeHardware (Threaded):
    def __init__(self, hw: Hardware):
        Threaded.__init__(self)
        self.hw = hw
    def _thread_fn(self):
        for line in sys.stdin:
            if line[0].lower() == 'r':
                print ("Faking record button")
                if line[1] == '1':
                    self.hw._btn_callback(Hardware.Buttons.Rec.value)
                fake_gpio.override_value(Hardware.Buttons.Rec.value, GPIO.LOW if line[1] == '1' else GPIO.HIGH)


            if line[0].lower() == 's':
                print("Faking select first element")
                self.hw._btn_callback(Hardware.Buttons.Dir1.value)
