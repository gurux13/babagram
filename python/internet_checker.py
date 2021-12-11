import time

import requests
import threading

from hardware import Hardware
from threaded import Threaded


class InternetChecker (Threaded):
    def __init__(self, hardware: Hardware):
        Threaded.__init__(self)
        self.hw = hardware

    def connected_to_internet(self, url='http://www.google.com/', timeout=5):
        try:
            _ = requests.head(url, timeout=timeout)
            return True
        except requests.ConnectionError:
            print("No internet connection available.")
        return False

    def _thread_fn(self):
        while not self._stop:
            self.hw.led(Hardware.Led.WiFi,
                         Hardware.LedMode.On if self.connected_to_internet() else Hardware.LedMode.Off)
            time.sleep(1)

