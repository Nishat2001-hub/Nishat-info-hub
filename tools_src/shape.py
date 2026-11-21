import uharfbuzz as hb, freetype
import numpy as np
from PIL import Image, ImageFilter

_c = {}
def _get(key):
    if key not in _c:
        path = f'fonts/{key}.ttf'
        blob = hb.Blob.from_file_path(path)
        face = hb.Face(blob)
        _c[key] = (hb.Font(face), face.upem, freetype.Face(path))
    return _c[key]

def shape(key, text):
    hbfont, upem, _ = _get(key)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hbfont, buf)
    return [(i.codepoint, p.x_advance, p.x_offset, p.y_offset)
            for i, p in zip(buf.glyph_infos, buf.glyph_positions)]

def w(key, text, size):
    return sum(g[1] for g in shape(key, text)) * size / _get(key)[1]

def img(key, text, size, color, stroke=0, sf=None):
    hbfont, upem, ft = _get(key)
    gl = shape(key, text)
    ft.set_pixel_sizes(0, size)
    k = size / upem
    spawn = ft.size.ascender / 64
    sdesc = ft.size.descender / 64
    if not gl:
        return Image.new('RGBA', (1, int(spawn - sdesc))), int(spawn), 0.0
    items = []
    pen = 0.0
    for gid, ax, ox, oy in gl:
        ft.load_glyph(gid, freetype.FT_LOAD_RENDER)
        g = ft.glyph
        b = g.bitmap
        if b.width > 0 and b.rows > 0:
            arr = np.frombuffer(bytes(b.buffer), np.uint8).reshape(b.rows, b.width)
            items.append((pen + ox * k + g.bitmap_left, -g.bitmap_top - oy * k, arr))
        pen += ax * k
    if not items:
        pad = stroke + 2
        h = int(spawn - sdesc) + pad * 2
        return Image.new('RGBA', (int(pen) + 2 * pad, h)), int(spawn) + pad, pen
    x0 = min(it[0] for it in items)
    x1 = max(it[0] + it[2].shape[1] for it in items)
    y0 = min(it[1] for it in items)
    y1 = max(it[1] + it[2].shape[0] for it in items)
    pad = stroke + 2
    ih = int(y1 - y0) + pad * 2
    iw = int(x1 - x0) + pad * 2
    body = np.zeros((ih, iw), np.uint8)
    dx = -x0 + pad
    dy = -y0 + pad
    for gx, gy, arr in items:
        px = int(gx + dx)
        py = int(gy + dy)
        body[py:py + arr.shape[0], px:px + arr.shape[1]] = np.maximum(
            body[py:py + arr.shape[0], px:px + arr.shape[1]], arr)
    base = -int(y0) + pad
    if stroke > 0:
        dil = np.array(Image.fromarray(body).filter(ImageFilter.MaxFilter(2 * stroke + 1)), int)
        sarr = np.clip(dil - body.astype(int), 0, 255).astype(np.uint8)
        out = np.zeros((ih, iw, 4), np.uint8)
        out[..., 0], out[..., 1], out[..., 2] = (sf if sf else color)[:3]
        out[..., 3] = dil
        barr = np.zeros((ih, iw, 4), np.uint8)
        barr[..., 0], barr[..., 1], barr[..., 2] = color[:3]
        barr[..., 3] = body
        outim = Image.fromarray(out)
        outim.alpha_composite(Image.fromarray(barr))
    else:
        out = np.zeros((ih, iw, 4), np.uint8)
        out[..., 0], out[..., 1], out[..., 2] = color[:3]
        out[..., 3] = body
        outim = Image.fromarray(out)
    return outim, base, pen
