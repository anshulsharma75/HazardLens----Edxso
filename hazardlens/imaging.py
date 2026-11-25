"""Image preprocessing and hazard-zone annotation."""
import io

from PIL import Image, ImageDraw, ImageFont, ImageOps

from .config import ZONES
from .risk import BAND_COLOR


def prepare_image(fileobj, max_side: int = 1280) -> bytes:
    """Fix EXIF rotation, convert to RGB, downscale and re-encode as JPEG."""
    img = ImageOps.exif_transpose(Image.open(fileobj)).convert("RGB")
    img.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return buf.getvalue()


def _font(size: int):
    for name in ("DejaVuSans-Bold.ttf", "Arial Bold.ttf", "arialbd.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _hex(color: str, alpha: int = 255):
    c = color.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), alpha


def annotate(jpeg: bytes, hazards: list) -> bytes:
    """Overlay a 3x3 locator grid and numbered markers coloured by risk band."""
    base = Image.open(io.BytesIO(jpeg)).convert("RGBA")
    w, h = base.size
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    for i in (1, 2):  # faint grid lines
        d.line([(w * i / 3, 0), (w * i / 3, h)], fill=(255, 255, 255, 60), width=1)
        d.line([(0, h * i / 3), (w, h * i / 3)], fill=(255, 255, 255, 60), width=1)

    r = max(14, min(w, h) // 22)
    font = _font(int(r * 1.05))
    by_zone = {}
    for hz in hazards:
        by_zone.setdefault(hz["zone"], []).append(hz)

    for zone, items in by_zone.items():
        idx = ZONES.index(zone) if zone in ZONES else 4
        cx, cy = (idx % 3 + 0.5) * w / 3, (idx // 3 + 0.5) * h / 3
        n = len(items)
        for k, hz in enumerate(items):
            x = cx + (k - (n - 1) / 2) * r * 2.3
            col = BAND_COLOR[hz["band"]]
            d.ellipse([x - r - 4, cy - r - 4, x + r + 4, cy + r + 4], fill=_hex(col, 70))
            d.ellipse([x - r, cy - r, x + r, cy + r], fill=_hex(col), outline=(255, 255, 255, 255), width=2)
            label = hz["ref"].replace("H", "")
            bb = d.textbbox((0, 0), label, font=font)
            d.text((x - (bb[2] - bb[0]) / 2 - bb[0], cy - (bb[3] - bb[1]) / 2 - bb[1]), label, font=font, fill=(255, 255, 255, 255))

    out = Image.alpha_composite(base, overlay).convert("RGB")
    buf = io.BytesIO()
    out.save(buf, format="JPEG", quality=90)
    return buf.getvalue()
