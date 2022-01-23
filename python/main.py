from button_logic import ButtonLogic
from fake_hw import FakeHardware
from hardware import Hardware, is_pi
from internet_checker import InternetChecker
from paper_status import PaperStatus
from recording import Recording
from tg import Telegram
import os


def main():
    print("CWD:", os)
    hardware = Hardware()
    recording = Recording(hardware)
    hardware.set_recording(recording)
    internet_checker = InternetChecker(hardware)
    paper_status = PaperStatus(hardware)
    tg = Telegram(hardware)
    buttons = ButtonLogic(hardware, tg, recording)
    tg.set_sos_cancel_callback(buttons.on_tg_stopsos)
    tg.set_dbgprint_callback(buttons.on_tg_dbgprint)
    hardware.on_btn_press(buttons.on_btn_click)
    fake = None
    if not is_pi:
        print("Starting fake hardware")
        fake = FakeHardware(hardware)
        fake.start()
    try:
        internet_checker.start()
        paper_status.start()
        tg.main()
    finally:
        try:
            if fake is not None:
                fake.stop()
            internet_checker.stop()
            paper_status.stop()
        finally:
            hardware.cleanup()

if __name__ == '__main__':
    main()