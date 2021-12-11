from hardware import Hardware
from image import Image, print_message
import time
import numpy as np
class Printer:
    def __init__(self, hardware: Hardware):
        self.hw = hardware

    def print_img(self, img: np.ndarray, delay: int, line_times = 2):
        pixels = img
        self.hw.lock()
        try:
            for i in range(pixels.shape[0]):
                line = pixels[i]
                for _ in range(line_times):
                    self.hw.line(bytes(np.packbits(1 - line[::-1])))
                    self.hw.fire(delay)
                    self.hw.scroll(3)
                    time.sleep(0.02)
            self.hw.scroll(100)
        finally:
            self.hw.unlock()

# Printer(Hardware()).print_img(print_message(u'Андрей', 'Сообщение'), 6000, 1)