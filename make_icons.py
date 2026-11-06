# make_icons.py - app ke icons banata hai (static folder me)
import os
from PIL import Image, ImageDraw

os.makedirs("static", exist_ok=True)


def make_icon(size):
    S = size * 4
    img = Image.new("RGB", (S, S), "#16213E")
    d = ImageDraw.Draw(img)
    u = S / 100.0
    d.rounded_rectangle([29*u, 20*u, 71*u, 80*u], radius=5*u, fill="white")
    d.polygon([(58*u, 20*u), (71*u, 33*u), (58*u, 33*u)], fill="#C8CEDB")
    for y, x2 in ((42, 62), (50, 62), (58, 52)):
        d.rounded_rectangle([36*u, y*u, x2*u, (y+3.2)*u], radius=1.6*u, fill="#C8CEDB")
    cx, cy, r = 66*u, 70*u, 13*u
    d.ellipse([cx-r, cy-r, cx+r, cy+r], fill="#0EA87A", outline="#16213E", width=int(2.2*u))
    d.line([(60.5*u, 70.5*u), (64.5*u, 74.5*u), (72*u, 65*u)], fill="white", width=int(3.4*u), joint="curve")
    return img.resize((size, size), Image.LANCZOS)


for n in (192, 512):
    make_icon(n).save(f"static/icon-{n}.png")
    print("bana: static/icon-%d.png" % n)