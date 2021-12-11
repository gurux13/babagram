import threading
import time

from hardware import Hardware
from threaded import Threaded

global_paper_status = None

class PaperStatus (Threaded):
    def __init__(self, hardware: Hardware):
        Threaded.__init__(self)
        global global_paper_status
        if global_paper_status is not None:
            raise Exception("There can only be one!")
        self.hw = hardware
        self.is_ok = False
        global_paper_status = self

    @classmethod
    def instance(cls):
        return global_paper_status

    def _thread_fn(self):
        while not self._stop:
            status = self.hw.get_paper_status()
            if status is not None and status & 3 == 3:
                self.hw.led(Hardware.Led.Paper, Hardware.LedMode.Off)
                self.is_ok = True
            else:
                self.hw.led(Hardware.Led.Paper, Hardware.LedMode.On)
                self.is_ok = False
            time.sleep(0.1)
