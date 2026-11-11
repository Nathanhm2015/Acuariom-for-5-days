"""
Genera GIFs de peces de colores a partir de salmon.gif.
Corre una sola vez: python make_colored_fish.py
"""
from PIL import Image
import os

SRC = 'animation/salmon.gif'

COLORS = {
    'red':    (230,  80,  80),
    'orange': (255, 160,  50),
    'yellow': (255, 220,  60),
    'green':  ( 80, 200, 100),
    'blue':   ( 80, 160, 255),
    'purple': (190, 100, 200),
    'golden': (255, 215,   0),
}

def tint_frame(frame_rgba, tint_rgb):
    """Applies a color tint to an RGBA PIL image preserving alpha."""
    r, g, b, a = frame_rgba.split()
    tr, tg, tb = [c / 255.0 for c in tint_rgb]
    r = r.point(lambda x: int(x * tr))
    g = g.point(lambda x: int(x * tg))
    b = b.point(lambda x: int(x * tb))
    return Image.merge('RGBA', (r, g, b, a))

src = Image.open(SRC)
n_frames = getattr(src, 'n_frames', 1)

# Detect background color from first frame top-left pixel
src.seek(0)
first = src.convert('RGBA')
bg_color = first.getpixel((0, 0))[:3]

def remove_bg(img_rgba, bg, threshold=40):
    pixels = list(img_rgba.getdata())
    new_pixels = []
    br, bg_r, bb = bg
    for px in pixels:
        r, g, b, a = px
        if abs(r - br) < threshold and abs(g - bg_r) < threshold and abs(b - bb) < threshold:
            new_pixels.append((r, g, b, 0))
        else:
            new_pixels.append(px)
    result = img_rgba.copy()
    result.putdata(new_pixels)
    return result

for name, tint in COLORS.items():
    frames = []
    durations = []
    for i in range(n_frames):
        src.seek(i)
        frame = src.convert('RGBA')
        frame = remove_bg(frame, bg_color)
        frame = tint_frame(frame, tint)
        frames.append(frame)
        try:
            durations.append(src.info.get('duration', 80))
        except Exception:
            durations.append(80)

    out_path = f'animation/fish_{name}.gif'
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        loop=0,
        duration=durations,
        disposal=2,
    )
    print(f'Guardado: {out_path}')

print('Listo.')
