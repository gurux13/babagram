import time
from threading import Thread

from hardware import Hardware
from image import print_message
from printer import Printer
from recording import Recording
from tg import Telegram


class ButtonLogic:
    def __init__(self, hardware: Hardware, tg: Telegram, rec: Recording):
        self.hw = hardware
        self.tg = tg
        self.rec = rec
        self.is_recording = False
        self.destination = None

    def record(self):
        try:
            if self.destination is None:
                for i in range(4):
                    self.hw.led(Hardware.Led(Hardware.Led.Dir1.value + i), Hardware.LedMode.Blink)
                while self.hw.btn_pressed(Hardware.Buttons.Rec):
                    time.sleep(0.001)
                self.hw.all_volatile_leds_off()
                return

            self.hw.led(Hardware.Led.Rec, Hardware.LedMode.On)
            self.hw.led(Hardware.Led(Hardware.Led.Dir1.value + self.destination), Hardware.LedMode.Blink)
            audio = self.rec.record()
            self.hw.led(Hardware.Led.Rec, Hardware.LedMode.Blink)
            self.hw.led(Hardware.Led(Hardware.Led.Dir1.value + self.destination), Hardware.LedMode.Off)
            try:
                self.tg.send_audio(audio, self.destination)
            except:
                Printer(self.hw).print_img(print_message("Ошибка", "Не удалось отправить сообщение!"), 6000, 1)
            finally:
                self.hw.led(Hardware.Led.Rec, Hardware.LedMode.Off)
                self.hw.led(Hardware.Led(Hardware.Led.Dir1.value + self.destination), Hardware.LedMode.On)

        finally:
            self.is_recording = False

    def on_sos(self):
        self.hw.led(Hardware.Led.Sos, Hardware.LedMode.Blink)

    def update_destination(self):
        self.hw.all_volatile_leds_off()
        self.hw.led(Hardware.Led(Hardware.Led.Dir1.value + self.destination), Hardware.LedMode.On)

    def on_btn_click(self, btn: Hardware.Buttons):
        if self.is_recording:
            return
        if btn == Hardware.Buttons.Rec:
            self.is_recording = True
            Thread(target=self.record, daemon=True).start()
            return
        if btn == Hardware.Buttons.Sos:
            self.on_sos()
            return
        if btn == Hardware.Buttons.Dir1:
            self.destination = 0
        if btn == Hardware.Buttons.Dir2:
            self.destination = 1
        if btn == Hardware.Buttons.Dir3:
            self.destination = 2
        if btn == Hardware.Buttons.Dir4:
            self.destination = 3
        self.update_destination()



