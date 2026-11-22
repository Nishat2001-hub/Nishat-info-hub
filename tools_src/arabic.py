import uharfbuzz as hb, freetype
import numpy as np
from PIL import Image

_path = 'fonts/quran.ttf'
_blob = hb.Blob.from_file_path(_path)
_face = hb.Face(_blob)
_hbfont = hb.Font(_face)
_upem = _face.upem
_ftface = freetype.Face(_path)

def shape(text):
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(_hbfont, buf)
    return [(i.codepoint, p.x_advance, p.x_offset, p.y_offset) for i, p in zip(buf.glyph_infos, buf.glyph_positions)]

def arab_img(text, size, color=(255, 201, 60)):
    gl = shape(text)
    _ftface.set_pixel_sizes(0, size)
    asc = _ftface.size.ascender / 64
    desc = _ftface.size.descender / 64
    k = size / _upem
    adv = sum(g[1] for g in gl) * k
    im = Image.new('RGBA', (int(adv) + 32, int(asc - desc) + 16), (0, 0, 0, 0))
    base_y = int(asc) + 8
    pen_x = 8.0

    for gid, ax, ox, oy in gl:
        _ftface.load_glyph(gid, freetype.FT_LOAD_RENDER)
        g = _ftface.glyph
        bmp = g.bitmap
        if bmp.width > 0 and bmp.rows > 0:
            arr = np.array(bmp.buffer, dtype=np.uint8).reshape(bmp.rows, bmp.width)
            patch = np.zeros((bmp.rows, bmp.width, 4), dtype=np.uint8)
            patch[:, :, 0], patch[:, :, 1], patch[:, :, 2] = color
            patch[:, :, 3] = arr
            gx = int(pen_x + ox * k)
            gy = base_y - g.bitmap_top - int(oy * k)
            im.alpha_composite(Image.fromarray(patch), (max(gx, 0), max(gy, 0)))
        pen_x += ax * k
    bbox = im.getbbox()
    return im.crop(bbox) if bbox else im
