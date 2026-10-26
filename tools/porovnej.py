"""Snimek z PC vedle reference Misy (pravidlo radce 18:25): vlevo hra, vpravo reference, kazda 960x600 (orez na stred
podle pomeru), nahore popisky. Vystup PNG/JPG do docs/screens/.
  python3 tools/porovnej.py hra.png reference.jpg docs/screens/rozprac_<krok>.jpg ["popis hry" "popis reference"]"""
import sys

from PIL import Image, ImageDraw

W, H = 960, 600


def panel(cesta):
    im = Image.open(cesta).convert("RGB")
    r = W / H
    w, h = im.size
    if w / h > r:
        nw = int(h * r)
        im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = int(w / r)
        im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    return im.resize((W, H), Image.LANCZOS)


def main():
    hra, ref, ven = sys.argv[1:4]
    popisy = sys.argv[4:6] if len(sys.argv) >= 6 else ["hra (PC)", "reference KCD2"]
    out = Image.new("RGB", (W * 2, H))
    out.paste(panel(hra), (0, 0))
    out.paste(panel(ref), (W, 0))
    d = ImageDraw.Draw(out)
    for i, t in enumerate(popisy):
        d.rectangle((i * W + 8, 8, i * W + 16 + 9 * len(t), 30), fill=(0, 0, 0))
        d.text((i * W + 12, 12), t, fill=(255, 255, 255))
    out.save(ven, quality=88)
    print("porovnani:", ven)


if __name__ == "__main__":
    main()
