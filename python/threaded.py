import time

import requests
import threading

from hardware import Hardware


class Threaded:
    def __init__(self):
        self._stop = False
        self._thread: threading.Thread = None

    def _thread_fn(self):
        pass

    def stop(self):
        self._stop = True
        if self._thread is not None:
            self._thread.join()

    def start(self):
        self._thread = threading.Thread(target=self._thread_fn, daemon=True)
        self._thread.start()