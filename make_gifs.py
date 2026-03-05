"""
make_gifs.py — Generate animated wing-flap GIFs from static bird PNGs.
Run once:  python make_gifs.py
Outputs:   images/pelicano.gif
           images/ave_pescador.gif
"""
import math
from PIL import Image


def make_flap_gif(src_path, dst_path, target_size, n_frames=16, duration=50):
    """
    Build a looping GIF that squishes/stretches the image vertically
    to simulate a wing-beat cycle.
    target_size : (width, height) to scale the sprite to in the game
    n_frames    : number of animation frames
    duration    : milliseconds per frame
    """
    base = Image.open(src_path).convert('RGBA')
    # Scale to game sprite size first so the GIF is compact
    base = base.resize(target_size, Image.LANCZOS)
    bw, bh = base.size

    frames = []
    for i in range(n_frames):
        t = 2 * math.pi * i / n_frames
        # +15 % when wings up, −15 % when wings down
        scale_h = 1.0 + 0.15 * math.sin(t)
        new_h   = max(4, int(bh * scale_h))

        resized = base.resize((bw, new_h), Image.LANCZOS)

        # Center vertically on a canvas the same size as the original
        canvas  = Image.new('RGBA', (bw, bh), (0, 0, 0, 0))
        paste_y = (bh - new_h) // 2
        if paste_y < 0:
            # Taller than canvas: crop the top/bottom overflow
            crop_top = -paste_y
            resized  = resized.crop((0, crop_top, bw, crop_top + bh))
            paste_y  = 0
        canvas.paste(resized, (0, paste_y))
        frames.append(canvas)

    # Pillow ≥ 6 can save RGBA lists as animated GIF with transparency
    frames[0].save(
        dst_path,
        save_all=True,
        append_images=frames[1:],
        loop=0,          # loop forever
        duration=duration,
        disposal=2,      # restore background between frames
    )
    print(f"✓  {dst_path}  ({n_frames} frames × {duration} ms)")


if __name__ == '__main__':
    make_flap_gif('images/pelicano.png',     'images/pelicano.gif',     target_size=(115, 78))
    make_flap_gif('images/ave pescador.png', 'images/ave_pescador.gif', target_size=(100, 70))
    print("Done! GIFs are ready in images/")
