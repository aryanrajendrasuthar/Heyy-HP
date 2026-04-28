"""Generate hp.ico — Iron Man arc-reactor themed HP logo."""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def create_frame(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = cy = size / 2
    pad = max(2, size // 48)

    # ── Background circle (very dark red) ────────────────────────────────
    d.ellipse([pad, pad, size - pad, size - pad], fill="#120000")

    # ── Outer gold ring ───────────────────────────────────────────────────
    bw = max(3, size // 20)
    d.ellipse([pad, pad, size - pad, size - pad], outline="#FFD700", width=bw)

    # ── Second gold ring ──────────────────────────────────────────────────
    if size >= 48:
        m2 = size // 7
        d.ellipse([m2, m2, size - m2, size - m2], outline="#B8860B", width=max(1, bw // 3))

    # ── Arc-reactor spokes (8 lines) ──────────────────────────────────────
    if size >= 64:
        r_out = cx - size // 5
        r_in  = cx - size // 4
        for deg in range(0, 360, 45):
            rad = math.radians(deg)
            x1 = cx + r_in  * math.cos(rad)
            y1 = cy + r_in  * math.sin(rad)
            x2 = cx + r_out * math.cos(rad)
            y2 = cy + r_out * math.sin(rad)
            d.line([(x1, y1), (x2, y2)], fill="#FFD700", width=max(1, size // 80))

    # ── "HP" text ─────────────────────────────────────────────────────────
    fs = max(6, int(size * 0.38))
    font = _font(fs)
    # shadow
    shadow_off = max(1, size // 96)
    d.text((cx + shadow_off, cy + shadow_off), "HP", fill="#4A0000", font=font, anchor="mm")
    # main text
    d.text((cx, cy), "HP", fill="#FFD700", font=font, anchor="mm")

    return img


if __name__ == "__main__":
    sizes = [16, 24, 32, 48, 64, 128, 256]
    frames = [create_frame(s) for s in sizes]
    out = Path(__file__).parent / "hp.ico"
    frames[0].save(
        str(out),
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=frames[1:],
    )
    print(f"Saved {out}")
