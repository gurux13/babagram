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
        img = (img - img.min())/ (img.max() - img.min())
    img = (img > 0.5) * 1
    return img

def print_message(sender: str, text: str) -> np.array:
    img = PILImage.new('L', (128, 1000), color=255)
    d = ImageDraw.Draw(img)
    # sender_font = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSans.ttf", 28)
    sender_font = ImageFont.load('fonts/10x20-KOI8-R.pil')
    # text_font = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSans.ttf", 18)
    text_font = ImageFont.load('fonts/8x13-KOI8-R.pil')
    sender = (sender + ":").encode('koi8-r')
    text = text.encode('koi8-r')
    # text_font = ImageFont.truetype("SourceSansPro-Regular.ttf", 25)
    d.text((0, 0), sender, fill=0, font=sender_font)
    sender_shape = d.textsize(sender, font = sender_font)
    cur_height = sender_shape[1] + 5
    curpos = 0
    while curpos < len(text):
        cur_height += (1 - cur_height & 1)
        line = ''
        prev_height = 0
        line = None
        for i in range(1, len(text) - curpos + 1):
            line = text[curpos : curpos + i]
            sz = d.textsize(line, font=text_font)
            if sz[0] > 128 - 5:
                line = line[:-1]
                curpos += len(line)
                d.text((5, cur_height), line, font=text_font, fill=0)
                cur_height += prev_height + 2
                line = None
                break
            else:
                prev_height = sz[1]
        if line is not None:
            curpos += len(line)
            d.text((5, cur_height), line, font=text_font, fill=0)
            cur_height += d.textsize(line, font=text_font)[1] + 2
            line = None
    cur_height += 3
    d.line((0, cur_height, 128, cur_height), fill = 0, width=2)
    img = img.crop((0, 0, 128, cur_height+2))
    if not is_pi:
        img.save('/tmp/image-to-print.png')
    # img = img.resize((128, math.floor(img.size[1] * 1.3)), resample=PILImage.HAMMING)
    return bw(np.array(img.getdata()).reshape(-1, 128))

# image = Image("engrave.png")
# print(image.get_pixels())

