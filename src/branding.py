"""Round logo from assets/logo.jpg, placed on every chart/card."""
import os
import numpy as np
from . import config

_cache = {}


def logo_rgba(px=160):
    """Circular RGBA array (px x px) or None if no logo file."""
    if px in _cache:
        return _cache[px]
    if not os.path.exists(config.LOGO_IMAGE):
        _cache[px] = None
        return None
    from PIL import Image
    im = Image.open(config.LOGO_IMAGE).convert("RGB")
    s = min(im.size)
    im = im.crop(((im.width - s) // 2, (im.height - s) // 2, (im.width + s) // 2, (im.height + s) // 2)).resize((px, px))
    a = np.asarray(im)
    yy, xx = np.mgrid[:px, :px]
    r = px / 2
    alpha = (np.hypot(xx - r + 0.5, yy - r + 0.5) <= r - 1).astype(np.uint8) * 255
    _cache[px] = np.dstack([a, alpha])
    return _cache[px]


def add_logo_fig(fig, x, y, size_frac_w):
    """Place the logo with its lower-left at figure fraction (x, y); width = size_frac_w of figure width (kept square)."""
    lg = logo_rgba()
    if lg is None:
        return
    w, h = fig.get_size_inches()
    ax = fig.add_axes([x, y, size_frac_w, size_frac_w * w / h], zorder=20)
    ax.imshow(lg); ax.axis("off")


def add_logo_before_text(fig, text_artist, size_px=34, gap_px=8):
    """Put the logo immediately left of an existing (right-aligned) footer text."""
    if logo_rgba() is None:
        return
    fig.canvas.draw()
    bb = text_artist.get_window_extent().transformed(fig.transFigure.inverted())
    w, h = fig.get_size_inches(); dpi = fig.dpi
    fw = size_px / (w * dpi)
    add_logo_fig(fig, bb.x0 - fw - gap_px / (w * dpi), bb.y0 + bb.height / 2 - (fw * w / h) / 2, fw)
