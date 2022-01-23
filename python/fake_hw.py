from hardware import Hardware
from threaded import Threaded
import sys

class FakeHardware (Threaded):
    def __init__(self, hw: Hardware):
        Threaded.__init__(self)
        self.hw = hw
    def _thread_fn(self):
        for line in sys.stdin:
            if line[0].lower() == 'r':
                print ("Faking record button")
                self.hw._btn_callback(Hardware.Buttons.Rec.value)
            if line[0].lower() == 's':
                print("Faking select first element")
                self.hw._btn_callback(Hardware.Buttons.Dir1.value)
