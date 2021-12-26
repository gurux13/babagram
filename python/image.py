import datetime
import math

from PIL import Image as PILImage, ImageDraw, ImageFont
import imageio
import numpy as np

from hardware import is_pi


class Image:
    def __init__(self, path: str):
        self.img = imageio.imread(path)
        if len(self.img.shape) == 3:
            self.img = np.average(self.img, 2)
            self.img = (self.img > 0.5) * 1

    def get_pixels(self):
        return self.img


def bw(img: np.ndarray) -> np.ndarray:
    if len(img.shape) == 3:
        img = np.average(img, 2)
    if (img.max() == img.min()):
        img = img * 0 + 1
    else:
        img = (img - img.min()) / (img.max() - img.min())
    img = (img > 0.5) * 1
    return img


def print_message(sender: str, text: str, when: datetime.datetime) -> np.array:
    img = PILImage.new('L', (128, 2000), color=255)
    d = ImageDraw.Draw(img)
    text_font = ImageFont.load('fonts/new/t0-17b-m51.pil')
    date_font = ImageFont.load('fonts/new/t0-15b-m51.pil')
    date = when.astimezone().strftime("Дата: %d.%m.%Y\nВремя: %H:%M:%S")

    sender_font = ImageFont.load('fonts/new/t0-22-m51.pil')
    sender = '- ' + sender + ' -'
    sender = sender.encode('cp1251')
    text = text.encode('cp1251')
    date = date.encode('cp1251')
    d.multiline_text((0, 0), date, fill=0, font=date_font)
    date_shape = d.multiline_textsize(date, font=date_font)
    cur_height = date_shape[1] + 5

    sender_shape = d.textsize(sender, font=sender_font)
    sender_left = max(0, (128 - sender_shape[0]) / 2)
    d.text((sender_left, cur_height), sender, fill=0, font=sender_font)

    cur_height += sender_shape[1] + 5
    curpos = 0
    text_left = 0
    while curpos < len(text):
        cur_height += (1 - cur_height & 1)
        line = ''
        prev_height = 0
        line = None
        for i in range(1, len(text) - curpos + 1):
            line = text[curpos: curpos + i]
            sz = d.textsize(line, font=text_font)
            if sz[0] > 128 - text_left:
                line = line[:-1]
                curpos += len(line)
                d.text((text_left, cur_height), line, font=text_font, fill=0)
                cur_height += prev_height + 2
                line = None
                break
            else:
                prev_height = sz[1]
        if line is not None:
            curpos += len(line)
            d.text((text_left, cur_height), line, font=text_font, fill=0)
            cur_height += d.textsize(line, font=text_font)[1] + 2
            line = None
    cur_height += 3
    d.line((0, cur_height, 128, cur_height), fill=0, width=2)
    img = img.crop((0, 0, 128, cur_height + 2))
    if not is_pi or True:
        img.save('/tmp/image-to-print.png')
    # img = img.resize((128, math.floor(img.size[1] * 1.3)), resample=PILImage.HAMMING)
    return bw(np.array(img.getdata()).reshape(-1, 128))

# image = Image("engrave.png")
# print(image.get_pixels())
