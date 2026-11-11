#!/usr/bin/env python3

import pygame
import json
import math
import os
import random
import sys
import smtplib
import threading
import colorsys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum

# ── Correo del remitente ─────────────────────────────────────────────────────
#  1. Activa la verificación en 2 pasos en tu Gmail:
#     https://myaccount.google.com/signinoptions/two-step-verification
#  2. Ve a: https://myaccount.google.com/apppasswords
#     → Nombre de la app: "Wings and Fish" → GENERAR
#  3. Copia las 16 letras que te da Google (sin espacios) y pégalas abajo:
EMAIL_SENDER   = "nathanherreramadrigal@gmail.com"
EMAIL_PASSWORD = "ItsTimeToCom3+"   # <-- REEMPLAZA esto con la contraseña de app de 16 letras
EMAIL_OWNER    = "nathanherreramadrigal@gmail.com"   # correo donde te llegan los avisos de compra
# ─────────────────────────────────────────────────────────────────────────────

# Optional Pillow — used to load animated GIF frames
try:
    from PIL import Image as _PILImage
    _PIL_OK = True
except ImportError:
    _PIL_OK = False


def _load_gif_frames(path):
    """Return a list of pygame surfaces, one per GIF frame, with bg removed."""
    frames = []
    bg_color = None
    with _PILImage.open(path) as gif:
        for i in range(getattr(gif, 'n_frames', 1)):
            gif.seek(i)
            frame = gif.convert('RGBA')
            # Detect background from top-left pixel of first frame
            if bg_color is None:
                bg_color = frame.getpixel((0, 0))
            # Remove background: set pixels close to bg_color to transparent
            raw = frame.tobytes()
            new_bytes = bytearray(raw)
            br, bg, bb, _ = bg_color
            for i in range(0, len(raw), 4):
                r, g, b = raw[i], raw[i + 1], raw[i + 2]
                if abs(r - br) < 40 and abs(g - bg) < 40 and abs(b - bb) < 40:
                    new_bytes[i + 3] = 0
            frame = _PILImage.frombytes('RGBA', frame.size, bytes(new_bytes))
            surf = pygame.image.fromstring(
                frame.tobytes(), frame.size, 'RGBA'
            ).convert_alpha()
            frames.append(surf)
    return frames


pygame.init()
info = pygame.display.Info()
SCREEN_WIDTH  = max(1280, info.current_w if info.current_w > 0 else 1920)
SCREEN_HEIGHT = max(720, info.current_h if info.current_h > 0 else 1080)
FPS           = 60

# ── Color palette ─────────────────────────────────────────────────────────
SKY_TOP       = (100, 190, 240)
SKY_BOTTOM    = (160, 220, 255)
WATER_SURFACE = ( 30, 140, 200)
WATER_DEEP    = ( 10,  60, 130)
WHITE         = (255, 255, 255)
BLACK         = (  0,   0,   0)
ORANGE        = (255, 140,  30)
RED           = (220,  50,  50)
GREEN         = ( 50, 200,  80)
GRAY          = (150, 150, 160)
BROWN         = (120,  70,  30)
HUD_BLUE      = ( 40, 130, 200)
BTN_GREEN     = ( 50, 160,  60)
DARK_GREEN    = ( 30,  90,  40)

WATER_Y = 370   # y-coordinate of the water surface
STARTING_FISH_COUNT = 22
MAX_WAVE_FISH_COUNT = 34
STAMINA_DRAIN_SECONDS = 45
BOSS_STAMINA_DRAIN_SECONDS = 90
CAMPAIGN_LEVEL_COUNT = 20


# ═══════════════════════════════════════════════════════════════════════════
#  GAME STATE
# ═══════════════════════════════════════════════════════════════════════════
class GameState(Enum):
    MENU          = 0   # new animated main menu
    START         = 1
    FLYING        = 2
    DIVING        = 3
    UNDERWATER    = 4
    RISING        = 5
    SETTINGS      = 6
    GAME_OVER     = 7
    SHOP          = 8
    ITEM_STORE    = 9
    PURCHASE_FORM = 10
    SKINS         = 11
    MODE_SELECT   = 12
    TUTORIAL      = 13
    LEVEL_SELECT  = 14
    LEVEL_COMPLETE = 15


# ═══════════════════════════════════════════════════════════════════════════
#  SALMON CLASS  (GIF sprite, medium speed)
# ═══════════════════════════════════════════════════════════════════════════
_salmon_frames = []   # loaded once, shared across all Salmon instances

def _ensure_salmon_frames():
    global _salmon_frames
    if _salmon_frames:
        return
    try:
        if _PIL_OK:
            raw = _load_gif_frames('animation/salmon.gif')
            _salmon_frames = [pygame.transform.scale(f, (72, 36)) for f in raw]
        else:
            surf = pygame.image.load('animation/salmon.gif').convert_alpha()
            _salmon_frames = [pygame.transform.scale(surf, (72, 36))]
    except Exception as e:
        print(f"salmon.gif not loaded: {e}")


class Salmon:
    """GIF-animated salmon that swims at medium speed."""

    def __init__(self):
        _ensure_salmon_frames()
        self.x      = float(random.randint(120, SCREEN_WIDTH - 120))
        self.y      = float(random.randint(WATER_Y + 50, SCREEN_HEIGHT - 60))
        speed       = random.uniform(1.2, 1.9)
        self.vx     = speed * random.choice([-1, 1])
        self.vy     = random.uniform(-0.25, 0.25)
        self.radius = 26   # collision radius (matches sprite size)
        self.color  = (220, 100, 60)  # salmon orange (fallback for caught_fish drawing)
        self.alive  = True
        self.frame  = 0
        self.value  = 4   # 4 monedas por salmón
        self.golden = False

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.frame += 1
        if self.x < 80 or self.x > SCREEN_WIDTH - 80:
            self.vx *= -1
        if self.y < WATER_Y + 30 or self.y > SCREEN_HEIGHT - 50:
            self.vy *= -1
        self.x = max(80, min(SCREEN_WIDTH - 80, self.x))
        self.y = max(WATER_Y + 30, min(SCREEN_HEIGHT - 50, self.y))

    def draw(self, screen):
        if not self.alive:
            return
        if not _salmon_frames:
            # fallback: draw as a simple orange ellipse
            cx, cy = int(self.x), int(self.y)
            pygame.draw.ellipse(screen, (220, 100, 60), (cx - 26, cy - 13, 52, 26))
            return
        surf = _salmon_frames[(self.frame // 5) % len(_salmon_frames)]
        # GIF faces left by default; flip when going right
        if self.vx > 0:
            surf = pygame.transform.flip(surf, True, False)
        w, h = surf.get_size()
        screen.blit(surf, (int(self.x) - w // 2, int(self.y) - h // 2))


def _spawn_fish(luck=0):
    """Spawn one fish; with luck>0 may return a GoldenFish."""
    if luck > 0 and random.random() < luck * 0.20:
        return GoldenFish()
    return Fish()


def _make_fish_pool(n=STARTING_FISH_COUNT, luck=0):
    """Return a mixed list of Fish, Salmon, and possibly GoldenFish."""
    pool = []
    for i in range(n):
        if i % 3 == 0:
            pool.append(Salmon())
        else:
            pool.append(_spawn_fish(luck))
    return pool


# ═══════════════════════════════════════════════════════════════════════════
#  FISH CLASS
# ═══════════════════════════════════════════════════════════════════════════
class Fish:
    TYPES = {
        'red':    (230,  80,  80),
        'orange': (255, 160,  50),
        'yellow': (255, 220,  60),
        'green':  ( 80, 200, 100),
        'blue':   ( 80, 160, 255),
        'purple': (190, 100, 200),
    }

    def __init__(self, x=None, y=None):
        self.x      = float(x if x is not None else random.randint(120, SCREEN_WIDTH - 120))
        self.y      = float(y if y is not None else random.randint(WATER_Y + 40, SCREEN_HEIGHT - 40))
        self.vx     = random.uniform(-1.5, 1.5)
        self.vy     = random.uniform(-0.4, 0.4)
        self.radius = random.randint(13, 22)
        self.fish_type = random.choice(list(self.TYPES.keys()))
        self.color  = self.TYPES[self.fish_type]
        self.alive  = True
        self.frame  = 0
        self.golden = False
        self.value  = random.randint(2, 4)  # 2–4 monedas por pez normal

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.frame += 1
        if self.x < 80 or self.x > SCREEN_WIDTH - 80:
            self.vx *= -1
        if self.y < WATER_Y + 20 or self.y > SCREEN_HEIGHT - 20:
            self.vy *= -1
        self.x = max(80, min(SCREEN_WIDTH - 80, self.x))
        self.y = max(WATER_Y + 20, min(SCREEN_HEIGHT - 20, self.y))

    def draw(self, screen):
        if not self.alive:
            return
        r  = self.radius
        cx = int(self.x)
        cy = int(self.y)
        if _salmon_frames:
            w, h = r * 4, r * 2
            base = _salmon_frames[(self.frame // 5) % len(_salmon_frames)]
            surf = pygame.transform.scale(base, (w, h)).copy()
            # Apply color tint
            tint = pygame.Surface((w, h), pygame.SRCALPHA)
            tint.fill(self.color + (255,))
            surf.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            if self.vx >= 0:
                surf = pygame.transform.flip(surf, True, False)
            screen.blit(surf, (cx - w // 2, cy - h // 2))
        else:
            pygame.draw.ellipse(screen, self.color, (cx - r, cy - r // 2, r * 2, r))


# ═══════════════════════════════════════════════════════════════════════════
#  GOLDEN FISH CLASS
# ═══════════════════════════════════════════════════════════════════════════
class GoldenFish(Fish):
    """Rare golden fish worth 3 coins."""
    def __init__(self, x=None, y=None):
        super().__init__(x, y)
        self.color  = (255, 215, 0)
        self.golden = True
        self.value  = random.randint(8, 12)  # 8–12 monedas por pez dorado
        self.radius = max(self.radius, 20)
        self.vx    *= 0.65
        self.vy    *= 0.65

    def draw(self, screen):
        if not self.alive:
            return
        r  = self.radius
        cx = int(self.x)
        cy = int(self.y)
        # ── glow aura ─────────────────────────────────
        glow_r = r + 6 + int(math.sin(self.frame * 0.08) * 3)
        glow_surf = pygame.Surface((glow_r * 2 + 4, glow_r * 2 + 4), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_surf, (255, 215, 0, 60),
                            (0, 0, glow_r * 2 + 4, glow_r + 4))
        screen.blit(glow_surf, (cx - glow_r - 2, cy - glow_r // 2 - 2))
        if _salmon_frames:
            w, h = r * 4, r * 2
            base = _salmon_frames[(self.frame // 5) % len(_salmon_frames)]
            surf = pygame.transform.scale(base, (w, h)).copy()
            # Golden tint
            tint = pygame.Surface((w, h), pygame.SRCALPHA)
            tint.fill((255, 215, 0, 255))
            surf.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            if self.vx >= 0:
                surf = pygame.transform.flip(surf, True, False)
            screen.blit(surf, (cx - w // 2, cy - h // 2))
        else:
            pygame.draw.ellipse(screen, (255, 215, 0), (cx - r, cy - r // 2, r * 2, r))
        # ── sparkles ──────────────────────────────────
        for i in range(4):
            ang = 2 * math.pi * i / 4 + self.frame * 0.05
            sx2 = cx + int(math.cos(ang) * (r + 11))
            sy2 = cy + int(math.sin(ang) * (r + 11))
            sr  = max(1, int(2 + math.sin(self.frame * 0.12 + i) * 1.5))
            pygame.draw.circle(screen, WHITE, (sx2, sy2), sr)


# ═══════════════════════════════════════════════════════════════════════════
#  PUFFER FISH CLASS  (obstacle — costs -3 coins on contact)
# ═══════════════════════════════════════════════════════════════════════════
class PufferFish:
    def __init__(self, hp=1):
        self.x             = float(random.randint(150, SCREEN_WIDTH - 150))
        self.y             = float(random.randint(WATER_Y + 60, SCREEN_HEIGHT - 60))
        self.vx            = random.choice([-1, 1]) * random.uniform(0.5, 1.1)
        self.vy            = random.uniform(-0.3, 0.3)
        self.radius        = 28
        self.alive         = True
        self.frame         = 0
        self.hp            = hp
        self.max_hp        = hp
        self.hit_flash     = 0     # red-flash countdown on hit
        self.sting_cooldown = 0   # frames before it can sting again

    def update(self):
        if not self.alive:
            return
        self.frame += 1
        self.x += self.vx
        self.y += self.vy
        if self.x < 100 or self.x > SCREEN_WIDTH - 100:
            self.vx *= -1
        if self.y < WATER_Y + 45 or self.y > SCREEN_HEIGHT - 55:
            self.vy *= -1
        self.x = max(100, min(SCREEN_WIDTH - 100, self.x))
        self.y = max(WATER_Y + 45, min(SCREEN_HEIGHT - 55, self.y))
        if self.sting_cooldown > 0:
            self.sting_cooldown -= 1
        if self.hit_flash > 0:
            self.hit_flash -= 1

    def draw(self, screen):
        if not self.alive:
            return
        cx, cy = int(self.x), int(self.y)
        r  = self.radius
        puff = int(math.sin(self.frame * 0.07) * 5)
        # spines
        spine_color = (255, 80, 60) if self.hit_flash > 0 else (220, 180, 60)
        for i in range(12):
            a  = 2 * math.pi * i / 12
            x1 = cx + int(math.cos(a) * (r + puff))
            y1 = cy + int(math.sin(a) * (r + puff))
            x2 = cx + int(math.cos(a) * (r + puff + 11))
            y2 = cy + int(math.sin(a) * (r + puff + 11))
            pygame.draw.line(screen, spine_color, (x1, y1), (x2, y2), 2)
        # body
        body_col  = (255, 80, 60)  if self.hit_flash > 0 else (190, 150, 50)
        inner_col = (255, 130, 90) if self.hit_flash > 0 else (240, 205, 90)
        pygame.draw.circle(screen, body_col,  (cx, cy), r + puff)
        pygame.draw.circle(screen, inner_col, (cx, cy), r + puff - 4)
        # spots
        for ox, oy, sr in [(-9, -6, 5), (9, -4, 4), (0, 9, 6), (-13, 4, 3)]:
            pygame.draw.circle(screen, (160, 100, 25), (cx + ox, cy + oy), sr)
        # eyes
        for side in (-1, 1):
            ex, ey = cx + side * (r // 2), cy - r // 3
            pygame.draw.circle(screen, (255, 255, 255), (ex, ey), 6)
            pygame.draw.circle(screen, (0, 0, 0), (ex + side, ey), 3)
        # warning "!" above
        wx, wy = cx, cy - r - puff - 18
        pygame.draw.rect(screen, (255, 50, 50), (wx - 2, wy,      4, 10))
        pygame.draw.rect(screen, (255, 50, 50), (wx - 2, wy + 13, 4,  4))
        # HP bar
        bar_w, bar_h = 44, 6
        bar_x, bar_y = cx - bar_w // 2, wy - 12
        pygame.draw.rect(screen, (60, 0, 0), (bar_x, bar_y, bar_w, bar_h), border_radius=2)
        fill_w = int(bar_w * self.hp / self.max_hp)
        if fill_w > 0:
            hp_col = (80, 220, 80) if self.hp == self.max_hp else (220, 80, 80)
            pygame.draw.rect(screen, hp_col, (bar_x, bar_y, fill_w, bar_h), border_radius=2)
        pygame.draw.rect(screen, (200, 50, 50), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=2)


# ═══════════════════════════════════════════════════════════════════════════
#  CRAB CLASS
# ═══════════════════════════════════════════════════════════════════════════
SAND_Y = SCREEN_HEIGHT - 38   # y where crabs sit (on top of the sand strip)

class Crab:
    COLOR_SHELL = (210,  85,  25)
    COLOR_BODY  = (240, 120,  40)

    def __init__(self):
        self.x     = float(random.randint(80, SCREEN_WIDTH - 80))
        self.y     = float(SAND_Y)
        self.vx    = random.choice([-1, 1]) * random.uniform(0.4, 1.1)
        self.alive = True
        self.frame = 0

    def update(self):
        self.frame += 1
        self.x += self.vx
        if self.x < 60 or self.x > SCREEN_WIDTH - 60:
            self.vx *= -1
        self.x = max(60, min(SCREEN_WIDTH - 60, self.x))

    def draw(self, screen):
        if not self.alive:
            return
        cx, cy = int(self.x), int(self.y)
        leg_off = int(math.sin(self.frame * 0.22) * 4)
        # legs (3 on each side)
        for side in (-1, 1):
            for i, (dx, dy) in enumerate([(10, -5), (16, 1), (10, 7)]):
                x0, y0 = cx + side * 7, cy
                x1 = cx + side * dx
                y1 = cy + dy + (leg_off if i % 2 == 0 else -leg_off)
                pygame.draw.line(screen, self.COLOR_SHELL, (x0, y0), (x1, y1), 2)
        # shell body
        pygame.draw.ellipse(screen, self.COLOR_SHELL, (cx - 16, cy - 9,  32, 18))
        pygame.draw.ellipse(screen, self.COLOR_BODY,  (cx - 11, cy - 6,  22, 12))
        # claws
        for side in (-1, 1):
            claw_x = cx + side * 21
            claw_y = cy - 5
            pygame.draw.circle(screen, self.COLOR_SHELL, (claw_x, claw_y), 7)
            pygame.draw.circle(screen, self.COLOR_BODY,  (claw_x + side * 4, claw_y - 3), 4)
        # eyes on stalks
        for side in (-1, 1):
            ex, ey = cx + side * 7, cy - 13
            pygame.draw.line(screen, self.COLOR_SHELL, (cx + side * 5, cy - 9), (ex, ey), 2)
            pygame.draw.circle(screen, (255, 255, 255), (ex, ey), 4)
            pygame.draw.circle(screen, (0, 0, 0),       (ex, ey), 2)


# ═══════════════════════════════════════════════════════════════════════════
#  BIRD CLASS
# ═══════════════════════════════════════════════════════════════════════════
class Bird:
    """
    bird_type: 'pelican' | 'osprey'
      Brown Pelican -> cream/white body, dark-brown wings, gray beak, orange gular pouch
      Osprey        -> white chest, dark-brown wings, dark hooked beak, yellow eye
    """
    CONFIGS = {
        # max_depth : pixels below WATER_Y; leave room for the bottom sand
        # uw_entry_vy : downward speed when first entering the water
        # uw_decay    : velocity multiplier each frame underwater (closer to 1 = goes deeper)
        'pelican': dict(speed=3.5, dive_speed=11, capture_radius=48, wingspan=95,
                max_depth=SCREEN_HEIGHT - WATER_Y - 78,
                        uw_entry_vy=5.5, uw_decay=0.997),
        'osprey':  dict(speed=5.0, dive_speed=15, capture_radius=32, wingspan=78,
                max_depth=(SCREEN_HEIGHT - WATER_Y - 78) // 2,
                        uw_entry_vy=3.5, uw_decay=0.997),
    }

    # Real-life color palettes
    _COLORS = {
        'pelican': dict(body=(235, 225, 200), wing=(80, 52, 28),  beak=(145, 140, 135)),
        'osprey':  dict(body=(230, 225, 215), wing=(72, 50, 25),  beak=(38, 32, 28)),
    }

    def __init__(self, bird_type, x, y):
        self.bird_type = bird_type
        self.x         = float(x)
        self.y         = float(y)
        self.vx        = 0.0
        self.vy        = 0.0
        self.state     = 'flying'
        cfg = self.CONFIGS[bird_type]
        self.speed          = cfg['speed']
        self.dive_speed     = cfg['dive_speed']
        self.capture_radius = cfg['capture_radius']
        self.wingspan       = cfg['wingspan']
        self.max_depth      = cfg['max_depth']
        self.uw_entry_vy    = cfg['uw_entry_vy']
        self.uw_decay       = cfg['uw_decay']
        self.angle          = 0.0
        self.frame          = 0
        self.caught_fish    = None
        self.facing_right   = True
        self.fire_effect    = ''      # effect name: '', 'fire', 'water', 'stars', 'leaves', 'gold', 'silver', 'rainbow'
        self._fire_particles = []     # list of [x, y, vx, vy, life, color]
        self._trail          = []     # list of [x, y, hue] for rainbow trail
        self.beak_open       = 0       # frames for pelican mouth-open effect
        # HP & combat
        self.max_hp         = 20 if bird_type == 'pelican' else 12
        self.hp             = self.max_hp
        self.hit_flash      = 0   # red-flash countdown when hit
        self.ammo           = 3
        self.shoot_cooldown = 0
        # Special abilities
        self.special_cooldown  = 0   # frames until special can be used again
        self.burst_queue       = 0   # pelican: bullets still queued to fire this burst
        self.burst_interval    = 0   # frames until next burst bullet fires
        self.peck_cooldown     = 0      # osprey: cooldown for right-click peck (frames)
        self.peck_dash         = False  # osprey: actively dashing
        self.peck_phase        = 'off'  # 'off' | 'going' | 'returning'
        self._peck_rx          = 0.0    # return-to X
        self._peck_ry          = 0.0    # return-to Y
        self.peck_trail        = []     # osprey: trail positions for visual effect
        self.drill_dash        = False  # osprey: E taladro spin-dive active
        self.drill_phase       = 'off'  # 'off' | 'going' | 'returning'
        self._drill_rx         = 0.0
        self._drill_ry         = 0.0
        self.drill_angle       = 0.0    # osprey: spin angle for drill visual (degrees)
        self._peck_hit_ids     = set()  # enemies already hit during this peck
        self._drill_hit_ids    = set()  # enemies already hit during this drill
        # Visual colors
        pal = self._COLORS[bird_type]
        self.body_color = pal['body']
        self.wing_color = pal['wing']
        self.beak_color = pal['beak']

        # Sprite frames for animation (GIF) + static base for rotated states
        self.frames      = []    # list of pygame surfaces (flying frames)
        self.sprite_base = None  # first frame / static reference
        _bird_assets = {
            'pelican': ('animation/pelican.gif',      (125, 85)),
            'osprey':  ('animation/ave pescador.gif', (110, 77)),
        }
        if bird_type in _bird_assets:
            gif_path, size = _bird_assets[bird_type]
            try:
                if _PIL_OK:
                    raw_frames = _load_gif_frames(gif_path)
                    self.frames = [pygame.transform.scale(f, size) for f in raw_frames]
                else:
                    # Pillow not available — load just the first frame with pygame
                    surf = pygame.image.load(gif_path).convert_alpha()
                    self.frames = [pygame.transform.scale(surf, size)]
                self.sprite_base = self.frames[0]
            except Exception as e:
                print(f"{gif_path} not loaded: {e}")

    # ── movement with arrow keys ──────────────────
    def move(self, dx, dy):
        if self.state != 'flying':
            return
        self.vx += dx * 0.65
        self.vy += dy * 0.65
        self.vx *= 0.84
        self.vy *= 0.84
        spd = math.hypot(self.vx, self.vy)
        if spd > self.speed:
            self.vx = self.vx / spd * self.speed
            self.vy = self.vy / spd * self.speed

    def start_dive(self):
        if self.state != 'flying':
            return False
        if self.y > WATER_Y - 30:
            return False
        self.state = 'diving'
        self.vy    = self.dive_speed
        self.vx   *= 0.25
        return True

    def update(self):
        self.frame += 1
        if self.hit_flash > 0:
            self.hit_flash -= 1
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.special_cooldown > 0:
            self.special_cooldown -= 1
        if self.burst_interval > 0:
            self.burst_interval -= 1
        if self.beak_open > 0:
            self.beak_open -= 1
        # trail: keep last 8 positions for osprey peck visual
        if self.peck_dash:
            self.peck_trail.append((int(self.x), int(self.y)))
            if len(self.peck_trail) > 8:
                self.peck_trail.pop(0)
        else:
            self.peck_trail = []
        # peck cooldown + drill spin angle
        if self.peck_cooldown > 0:
            self.peck_cooldown -= 1
        if self.drill_dash:
            self.drill_angle = (self.drill_angle + 22.0) % 360.0

        if self.state == 'flying':
            if self.peck_dash or self.drill_dash:
                # position controlled entirely by peck/drill blocks in Game.update
                self.vx = 0.0
                self.vy = 0.0
            else:
                self.x += self.vx
                self.y += self.vy
                # soft gravity
                if self.vy < 0.5:
                    self.vy += 0.06
                self.x = max(30, min(SCREEN_WIDTH - 30, self.x))
                self.y = max(30, min(WATER_Y - 15, self.y))

        elif self.state == 'diving':
            self.x += self.vx
            self.y += self.vy
            if self.y >= WATER_Y + 15:
                self.state = 'underwater'
                self.vy = self.uw_entry_vy

        elif self.state == 'underwater':
            self.x += self.vx
            self.y += self.vy
            self.vy *= self.uw_decay
            self.y   = min(self.y, SCREEN_HEIGHT - 20)

        elif self.state == 'rising':
            self.x += self.vx
            self.y += self.vy
            self.vy -= 0.22
            if self.y < WATER_Y - 25:
                self.state = 'flying'
                self.vy = -2.0

        # visual angle
        if abs(self.vx) > 0.1 or abs(self.vy) > 0.1:
            self.angle = math.atan2(self.vy, max(0.01, abs(self.vx)))
        if abs(self.vx) > 0.05:
            self.facing_right = self.vx >= 0

    # ── helper: animated stripe overlay ────────────────────────────────
    @staticmethod
    def _fire_stripe_overlay(surf, frame, hue_start, hue_end, stripe_h=8, alpha=130, scroll_speed=3, scroll_up=False):
        """
        Draw a scrolling multi-stripe color overlay on a copy of surf.
        The stripes cycle through hue_start→hue_end (degrees).
        scroll_up=True moves stripes upward (water/bubbles feel).
        """
        w, h = surf.get_size()
        ov = pygame.Surface((w, h), pygame.SRCALPHA)
        band_total = stripe_h * 3
        if scroll_up:
            offset = -(frame * scroll_speed) % band_total
        else:
            offset = (frame * scroll_speed) % band_total
        hue_range = hue_end - hue_start
        for y in range(h):
            band = ((y + offset) % band_total) / band_total
            hue  = (hue_start + band * hue_range) / 360
            rc, gc, bc = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            pygame.draw.line(ov, (int(rc*255), int(gc*255), int(bc*255), alpha), (0, y), (w, y))
        out = surf.copy()
        out.blit(ov, (0, 0), special_flags=pygame.BLEND_ADD)
        return out
    def draw(self, screen):
        # ── rainbow trail (behind everything) ──────
        if self.fire_effect == 'rainbow' and self._trail:
            for ti, tp in enumerate(self._trail):
                frac = (ti + 1) / len(self._trail)
                alpha = int(frac * 200)
                r_sz  = max(2, int(frac * 14))
                rc, gc, bc = colorsys.hsv_to_rgb(tp[2] / 360, 1.0, 1.0)
                tc = pygame.Surface((r_sz*2+2, r_sz*2+2), pygame.SRCALPHA)
                pygame.draw.circle(tc, (int(rc*255), int(gc*255), int(bc*255), alpha),
                                   (r_sz+1, r_sz+1), r_sz)
                screen.blit(tc, (int(tp[0])-r_sz-1, int(tp[1])-r_sz-1))

        # ── sprite path (both birds, all states) ──────
        if self.sprite_base:
            cx, cy = int(self.x), int(self.y)
            if self.state == 'flying':
                # Cycle through pre-computed GIF frames (// 4 → ~15 fps animation at 60 fps game)
                surf = self.frames[(self.frame // 4) % len(self.frames)]
                # GIF sprites face left by default — flip to face right
                if self.facing_right:
                    surf = pygame.transform.flip(surf, True, False)
                if self.fire_effect == 'rainbow':
                    hue = (self.frame * 5) % 360
                    rc2, gc2, bc2 = colorsys.hsv_to_rgb(hue / 360, 0.95, 1.0)
                    surf = surf.copy()
                    ov = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
                    ov.fill((int(rc2*255), int(gc2*255), int(bc2*255), 110))
                    surf.blit(ov, (0, 0), special_flags=pygame.BLEND_ADD)
                elif self.fire_effect == 'fire':
                    # 3 scrolling stripes: red → orange → yellow
                    surf = Bird._fire_stripe_overlay(surf, self.frame, 0, 55, stripe_h=20, alpha=160, scroll_speed=4)
                elif self.fire_effect == 'water':
                    surf = Bird._fire_stripe_overlay(surf, self.frame, 190, 230, stripe_h=24, alpha=140, scroll_speed=3, scroll_up=True)
                elif self.fire_effect == 'stars':
                    surf = Bird._fire_stripe_overlay(surf, self.frame, 270, 310, stripe_h=20, alpha=140, scroll_speed=2)
                elif self.fire_effect == 'leaves':
                    surf = Bird._fire_stripe_overlay(surf, self.frame, 90, 140, stripe_h=22, alpha=140, scroll_speed=2)
                elif self.fire_effect == 'gold':
                    surf = Bird._fire_stripe_overlay(surf, self.frame, 40, 60, stripe_h=20, alpha=155, scroll_speed=3)
                elif self.fire_effect == 'silver':
                    surf = Bird._fire_stripe_overlay(surf, self.frame, 200, 220, stripe_h=20, alpha=120, scroll_speed=2)
                w, h = surf.get_size()
                screen.blit(surf, (cx - w // 2, cy - h // 2))
            else:
                if self.state == 'diving':
                    rot_angle = -82
                elif self.state == 'underwater':
                    rot_angle = -75
                else:                                      # rising
                    rot_angle = 75
                surf = self.sprite_base
                # GIF sprites face left by default — flip to face right
                if self.facing_right:
                    surf = pygame.transform.flip(surf, True, False)
                surf = pygame.transform.rotate(surf, rot_angle)
                if self.fire_effect == 'rainbow':
                    hue = (self.frame * 5) % 360
                    rc2, gc2, bc2 = colorsys.hsv_to_rgb(hue / 360, 0.95, 1.0)
                    surf = surf.copy()
                    ov = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
                    ov.fill((int(rc2*255), int(gc2*255), int(bc2*255), 110))
                    surf.blit(ov, (0, 0), special_flags=pygame.BLEND_ADD)
                elif self.fire_effect == 'fire':
                    surf = Bird._fire_stripe_overlay(surf, self.frame, 0, 55, stripe_h=20, alpha=160, scroll_speed=4)
                elif self.fire_effect == 'water':
                    surf = Bird._fire_stripe_overlay(surf, self.frame, 190, 230, stripe_h=24, alpha=140, scroll_speed=3, scroll_up=True)
                elif self.fire_effect == 'stars':
                    surf = Bird._fire_stripe_overlay(surf, self.frame, 270, 310, stripe_h=20, alpha=140, scroll_speed=2)
                elif self.fire_effect == 'leaves':
                    surf = Bird._fire_stripe_overlay(surf, self.frame, 90, 140, stripe_h=22, alpha=140, scroll_speed=2)
                elif self.fire_effect == 'gold':
                    surf = Bird._fire_stripe_overlay(surf, self.frame, 40, 60, stripe_h=20, alpha=155, scroll_speed=3)
                elif self.fire_effect == 'silver':
                    surf = Bird._fire_stripe_overlay(surf, self.frame, 200, 220, stripe_h=20, alpha=120, scroll_speed=2)
                r = surf.get_rect(center=(cx, cy))
                screen.blit(surf, r)
                # bubbles while underwater
                if self.state == 'underwater' and self.frame % 7 == 0:
                    bx = cx + random.randint(-14, 14)
                    by = cy - random.randint(5, 22)
                    pygame.draw.circle(screen, (180, 220, 255), (bx, by), 4, 1)
                # caught fish while rising
                if self.caught_fish and self.state == 'rising':
                    fx = cx + (30 if self.facing_right else -30)
                    fy = cy + 20
                    pygame.draw.ellipse(screen, self.caught_fish.color,
                                        (fx - 11, fy - 6, 22, 12))
            # ── skin particle effect overlay ────────────────────────
            fx_type = self.fire_effect  # '', 'fire', 'water', 'stars', 'leaves', 'gold', 'silver'
            if fx_type and self.state in ('flying', 'diving', 'rising'):
                # spawn rate: stars slower, gold/silver faster burst
                spawn_every = 4 if fx_type == 'stars' else 2
                if self.frame % spawn_every == 0:
                    if fx_type == 'fire':
                        for _ in range(3):
                            self._fire_particles.append([
                                cx + random.randint(-18, 18),
                                cy + random.randint(-8, 8),
                                random.uniform(-1.0, 1.0),
                                random.uniform(-2.5, -0.5),
                                random.randint(12, 22),
                                random.choice([(255,80,0),(255,160,0),(255,220,60),(255,40,0)])
                            ])
                    elif fx_type == 'water':
                        for _ in range(2):
                            self._fire_particles.append([
                                cx + random.randint(-20, 20),
                                cy + random.randint(-10, 10),
                                random.uniform(-0.6, 0.6),
                                random.uniform(-1.8, 0.3),
                                random.randint(10, 20),
                                random.choice([(60,140,255),(100,190,255),(180,230,255),(40,100,220)])
                            ])
                    elif fx_type == 'stars':
                        for _ in range(2):
                            self._fire_particles.append([
                                cx + random.randint(-28, 28),
                                cy + random.randint(-16, 16),
                                random.uniform(-1.4, 1.4),
                                random.uniform(-1.6, -0.1),
                                random.randint(14, 26),
                                random.choice([(200,140,255),(255,200,255),(180,80,255),(255,255,255)])
                            ])
                    elif fx_type == 'leaves':
                        for _ in range(2):
                            self._fire_particles.append([
                                cx + random.randint(-22, 22),
                                cy + random.randint(-10, 10),
                                random.uniform(-1.8, 1.8),
                                random.uniform(-0.3, 1.2),
                                random.randint(14, 28),
                                random.choice([(60,200,60),(80,230,60),(130,255,80),(40,160,40)])
                            ])
                    elif fx_type == 'gold':
                        for _ in range(3):
                            self._fire_particles.append([
                                cx + random.randint(-20, 20),
                                cy + random.randint(-12, 12),
                                random.uniform(-2.2, 2.2),
                                random.uniform(-2.2, 0.4),
                                random.randint(8, 18),
                                random.choice([(255,220,0),(255,200,50),(255,240,120),(255,170,0)])
                            ])
                    elif fx_type == 'silver':
                        for _ in range(3):
                            self._fire_particles.append([
                                cx + random.randint(-20, 20),
                                cy + random.randint(-12, 12),
                                random.uniform(-2.2, 2.2),
                                random.uniform(-2.2, 0.4),
                                random.randint(8, 18),
                                random.choice([(200,220,255),(220,235,255),(255,255,255),(160,200,240)])
                            ])
                    elif fx_type == 'rainbow':
                        # update trail (add current pos)
                        self._trail.append([cx, cy, (self.frame * 4) % 360])
                        if len(self._trail) > 35:
                            self._trail = self._trail[-35:]
                        # rainbow sparkles
                        for _ in range(2):
                            rh = random.randint(0, 359)
                            rc3, gc3, bc3 = colorsys.hsv_to_rgb(rh/360, 1.0, 1.0)
                            self._fire_particles.append([
                                cx + random.randint(-22, 22),
                                cy + random.randint(-12, 12),
                                random.uniform(-1.8, 1.8),
                                random.uniform(-1.8, 0.5),
                                random.randint(10, 20),
                                (int(rc3*255), int(gc3*255), int(bc3*255))
                            ])
                # update + draw all particles
                alive_p = []
                for p in self._fire_particles:
                    p[0] += p[2]; p[1] += p[3]; p[4] -= 1
                    if p[4] > 0:
                        alpha = max(0, min(255, int(p[4] * 11)))
                        r_size = max(1, p[4] // 4)
                        ps = pygame.Surface((r_size*2+2, r_size*2+2), pygame.SRCALPHA)
                        pygame.draw.circle(ps, p[5] + (alpha,), (r_size+1, r_size+1), r_size)
                        screen.blit(ps, (int(p[0])-r_size-1, int(p[1])-r_size-1))
                        alive_p.append(p)
                self._fire_particles = alive_p
            return
        cx  = int(self.x)
        cy  = int(self.y)
        env = self.wingspan

        ang = self.angle
        if self.state == 'diving':
            ang = math.pi / 2
        elif self.state == 'underwater':
            ang = math.pi / 2 * 0.6
        elif self.state == 'rising':
            ang = -math.pi / 4

        # mirror if facing left
        sign = 1 if self.facing_right else -1

        def rot(ox, oy):
            c, s = math.cos(ang), math.sin(ang)
            rx = ox * c - oy * s
            ry = ox * s + oy * c
            return int(cx + sign * rx), int(cy + ry)

        # ── body ─────────────────────────────────
        body_pts = []
        for i in range(14):
            a = 2 * math.pi * i / 14
            body_pts.append(rot(math.cos(a) * env * 0.38,
                                math.sin(a) * env * 0.19))
        pygame.draw.polygon(screen, self.body_color, body_pts)

        # ── wings ────────────────────────────────
        flap = math.sin(self.frame * 0.22) * env * 0.14 \
               if self.state == 'flying' else 0

        if self.state in ('diving', 'underwater'):
            # wings tucked
            wL = [rot(0, -env*0.08), rot(-env*0.55, -env*0.04),
                  rot(-env*0.42,  env*0.03)]
            wR = [rot(0, -env*0.08), rot( env*0.55, -env*0.04),
                  rot( env*0.42,  env*0.03)]
        else:
            wL = [rot(0,0), rot(-env*0.75, -env*0.22+flap), rot(-env*0.52,  env*0.06)]
            wR = [rot(0,0), rot( env*0.75, -env*0.22+flap), rot( env*0.52,  env*0.06)]

        pygame.draw.polygon(screen, self.wing_color, wL)
        pygame.draw.polygon(screen, self.wing_color, wR)

        # ── beak ─────────────────────────────────
        beak_w = env * 0.22 if self.beak_open > 0 else env * 0.16
        beak_h = env * 0.10 if self.beak_open > 0 else env * 0.05
        beak_pts = [rot( env*0.30, -env*0.05),
                    rot( env*0.58 + beak_w,  env*0.04),
                    rot( env*0.58 + beak_w, -env*0.12 - beak_h)]
        pygame.draw.polygon(screen, self.beak_color, beak_pts)

        # ── gular pouch (pelican only) ────────────
        if self.bird_type == 'pelican':
            pouch = [rot(env*0.28,  env*0.04),
                     rot(env*0.56,  env*0.04),
                     rot(env*0.53,  env*0.22),
                     rot(env*0.26,  env*0.17)]
            pygame.draw.polygon(screen, (215, 135, 25), pouch)

        # ── eye ──────────────────────────────────
        ex1, ey1 = rot(env * 0.21, -env * 0.07)
        eye_color = (240, 200, 40) if self.bird_type == 'osprey' else WHITE
        pygame.draw.circle(screen, eye_color, (ex1, ey1), max(3, env // 10))
        pygame.draw.circle(screen, BLACK,     (ex1, ey1), max(1, env // 18))

        # ── caught fish ──────────────────────────
        if self.caught_fish and self.state == 'rising':
            fx, fy = rot(env * 0.52, env * 0.16)
            pygame.draw.ellipse(screen, self.caught_fish.color,
                                (fx - 11, fy - 6, 22, 12))

        # ── underwater bubbles ────────────────────
        if self.state == 'underwater' and self.frame % 7 == 0:
            bx = int(self.x) + random.randint(-14, 14)
            by = int(self.y) - random.randint(5, 22)
            pygame.draw.circle(screen, (180, 220, 255), (bx, by), 4, 1)


# ═══════════════════════════════════════════════════════════════════════════
#  FISH BULLET  (shot by bird, damages puffer fish)
# ═══════════════════════════════════════════════════════════════════════════
class FishBullet:
    SPEED = 14.0

    def __init__(self, x, y, vx, vy, color=(80, 210, 255)):
        self.x      = float(x)
        self.y      = float(y)
        self.vx     = vx
        self.vy     = vy
        self.alive  = True
        self.frame  = 0
        self.life   = 90   # frames until it disappears
        self.radius = 10
        self.color  = color
        # trail color: lighter version
        r, g, b = color
        self.trail_color = (min(255, r+100), min(255, g+30), min(255, b+30))

    def update(self):
        self.x    += self.vx
        self.y    += self.vy
        self.frame += 1
        self.life  -= 1
        if (self.life <= 0
                or self.x < -30 or self.x > SCREEN_WIDTH + 30
                or self.y < -30 or self.y > SCREEN_HEIGHT + 30):
            self.alive = False

    def draw(self, screen):
        if not self.alive:
            return
        cx, cy = int(self.x), int(self.y)
        r      = self.radius
        flip   = self.vx >= 0
        # rotate body with direction
        angle  = math.atan2(self.vy, self.vx)
        cos_a, sin_a = math.cos(angle), math.sin(angle)

        def rotpt(ox, oy):
            return (cx + int(cos_a * ox - sin_a * oy),
                    cy + int(sin_a * ox + cos_a * oy))

        # fish body ellipse approximated as polygon
        body_pts = [rotpt(r, 0), rotpt(r * 0.6, -r // 2),
                    rotpt(-r, 0), rotpt(r * 0.6, r // 2)]
        pygame.draw.polygon(screen, self.color, body_pts)
        # tail
        tail_pts = [rotpt(-r, -r // 3), rotpt(-r - r // 2, 0), rotpt(-r, r // 3)]
        pygame.draw.polygon(screen, self.color, tail_pts)
        # eye
        ex, ey = rotpt(r // 3, -r // 6)
        pygame.draw.circle(screen, WHITE, (ex, ey), 3)
        pygame.draw.circle(screen, BLACK, (ex, ey), 1)
        # trail
        tx, ty = rotpt(-r * 2, 0)
        pygame.draw.line(screen, self.trail_color, (cx, cy), (tx, ty), 2)


# ═══════════════════════════════════════════════════════════════════════════
#  BULLET PICKUP  (glowing fish in the sky, gives +1 ammo when collected)
# ═══════════════════════════════════════════════════════════════════════════
class ShrimpPickup:
    def __init__(self, x=None, y=None):
        self.x     = float(x) if x is not None else float(random.randint(140, SCREEN_WIDTH - 140))
        self.y     = float(y) if y is not None else float(random.randint(90, WATER_Y - 70))
        self.alive = True
        self.frame = 0
        self.radius = 14

    def update(self):
        self.frame += 1

    def draw(self, screen):
        if not self.alive:
            return
        cx, cy = int(self.x), int(self.y)
        r = 10
        glow_r = 18 + int(math.sin(self.frame * 0.12) * 3)
        glow = pygame.Surface((glow_r * 2 + 4, glow_r * 2 + 4), pygame.SRCALPHA)
        alpha = int(50 + math.sin(self.frame * 0.12) * 24)
        pygame.draw.circle(glow, (255, 180, 100, alpha), (glow_r + 2, glow_r + 2), glow_r)
        screen.blit(glow, (cx - glow_r - 2, cy - glow_r - 2))
        body_pts = [(cx + r, cy), (cx + r // 2, cy - r), (cx - r // 2, cy - r // 2),
                    (cx - r, cy), (cx - r // 2, cy + r // 2), (cx + r // 2, cy + r)]
        pygame.draw.polygon(screen, (240, 120, 70), body_pts)
        pygame.draw.circle(screen, (255, 220, 200), (cx - 2, cy - 2), 2)
        pygame.draw.line(screen, (220, 90, 40), (cx - r, cy), (cx - r - 4, cy), 2)


class ShrimpBullet(FishBullet):
    def __init__(self, x, y, vx, vy, color=(240, 120, 70)):
        super().__init__(x, y, vx, vy, color=color)
        self.radius = 8
        self.life = 100

    def draw(self, screen):
        if not self.alive:
            return
        cx, cy = int(self.x), int(self.y)
        r = self.radius
        angle = math.atan2(self.vy, self.vx)
        cos_a, sin_a = math.cos(angle), math.sin(angle)

        def rotpt(ox, oy):
            return (cx + int(cos_a * ox - sin_a * oy),
                    cy + int(sin_a * ox + cos_a * oy))

        body_pts = [rotpt(r, 0), rotpt(r * 0.7, -r), rotpt(-r * 0.2, -r * 0.4),
                    rotpt(-r, 0), rotpt(-r * 0.2, r * 0.4), rotpt(r * 0.7, r)]
        pygame.draw.polygon(screen, self.color, body_pts)
        pygame.draw.circle(screen, (255, 220, 200), (cx, cy), max(2, r // 3))
        tail_pts = [rotpt(-r * 1.1, -r // 2), rotpt(-r * 1.4, 0), rotpt(-r * 1.1, r // 2)]
        pygame.draw.polygon(screen, (220, 90, 40), tail_pts)


class BulletPickup:
    def __init__(self):
        self.x     = float(random.randint(140, SCREEN_WIDTH - 140))
        self.y     = float(random.randint(90, WATER_Y - 70))
        self.alive = True
        self.frame = 0
        self.radius = 18

    def update(self):
        self.frame += 1

    def draw(self, screen):
        if not self.alive:
            return
        cx, cy = int(self.x), int(self.y)
        r = 12
        # glow
        glow_r = 22 + int(math.sin(self.frame * 0.09) * 4)
        glow_surf = pygame.Surface((glow_r * 2 + 4, glow_r * 2 + 4), pygame.SRCALPHA)
        alpha = int(55 + math.sin(self.frame * 0.09) * 35)
        pygame.draw.circle(glow_surf, (80, 220, 255, alpha),
                           (glow_r + 2, glow_r + 2), glow_r)
        screen.blit(glow_surf, (cx - glow_r - 2, cy - glow_r - 2))
        # fish body
        pygame.draw.ellipse(screen, (50, 200, 255), (cx - r, cy - r // 2, r * 2, r))
        pygame.draw.polygon(screen, (50, 200, 255),
                            [(cx + r, cy - r // 3), (cx + r + r // 2, cy),
                             (cx + r, cy + r // 3)])
        pygame.draw.circle(screen, WHITE, (cx - r // 3, cy - r // 6), 3)
        pygame.draw.circle(screen, BLACK, (cx - r // 3, cy - r // 6), 1)
        # label
        font_sm = pygame.font.Font(None, 20)
        lbl = font_sm.render("+1", True, (200, 255, 255))
        screen.blit(lbl, (cx - lbl.get_width() // 2, cy - r - 14))


# ═══════════════════════════════════════════════════════════════════════════
#  SHARK BOSS  (wave 10 – lurks underwater, leaps at birds)
# ═══════════════════════════════════════════════════════════════════════════
class SharkBoss:
    MAX_HP = 30

    def __init__(self):
        self.x              = float(SCREEN_WIDTH // 2)
        self.y              = float(WATER_Y + 160)
        self.base_y         = float(WATER_Y + 160)
        self.vx             = 2.5
        self.vy             = 0.0
        self.hp             = self.MAX_HP
        self.max_hp         = self.MAX_HP
        self.radius         = 55
        self.alive          = True
        self.frame          = 0
        self.hit_flash      = 0
        self.sting_cooldown = 0
        self.jump_timer     = 180
        self.jumping        = False

    def update(self):
        if not self.alive:
            return
        self.frame += 1
        if self.hit_flash      > 0: self.hit_flash      -= 1
        if self.sting_cooldown > 0: self.sting_cooldown -= 1

        # jump attack cycle
        self.jump_timer -= 1
        if self.jump_timer <= 0 and not self.jumping:
            self.jumping  = True
            self.vy       = -9.0

        if self.jumping:
            self.y += self.vy
            self.vy += 0.45   # gravity pulls back down
            if self.y >= self.base_y:
                self.y       = self.base_y
                self.vy      = 0.0
                self.jumping  = False
                self.jump_timer = random.randint(200, 340)
        else:
            # gentle bob at rest depth
            self.y = self.base_y + math.sin(self.frame * 0.04) * 8

        # horizontal swim
        self.x += self.vx
        if self.x < 120 or self.x > SCREEN_WIDTH - 120:
            self.vx *= -1
        self.x = max(120.0, min(SCREEN_WIDTH - 120.0, self.x))

    def draw(self, screen):
        if not self.alive:
            return
        cx, cy = int(self.x), int(self.y)
        f   = 1 if self.vx >= 0 else -1   # facing direction
        r   = self.radius
        flash   = self.hit_flash > 0
        body_col  = (255, 80,  80)  if flash else (90, 120, 155)
        belly_col = (255, 200, 200) if flash else (200, 220, 235)
        fin_col   = (70,  100, 135) if flash else (70, 100, 135)
        red_glow  = (255,  30,  30)

        # ── main body ────────────────────────────
        body_pts = []
        for i in range(24):
            a  = 2 * math.pi * i / 24
            bx = cx + f * int(math.cos(a) * r * 1.85)
            by = cy     + int(math.sin(a) * r * 0.55)
            body_pts.append((bx, by))
        pygame.draw.polygon(screen, body_col, body_pts)

        # ── belly ────────────────────────────────
        belly_pts = [(cx + f * int(math.cos(math.pi * i / 9) * r * 1.6),
                      cy + int(math.sin(math.pi * i / 9) * r * 0.32) + r // 5)
                     for i in range(10)]
        if len(belly_pts) >= 3:
            pygame.draw.polygon(screen, belly_col, belly_pts)

        # ── dorsal fin ───────────────────────────
        dor = [(cx + f * r // 2,     cy - r // 2),
               (cx + f * r // 4,     cy - r * 2 + 14),
               (cx + f * int(r*1.3), cy - r // 3)]
        pygame.draw.polygon(screen, fin_col, dor)

        # ── tail fin ─────────────────────────────
        tx = cx - f * int(r * 1.7)
        tail = [(tx, cy),
                (tx - f * r // 2, cy - r),
                (tx - f * r,      cy - r // 3),
                (tx - f * r // 2, cy + r),
                (tx - f * r,      cy + r // 3)]
        pygame.draw.polygon(screen, fin_col, tail)

        # ── pectoral fin ─────────────────────────
        pec = [(cx + f * r // 2, cy + r // 4),
               (cx - f * r // 4, cy + r),
               (cx + f * r,      cy + r // 2)]
        pygame.draw.polygon(screen, fin_col, pec)

        # ── open mouth & teeth ───────────────────
        mx_tip = cx + f * int(r * 1.75)
        jaw_top = [(mx_tip, cy - r // 5),
                   (mx_tip + f * 18, cy - r // 4),
                   (mx_tip + f * 18, cy),
                   (mx_tip, cy + r // 5)]
        pygame.draw.polygon(screen, (180, 25, 25), jaw_top)
        for i in range(5):
            tx2 = mx_tip + f * 2
            ty  = cy - r // 6 + i * (r // 9)
            pygame.draw.polygon(screen, (240, 240, 240),
                                [(tx2, ty),
                                 (tx2 + f * 9,  ty + 3),
                                 (tx2 + f * 9,  ty - 3)])

        # ── red glowing eye ───────────────────────
        ex = cx + f * int(r * 0.8)
        ey = cy - r // 5
        glow = pygame.Surface((52, 52), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 0, 0, 90), (26, 26), 24)
        screen.blit(glow, (ex - 26, ey - 26))
        pygame.draw.circle(screen, (120, 0, 0), (ex, ey), 13)
        pygame.draw.circle(screen, red_glow,    (ex, ey), 10)
        pygame.draw.circle(screen, (255, 120, 0),(ex, ey),  6)
        pygame.draw.circle(screen, BLACK,        (ex, ey),  3)

        # ── boss label & HP bar ──────────────────
        bar_w, bar_h = 100, 12
        bar_x = cx - bar_w // 2
        bar_y = cy - r * 2 - 36
        font2 = pygame.font.Font(None, 22)
        lbl   = font2.render("\u2605 JEFE: TIBUR\u00d3N \u2605", True, (255, 80, 0))
        screen.blit(lbl, (cx - lbl.get_width() // 2, bar_y - 20))
        pygame.draw.rect(screen, (40, 0, 0),   (bar_x - 2, bar_y - 2, bar_w + 4, bar_h + 4), border_radius=4)
        pygame.draw.rect(screen, (60, 0, 0),   (bar_x, bar_y, bar_w, bar_h), border_radius=3)
        fill = int(bar_w * self.hp / self.max_hp)
        if fill > 0:
            hp_col = (220, 30, 30) if self.hp <= self.max_hp // 3 else (220, 120, 30) if self.hp <= self.max_hp * 2 // 3 else (30, 200, 80)
            pygame.draw.rect(screen, hp_col, (bar_x, bar_y, fill, bar_h), border_radius=3)
        pygame.draw.rect(screen, (200, 50, 50), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=3)
        hp_txt = font2.render(f"{self.hp}/{self.max_hp}", True, WHITE)
        screen.blit(hp_txt, (cx - hp_txt.get_width() // 2, bar_y + bar_h + 3))


# ═══════════════════════════════════════════════════════════════════════════
#  OCTOPUS BOSS  (wave 25 – deep sea boss with waving tentacles)
# ═══════════════════════════════════════════════════════════════════════════
class OctopusBoss:
    MAX_HP = 60
    # tentacle anchor angles (0=right, going counter-clockwise from bottom)
    _TENT_ANGLES = [math.pi * 0.55 + math.pi * i / 5 for i in range(8)]

    def __init__(self):
        self.x              = float(SCREEN_WIDTH // 2)
        self.y              = float(WATER_Y + 200)
        self.base_y         = float(WATER_Y + 200)
        self.vx             = 1.8
        self.hp             = self.MAX_HP
        self.max_hp         = self.MAX_HP
        self.radius         = 52
        self.alive          = True
        self.frame          = 0
        self.hit_flash      = 0
        self.sting_cooldown = 0
        self.lunge_timer    = 240
        self.lunging        = False
        self.lunge_vy       = 0.0

    def update(self):
        if not self.alive:
            return
        self.frame += 1
        if self.hit_flash      > 0: self.hit_flash      -= 1
        if self.sting_cooldown > 0: self.sting_cooldown -= 1

        # lunge upward periodically
        self.lunge_timer -= 1
        if self.lunge_timer <= 0 and not self.lunging:
            self.lunging  = True
            self.lunge_vy = -6.0

        if self.lunging:
            self.y     += self.lunge_vy
            self.lunge_vy += 0.35
            if self.y >= self.base_y:
                self.y       = self.base_y
                self.lunge_vy = 0.0
                self.lunging  = False
                self.lunge_timer = random.randint(260, 400)
        else:
            self.y = self.base_y + math.sin(self.frame * 0.035) * 10

        # horizontal drift
        self.x += self.vx
        if self.x < 130 or self.x > SCREEN_WIDTH - 130:
            self.vx *= -1
        self.x = max(130.0, min(SCREEN_WIDTH - 130.0, self.x))

    def draw(self, screen):
        if not self.alive:
            return
        cx, cy = int(self.x), int(self.y)
        r      = self.radius
        flash  = self.hit_flash > 0
        body_col  = (255,  80,  80) if flash else ( 90,  30, 140)
        mid_col   = (255, 140, 140) if flash else (120,  50, 180)
        tent_col  = (255,  60,  60) if flash else ( 75,  25, 120)
        red_glow  = (255,  30,  30)

        # ── tentacles (drawn behind body) ────────
        tent_len = int(r * 2.0)
        for i, base_angle in enumerate(self._TENT_ANGLES):
            phase = self.frame * 0.08 + i * 0.8
            # 3-segment tentacle
            px, py = cx, cy
            seg_len = tent_len // 3
            for seg in range(3):
                wave = math.sin(phase + seg * 1.2) * (14 + seg * 6)
                nx = px + int(math.cos(base_angle + wave * 0.04) * seg_len)
                ny = py + int(math.sin(base_angle) * seg_len + wave)
                width = max(1, 7 - seg * 2)
                pygame.draw.line(screen, tent_col, (px, py), (nx, ny), width)
                # sucker spots
                mx2 = (px + nx) // 2
                my2 = (py + ny) // 2
                pygame.draw.circle(screen, (140, 60, 200), (mx2, my2), max(1, 4 - seg))
                px, py = nx, ny

        # ── body (rounded polygon) ────────────────
        body_pts = []
        for i in range(20):
            a  = 2 * math.pi * i / 20
            bx = cx + int(math.cos(a) * r)
            by = cy + int(math.sin(a) * r * 0.75)
            body_pts.append((bx, by))
        pygame.draw.polygon(screen, body_col, body_pts)

        # ── mantle (dome on top) ──────────────────
        mantle_pts = []
        for i in range(12):
            a  = math.pi + math.pi * i / 11
            bx = cx + int(math.cos(a) * r * 0.92)
            by = cy + int(math.sin(a) * r * 1.25)
            mantle_pts.append((bx, by))
        if len(mantle_pts) >= 3:
            pygame.draw.polygon(screen, mid_col, mantle_pts)

        # ── red glowing eyes ──────────────────────
        for side in (-1, 1):
            ex = cx + side * r // 3
            ey = cy - r // 5
            glow = pygame.Surface((52, 52), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 0, 0, 90), (26, 26), 24)
            screen.blit(glow, (ex - 26, ey - 26))
            pygame.draw.circle(screen, (130, 0, 0), (ex, ey), 13)
            pygame.draw.circle(screen, red_glow,    (ex, ey), 10)
            pygame.draw.circle(screen, (255, 130, 0),(ex, ey),  6)
            pygame.draw.circle(screen, BLACK,        (ex, ey),  3)

        # ── boss label & HP bar ───────────────────
        bar_w, bar_h = 110, 12
        bar_x = cx - bar_w // 2
        bar_y = cy - r * 2 - 36
        font2 = pygame.font.Font(None, 22)
        lbl   = font2.render("\u2605 JEFE: PULPO \u2605", True, (200, 80, 255))
        screen.blit(lbl, (cx - lbl.get_width() // 2, bar_y - 20))
        pygame.draw.rect(screen, (30, 0, 50),  (bar_x - 2, bar_y - 2, bar_w + 4, bar_h + 4), border_radius=4)
        pygame.draw.rect(screen, (50, 0, 80),  (bar_x, bar_y, bar_w, bar_h), border_radius=3)
        fill = int(bar_w * self.hp / self.max_hp)
        if fill > 0:
            hp_col = (220, 30, 30) if self.hp <= self.max_hp // 3 else (180, 60, 220) if self.hp <= self.max_hp * 2 // 3 else (130, 30, 220)
            pygame.draw.rect(screen, hp_col, (bar_x, bar_y, fill, bar_h), border_radius=3)
        pygame.draw.rect(screen, (180, 50, 220), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=3)
        hp_txt = font2.render(f"{self.hp}/{self.max_hp}", True, WHITE)
        screen.blit(hp_txt, (cx - hp_txt.get_width() // 2, bar_y + bar_h + 3))


# ═══════════════════════════════════════════════════════════════════════════
#  GAME CLASS
# ═══════════════════════════════════════════════════════════════════════════
class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
        pygame.display.set_caption("Wings & Fish")
        self.clock = pygame.time.Clock()
        self.font       = pygame.font.Font(None, 36)
        self.font_sm    = pygame.font.Font(None, 24)
        self.font_lg    = pygame.font.Font(None, 80)
        self.font_title  = pygame.font.Font(None, 52)
        self.font_menu_title = pygame.font.Font(None, 110)
        self.font_menu_sub   = pygame.font.Font(None, 44)
        self.font_menu_btn   = pygame.font.Font(None, 30)
        self.font_menu_badge = pygame.font.Font(None, 22)

        self.state = GameState.START
        self.game_mode = 'free'
        self.mode_select_return_state = GameState.START

        # ── optional background image ────────────
        self.bg_image = None
        try:
            img = pygame.image.load('background.png')
            self.bg_image = pygame.transform.scale(
                img.convert(), (SCREEN_WIDTH, SCREEN_HEIGHT))
            print("background.png loaded")
        except Exception as e:
            print(f"No background.png: {e}")

        # ── shop images ──────────────────────────
        self.shop_image_alive = None
        self.shop_image_dead = None
        try:
            self.shop_image_alive = pygame.image.load('images/shop.png').convert_alpha()
            print(f"✓ shop.png loaded: {type(self.shop_image_alive)}")
        except Exception as e:
            print(f"✗ Error loading shop.png: {e}")
        try:
            self.shop_image_dead = pygame.image.load('images/shop after.png').convert_alpha()
            print(f"✓ shop after.png loaded: {type(self.shop_image_dead)}")
        except Exception as e:
            print(f"✗ Error loading shop after.png: {e}")

        # ── birds ────────────────────────────────
        self.pelican     = Bird('pelican', 260, 260)
        self.osprey      = Bird('osprey',  720, 190)
        self.active_bird = self.pelican

        # ── fish ─────────────────────────────────
        self.fish_list = _make_fish_pool(STARTING_FISH_COUNT, luck=0)

        # ── upgrades / shop ──────────────────────
        self.upgrades = {'depth': 0, 'capacity': 0, 'luck': 0, 'damage': 0, 'recovery': 0}
        self.upgrade_costs = {
            'depth':    [5, 10, 20, 35, 55],
            'capacity': [6, 12, 24, 40, 65],
            'luck':     [8, 16, 30, 50, 80],
            'damage':   [10, 20, 35, 60, 90],
            'recovery': [12, 25, 45, 70, 100],
        }
        self.max_upgrade    = 3                      # unlocked to 5 after rebirth
        self.bullet_damage  = 1                      # updated by _apply_upgrades
        # shop button rects (positioned in _draw methods)
        self.btn_close_shop = pygame.Rect(0, 0, 40, 40)
        self.shop_btns      = [pygame.Rect(0, 0, 180, 50) for _ in range(5)]
        self.btn_rebirth    = pygame.Rect(0, 0, 1, 1)

        # ── rebirth / lifetime stats ──────────────────
        self.rebirth_count       = 0
        self.crabs_caught_total  = 0
        self.golden_caught_total = 0
        self.normal_fish_caught  = 0

        # ── crabs ────────────────────────────────
        self.crab_list = [Crab() for _ in range(5)]

        # ── pufferfish (obstacles) ────────────────
        self.puffer_list = []
        self.caught_count     = 0
        self.fishes_in_dive   = 0     # peces atrapados en esta inmersión
        self.wave             = 1
        self.campaign_level   = 1
        self.unlocked_level   = 1
        self.completed_level  = 0
        self._level_progress_path = os.path.expanduser('~/.wings_and_fish_progress.json')
        self._load_level_progress()
        self.fish_this_wave   = 0     # fish caught this wave (counts toward wave_target)
        self.wave_target      = 8     # fish needed to complete the wave
        self.wave_clear_timer = 0     # >0: wave banner showing; 0 → advance wave
        self.stamina      = 100.0
        self.max_stamina  = 100.0
        self._stamina_drain = 100.0 / (STAMINA_DRAIN_SECONDS * FPS)

        self.guide_messages = []
        self._add_message("Chris: Press Play to begin the game.")

        # ── combo & score feedback ─────────────────────
        self.combo = 0
        self.combo_timer = 0
        self.last_combo_gain = 0

        # ── bullets & pickups ─────────────────────
        self.bullets             = []
        self.bullet_pickups      = []
        self.shrimp_pickups      = []
        self.shrimp_charge       = 0
        self._rainbow_hue        = 0   # cycles for rainbow bullet colors
        self._pickup_spawn_timer = 300   # frames until next ammo pickup spawns

        # ── boss ─────────────────────────────────
        self.boss = None   # SharkBoss or OctopusBoss instance when active

        # ── floating +1 labels ───────────────────
        self.floaters = []

        # ── input ────────────────────────────────
        self.keys = {
            pygame.K_UP:    False,
            pygame.K_DOWN:  False,
            pygame.K_LEFT:  False,
            pygame.K_RIGHT: False,
            pygame.K_w:     False,
            pygame.K_a:     False,
            pygame.K_s:     False,
            pygame.K_d:     False,
        }

        # ── HUD rects ────────────────────────────
        self.btn_play           = pygame.Rect(SCREEN_WIDTH - 200, 18, 178, 58)
        selector_w = min(980, SCREEN_WIDTH - 48)
        selector_h = min(620, SCREEN_HEIGHT - 48)
        selector_x = (SCREEN_WIDTH - selector_w) // 2
        selector_y = (SCREEN_HEIGHT - selector_h) // 2
        card_w = (selector_w - 72) // 2
        card_y = selector_y + 100
        card_h = selector_h - 180
        self.mode_select_panel = pygame.Rect(selector_x, selector_y, selector_w, selector_h)
        self.btn_mode_free = pygame.Rect(selector_x + 24, card_y, card_w, card_h)
        self.btn_mode_levels = pygame.Rect(selector_x + 48 + card_w, card_y, card_w, card_h)
        self.btn_mode_back = pygame.Rect(selector_x + selector_w // 2 - 64,
                         selector_y + selector_h - 54, 128, 38)
        self.btn_tutorial_continue = pygame.Rect(selector_x + selector_w // 2 - 180,
                                                  selector_y + selector_h - 82, 170, 48)
        self.btn_tutorial_skip = pygame.Rect(selector_x + selector_w // 2 + 10,
                                              selector_y + selector_h - 82, 170, 48)
        self.btn_levels_back = pygame.Rect(selector_x + selector_w // 2 - 64,
                                           selector_y + selector_h - 54, 128, 38)
        self.btn_level_continue = self.btn_levels_back.copy()
        self.level_button_rects = {}
        tile_w, tile_h, tile_gap = 120, 68, 16
        grid_w = tile_w * 5 + tile_gap * 4
        grid_x = selector_x + (selector_w - grid_w) // 2
        grid_y = selector_y + 142
        for level in range(1, CAMPAIGN_LEVEL_COUNT + 1):
            row, col = divmod(level - 1, 5)
            self.level_button_rects[level] = pygame.Rect(
                grid_x + col * (tile_w + tile_gap),
                grid_y + row * (tile_h + tile_gap),
                tile_w, tile_h)
        self.btn_pelican        = pygame.Rect(18,  SCREEN_HEIGHT - 132, 110, 110)
        self.btn_osprey         = pygame.Rect(SCREEN_WIDTH - 128, SCREEN_HEIGHT - 132, 110, 110)
        self.btn_gear           = pygame.Rect(SCREEN_WIDTH - 58, 10, 48, 48)   # right gear
        self.btn_shop           = pygame.Rect(SCREEN_WIDTH - 110, 10, 48, 48)  # shop button
        self.btn_item_store     = pygame.Rect(SCREEN_WIDTH - 162, 10, 48, 48)  # tienda consumibles
        self.item_store_btns    = [pygame.Rect(0, 0, 160, 44) for _ in range(5)]
        self.btn_close_item_store = pygame.Rect(0, 0, 40, 40)
        # ── purchase form ─────────────────────────
        self.gems                    = 0
        self._pf_fields              = {'Nombre': '', 'Cédula': '', 'Celular': '', 'Dirección': '', 'Correo': ''}
        self._pf_active              = None
        self._pf_records             = []
        self._pf_field_rects         = {}
        self._pf_pending_cost        = 0
        self.btn_pf_ingresar         = pygame.Rect(0, 0, 130, 34)
        self.btn_pf_modificar        = pygame.Rect(0, 0, 130, 34)
        self.btn_close_purchase_form = pygame.Rect(0, 0, 40, 40)
        self.btn_gear_left      = pygame.Rect(SCREEN_WIDTH - 58, 10, 48, 48)  # right gear (settings)
        self.prev_state         = GameState.FLYING   # state to restore when closing settings
        self.btn_close_settings = pygame.Rect(SCREEN_WIDTH//2 + 210, SCREEN_HEIGHT//2 - 220, 40, 40)

        # ── game-over buttons ────────────────────
        cx = SCREEN_WIDTH // 2
        self.btn_retry     = pygame.Rect(cx - 185, 420, 175, 58)
        self.btn_restart   = pygame.Rect(cx + 10,  420, 175, 58)
        self.btn_quit_game = pygame.Rect(cx - 87,  498, 175, 58)

        # ── animated clouds ──────────────────────
        self.clouds = [(random.randint(0, SCREEN_WIDTH),
                        random.randint(30, 120),
                        random.randint(25, 55),
                        random.uniform(0.2, 0.6),
                        random.uniform(0, math.pi * 2),
                        random.uniform(1.0, 3.5))
                       for _ in range(6)]

        # ── MENU: autonomous demo birds ───────────
        self._demo_p = {'x': 200.0, 'y': 200.0, 'vx': 2.5, 'vy': 0.4,
                        'state': 'flying', 'dive_t': 0, 'frame': 0,
                        'facing_right': True}
        self._demo_o = {'x': 750.0, 'y': 160.0, 'vx': -2.0, 'vy': 0.2,
                        'state': 'flying', 'dive_t': 0, 'frame': 0,
                        'facing_right': False}
        self._demo_fish = _make_fish_pool(10, luck=0)

        # ── SKINS ────────────────────────────────
        # Tuple: (display_name, body_color, wing_color, beak_color,
        #         luck_bonus, fish_bonus, damage_bonus_pct, stamina_bonus_pct, effect, cost)
        # effect: '' | 'fire' | 'water' | 'stars' | 'leaves' | 'gold' | 'silver' | 'rainbow'
        # cost: fish coins (>= 0) or -5 = costs $5 USD via purchase form
        self.pelican_skins = [
            ('Clasico',  (235, 225, 200), (80,  52,  28),  (145, 140, 135), 0,    0, 0.00, 0.00, '',        0),
            ('Marino',   (180, 210, 230), (30,  80,  140), (100, 120, 150), 0.10, 1, 0.10, 0.10, 'water',  10),
            ('Fuego',    (255, 180, 80),  (200, 50,  10),  (255, 120, 20),  0.25, 2, 0.25, 0.25, 'fire',   25),
            ('Noche',    (50,  50,  70),  (20,  20,  40),  (80,  80,  110), 0.50, 3, 0.50, 0.50, 'stars',  50),
            ('Selva',    (120, 200, 100), (40,  110, 40),  (160, 200, 60),  1.00, 5, 1.00, 1.00, 'leaves', 80),
            ('Dorado',   (255, 230, 120), (200, 160, 20),  (255, 200, 50),  2.00, 8, 2.00, 2.00, 'gold',   150),
            ('Arcoiris', (255, 180, 255), (100, 200, 255), (255, 255, 100), 3.00,10, 3.00, 3.00, 'rainbow',-5),
            ('Arrecife', (255, 155, 140), (150, 45, 70),   (255, 220, 150), 0.15, 1, 0.15, 0.15, 'water', 180),
            ('Aurora',   (165, 235, 220), (25, 100, 120),  (255, 210, 100), 0.20, 2, 0.20, 0.20, 'silver',220),
        ]
        self.osprey_skins = [
            ('Clasico',  (230, 225, 215), (72,  50,  25),  (38,  32,  28),  0,    0, 0.00, 0.00, '',        0),
            ('Artico',   (220, 235, 255), (100, 120, 160), (60,  70,  90),  0.10, 1, 0.10, 0.10, 'water',  10),
            ('Volcán',   (255, 140, 60),  (160, 40,  10),  (200, 80,  20),  0.25, 2, 0.25, 0.25, 'fire',   25),
            ('Sombra',   (60,  60,  80),  (25,  25,  45),  (90,  90,  120), 0.50, 3, 0.50, 0.50, 'stars',  50),
            ('Bosque',   (100, 170, 80),  (35,  90,  35),  (130, 180, 50),  1.00, 5, 1.00, 1.00, 'leaves', 80),
            ('Platino',  (210, 220, 230), (130, 145, 165), (145, 155, 170), 2.00, 8, 2.00, 2.00, 'silver', 150),
            ('Arcoiris', (255, 180, 255), (100, 200, 255), (255, 255, 100), 3.00,10, 3.00, 3.00, 'rainbow',-5),
            ('Marea',    (100, 210, 235), (20, 85, 130),   (255, 185, 90),  0.15, 1, 0.15, 0.15, 'water', 180),
            ('Volcan',   (255, 175, 110), (125, 45, 30),   (45, 35, 30),    0.20, 2, 0.20, 0.20, 'fire',  220),
        ]
        self.pelican_skin_idx = 0
        self.osprey_skin_idx  = 0
        # skins already purchased (index 0 free by default)
        self.unlocked_pelican = {0}
        self.unlocked_osprey  = {0}
        self._pf_purchase_type = 'gems'   # 'gems' | 'rainbow_pelican'
        # skin bonus multipliers (set by _apply_skin)
        self.skin_luck_bonus    = 0.0
        self.skin_fish_bonus    = 0
        self.skin_damage_bonus  = 0.0
        self.skin_stamina_bonus = 0.0
        self._apply_skin()

        # menu button rects (laid out at bottom of screen)
        bw, bh = 160, 56
        gap    = 20
        total  = 4 * bw + 3 * gap
        bx0    = (SCREEN_WIDTH - total) // 2
        by     = SCREEN_HEIGHT - bh - 28
        self.btn_menu_play  = pygame.Rect(bx0,                    by, bw, bh)
        self.btn_menu_shop  = pygame.Rect(bx0 + (bw + gap),      by, bw, bh)
        self.btn_menu_store = pygame.Rect(bx0 + 2 * (bw + gap),  by, bw, bh)
        self.btn_menu_skins = pygame.Rect(bx0 + 3 * (bw + gap),  by, bw, bh)
        self.btn_close_skins = pygame.Rect(0, 0, 40, 40)
        self.skins_tab       = 'pelican'   # 'pelican' or 'osprey'
        self.btn_skins_tab_p = pygame.Rect(0, 0, 140, 36)
        self.btn_skins_tab_o = pygame.Rect(0, 0, 140, 36)
        self._skin_card_rects = []

    # ── skin helpers ─────────────────────────────
    def _apply_skin(self):
        """Push selected skin colors + bonuses into the actual bird objects."""
        sk = self.pelican_skins[self.pelican_skin_idx]
        self.pelican.body_color   = sk[1]
        self.pelican.wing_color   = sk[2]
        self.pelican.beak_color   = sk[3]
        self.pelican.fire_effect  = sk[8]
        sk2 = self.osprey_skins[self.osprey_skin_idx]
        self.osprey.body_color    = sk2[1]
        self.osprey.wing_color    = sk2[2]
        self.osprey.beak_color    = sk2[3]
        self.osprey.fire_effect   = sk2[8]
        # Use the BEST bonus between the two active skins
        self.skin_luck_bonus    = max(sk[4],  sk2[4])
        self.skin_fish_bonus    = max(sk[5],  sk2[5])
        self.skin_damage_bonus  = max(sk[6],  sk2[6])
        self.skin_stamina_bonus = max(sk[7],  sk2[7])
        self._apply_upgrades()

    def _apply_upgrades(self):
        """Apply current upgrade levels to birds and stamina stats."""
        base = Bird.CONFIGS
        depth_bonus = self.upgrades.get('depth', 0) * 70
        capacity_bonus = self.upgrades.get('capacity', 0) * 15
        self.pelican.max_depth = base['pelican']['max_depth'] + depth_bonus
        self.pelican.capture_radius = base['pelican']['capture_radius'] + capacity_bonus
        self.osprey.max_depth = base['osprey']['max_depth'] + int(depth_bonus * 0.7)
        self.osprey.capture_radius = base['osprey']['capture_radius'] + capacity_bonus

        recovery_bonus = self.upgrades.get('recovery', 0) * 20.0
        base_stamina = 100.0 * (1.0 + getattr(self, 'skin_stamina_bonus', 0.0))
        self.max_stamina = base_stamina + recovery_bonus
        if hasattr(self, 'stamina'):
            self.stamina = min(self.stamina, self.max_stamina)

        dmg_level = self.upgrades.get('damage', 0)
        max_upgrade = getattr(self, 'max_upgrade', 3)
        if dmg_level >= max_upgrade and max_upgrade <= 3:
            self.bullet_damage = 999
        elif dmg_level >= 5:
            self.bullet_damage = 999
        else:
            self.bullet_damage = 1 + dmg_level * 3
        self.bullet_damage = max(1, int(self.bullet_damage * (1.0 + getattr(self, 'skin_damage_bonus', 0.0))))

    # ── bullet color based on active bird skin effect ────
    def _bullet_color(self, bird):
        """Return (r, g, b) for the bullet based on the firing bird's skin effect."""
        fx = bird.fire_effect
        _skin_bullet_colors = {
            '':       (80,  210, 255),
            'fire':   (255, 120,  20),
            'water':  ( 60, 160, 255),
            'stars':  (200, 100, 255),
            'leaves': ( 80, 220,  60),
            'gold':   (255, 210,   0),
            'silver': (200, 230, 255),
        }
        if fx == 'rainbow':
            self._rainbow_hue = (self._rainbow_hue + 25) % 360
            r, g, b = colorsys.hsv_to_rgb(self._rainbow_hue / 360, 1.0, 1.0)
            return (int(r * 255), int(g * 255), int(b * 255))
        return _skin_bullet_colors.get(fx, (80, 210, 255))

    # ── demo-bird AI tick ────────────────────────
    def _update_demo_birds(self):
        for db, pool_y_min, pool_x_range in [
                (self._demo_p, 230, (80, SCREEN_WIDTH - 80)),
                (self._demo_o, 170, (80, SCREEN_WIDTH - 80))
        ]:
            db['frame'] += 1
            db['dive_t'] -= 1

            if db['state'] == 'flying':
                # gentle wandering
                db['x'] += db['vx']
                db['y'] += db['vy']
                db['vy'] += 0.04
                if db['y'] > WATER_Y - 20:
                    db['vy'] = -1.5
                if db['y'] < 40:
                    db['vy'] = 1.0
                if db['x'] < 60 or db['x'] > SCREEN_WIDTH - 60:
                    db['vx'] *= -1
                    db['facing_right'] = db['vx'] > 0
                # random dive
                if db['dive_t'] <= 0 and db['y'] < WATER_Y - 60:
                    db['state'] = 'diving'
                    db['vy']    = 9.0
                    db['dive_t'] = random.randint(180, 360)

            elif db['state'] == 'diving':
                db['y'] += db['vy']
                db['x'] += db['vx'] * 0.2
                if db['y'] >= WATER_Y + 40:
                    db['state'] = 'underwater'
                    db['vy']    = 4.0

            elif db['state'] == 'underwater':
                db['y'] += db['vy']
                db['vy'] *= 0.982
                db['x'] += db['vx'] * 0.15
                # catch demo fish
                for f in self._demo_fish:
                    if not f.alive:
                        continue
                    if math.hypot(db['x'] - f.x, db['y'] - f.y) < 44:
                        f.alive = False
                        self._demo_fish.append(_spawn_fish(0))
                if db['vy'] < 0.3 or db['y'] > SCREEN_HEIGHT - 40:
                    db['state'] = 'rising'
                    db['vy']    = -5.0

            elif db['state'] == 'rising':
                db['y'] += db['vy']
                db['vy'] += 0.18
                if db['y'] < WATER_Y - 20:
                    db['state'] = 'flying'
                    db['vy'] = -1.5

            db['x'] = max(40.0, min(float(SCREEN_WIDTH - 40), db['x']))
            db['y'] = max(30.0, min(float(SCREEN_HEIGHT - 20), db['y']))

        # keep demo fish pool alive
        self._demo_fish = [f for f in self._demo_fish if f.alive] or _make_fish_pool(8, luck=0)
        for f in self._demo_fish:
            f.update()

    # ── helpers ──────────────────────────────────
    def _add_message(self, text, duration=260):
        self.guide_messages = [(text, duration)]

    def _get_combo_multiplier(self):
        if self.combo >= 10:
            return 3
        if self.combo >= 4:
            return 2
        return 1

    def _get_bonus_reward(self, base_amount):
        return int(base_amount * self._get_combo_multiplier())

    def _register_combo_gain(self, amount=1):
        self.combo += amount
        self.combo_timer = 180
        self.last_combo_gain = self.combo
        if self.combo % 4 == 0:
            self._add_message(f"¡COMBO x{self._get_combo_multiplier()}! Mantén la racha.")

    def _reset_combo_if_expired(self):
        if self.combo_timer > 0:
            self.combo_timer -= 1
        if self.combo_timer <= 0 and self.combo > 0:
            self.combo = 0
            self.last_combo_gain = 0

    def _add_floater(self, x, y, txt="+1"):
        self.floaters.append({'x': float(x), 'y': float(y), 't': 90, 'txt': txt})

    # ── main loop ────────────────────────────────
    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()

    # ═══════════════════════════════════════════
    #  EVENTS
    # ═══════════════════════════════════════════
    def handle_events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return False

            if ev.type == pygame.KEYDOWN:
                if ev.key in self.keys:
                    self.keys[ev.key] = True

                # ESC closes all overlays
                if ev.key == pygame.K_ESCAPE:
                    if self.state in (GameState.SETTINGS, GameState.SHOP, GameState.ITEM_STORE):
                        self.state = self.prev_state
                    elif self.state == GameState.PURCHASE_FORM:
                        self.state = GameState.ITEM_STORE
                    elif self.state == GameState.SKINS:
                        self.state = GameState.MENU
                    elif self.state == GameState.START:
                        self.state = GameState.MENU
                    elif self.state == GameState.MODE_SELECT:
                        self.state = self.mode_select_return_state
                    elif self.state == GameState.TUTORIAL:
                        self.state = GameState.START
                    elif self.state == GameState.LEVEL_SELECT:
                        self.state = GameState.MODE_SELECT
                    elif self.state == GameState.LEVEL_COMPLETE:
                        self.state = GameState.LEVEL_SELECT
                    else:
                        self.state = GameState.MENU

                # TAB opens/closes skins store
                if ev.key == pygame.K_TAB:
                    if self.state == GameState.SKINS:
                        self.state = GameState.MENU
                    elif self.state == GameState.MENU:
                        self.state = GameState.SKINS
                    elif self.state in (GameState.FLYING, GameState.DIVING, GameState.UNDERWATER, GameState.RISING, GameState.START):
                        self.prev_state = self.state
                        self.state = GameState.SKINS

                # typing in purchase form fields
                if self.state == GameState.PURCHASE_FORM and self._pf_active is not None:
                    _fo = ['Nombre', 'Cédula', 'Celular', 'Dirección', 'Correo']
                    if ev.key == pygame.K_BACKSPACE:
                        self._pf_fields[self._pf_active] = self._pf_fields[self._pf_active][:-1]
                    elif ev.key in (pygame.K_RETURN, pygame.K_TAB):
                        idx = _fo.index(self._pf_active)
                        self._pf_active = _fo[(idx + 1) % len(_fo)]
                    elif ev.unicode and ev.unicode.isprintable():
                        if len(self._pf_fields[self._pf_active]) < 40:
                            self._pf_fields[self._pf_active] += ev.unicode

                if self.state in (GameState.SETTINGS, GameState.SHOP, GameState.ITEM_STORE,
                                  GameState.PURCHASE_FORM, GameState.SKINS, GameState.MENU,
                                  GameState.MODE_SELECT, GameState.TUTORIAL,
                                  GameState.LEVEL_SELECT, GameState.LEVEL_COMPLETE):
                    continue

                if ev.key == pygame.K_SPACE:
                    self._dive(self.active_bird)

                if ev.key == pygame.K_z:
                    self.active_bird = self.pelican
                    self._dive(self.pelican)
                    self._add_message("Martin: Pelican dives for big fish!")

                if ev.key == pygame.K_x:
                    self.active_bird = self.osprey
                    self._dive(self.osprey)
                    self._add_message("Martin: Osprey dives with precision!")

                if ev.key == pygame.K_q:
                    self._pelican_burst()

                if ev.key == pygame.K_e:
                    self._osprey_drill()

                if ev.key == pygame.K_1:
                    self.active_bird = self.pelican
                    self._add_message("Pelícano seleccionado")

                if ev.key == pygame.K_2:
                    self.active_bird = self.osprey
                    self._add_message("Ave pescadora seleccionada")

            if ev.type == pygame.KEYUP:
                if ev.key in self.keys:
                    self.keys[ev.key] = False

            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 3:
                # Right-click → pelican shoots fish bullets, osprey does peck dive
                if self.state == GameState.FLYING:
                    if self.active_bird is self.pelican:
                        self._shoot(self.pelican)
                    else:
                        self._osprey_peck()

            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = pygame.mouse.get_pos()

                # ── GAME OVER screen ─────────────────────
                if self.state == GameState.GAME_OVER:
                    if self.btn_retry.collidepoint(mx, my):
                        self._start_game()
                        self.stamina = self.max_stamina
                    elif self.btn_restart.collidepoint(mx, my):
                        self.caught_count = 0
                        self.fish_list = _make_fish_pool(STARTING_FISH_COUNT, luck=self.upgrades['luck'])
                        self._start_game(reset_wave=True)
                        self.stamina = self.max_stamina
                    elif self.btn_quit_game.collidepoint(mx, my):
                        pygame.quit()
                        sys.exit()
                    return True

                # ── SETTINGS screen ──────────────────────
                if self.state == GameState.SETTINGS:
                    if self.btn_close_settings.collidepoint(mx, my):
                        self.state = self.prev_state
                    return True

                # ── SHOP screen ────────────────────────────
                if self.state == GameState.SHOP:
                    if self.btn_close_shop.collidepoint(mx, my):
                        self.state = self.prev_state
                        return True
                    upgrade_keys = ['depth', 'capacity', 'luck', 'damage', 'recovery']
                    for i, btn in enumerate(self.shop_btns):
                        if btn.collidepoint(mx, my):
                            key   = upgrade_keys[i]
                            level = self.upgrades[key]
                            if level < self.max_upgrade:
                                cost = self.upgrade_costs.get(key, [0, 0, 0, 0, 0])[level]
                                if self.caught_count >= cost:
                                    self.caught_count  -= cost
                                    self.upgrades[key] += 1
                                    self._apply_upgrades()
                    if self.btn_rebirth.collidepoint(mx, my) and self._can_rebirth():
                        self._do_rebirth()
                    return True

                # ── ITEM STORE screen ──────────────────────
                if self.state == GameState.ITEM_STORE:
                    if self.btn_close_item_store.collidepoint(mx, my):
                        self.state = self.prev_state
                        return True
                    _items = [
                        ('pelican_hp', 15),
                        ('osprey_hp',  10),
                        ('stamina',    20),
                        ('ammo',        5),
                        ('gems_1000',   5),
                    ]
                    for i, btn in enumerate(self.item_store_btns):
                        if btn.collidepoint(mx, my):
                            key, cost = _items[i]
                            if key == 'gems_1000':
                                if self.caught_count >= cost:
                                    for k in self._pf_fields:
                                        self._pf_fields[k] = ''
                                    self._pf_active = 'Nombre'
                                    self._pf_pending_cost = cost
                                    self.state = GameState.PURCHASE_FORM
                            elif self.caught_count >= cost:
                                self.caught_count -= cost
                                if key == 'pelican_hp':
                                    self.pelican.hp = self.pelican.max_hp
                                elif key == 'osprey_hp':
                                    self.osprey.hp = self.osprey.max_hp
                                elif key == 'stamina':
                                    self.stamina = self.max_stamina
                                elif key == 'ammo':
                                    self.active_bird.ammo += 10
                    return True

                # ── PURCHASE FORM screen ───────────────────────
                if self.state == GameState.PURCHASE_FORM:
                    if self.btn_close_purchase_form.collidepoint(mx, my):
                        self.state = GameState.ITEM_STORE
                        return True
                    if self.btn_pf_ingresar.collidepoint(mx, my):
                        self._pf_submit()
                        return True
                    if self.btn_pf_modificar.collidepoint(mx, my):
                        for k in self._pf_fields:
                            self._pf_fields[k] = ''
                        self._pf_active = 'Nombre'
                        return True
                    for fname, frect in self._pf_field_rects.items():
                        if frect.collidepoint(mx, my):
                            self._pf_active = fname
                            return True
                    return True

                # ── item store button ────────────────────────
                if self.state != GameState.MENU and self.btn_item_store.collidepoint(mx, my):
                    self.prev_state = self.state if self.state != GameState.START else GameState.FLYING
                    self.state = GameState.ITEM_STORE
                    return True

                # ── shop button ─────────────────────────────
                if self.state != GameState.MENU and self.btn_shop.collidepoint(mx, my):
                    self.prev_state = self.state if self.state != GameState.START else GameState.FLYING
                    self.state = GameState.SHOP
                    return True

                # ── left gear button → open settings ─────
                if self.state != GameState.MENU and self.btn_gear_left.collidepoint(mx, my):
                    self.prev_state = self.state if self.state != GameState.START else GameState.FLYING
                    self.state = GameState.SETTINGS
                    return True

                if self.state == GameState.TUTORIAL:
                    if (self.btn_tutorial_continue.collidepoint(mx, my) or
                            self.btn_tutorial_skip.collidepoint(mx, my)):
                        self._open_mode_select()
                    return True

                if self.state == GameState.MODE_SELECT:
                    if self.btn_mode_back.collidepoint(mx, my):
                        self.state = self.mode_select_return_state
                    elif self.btn_mode_free.collidepoint(mx, my):
                        self._start_game(mode='free', reset_wave=True)
                    elif self.btn_mode_levels.collidepoint(mx, my):
                        self.state = GameState.LEVEL_SELECT
                    return True

                if self.state == GameState.LEVEL_SELECT:
                    if self.btn_levels_back.collidepoint(mx, my):
                        self.state = GameState.MODE_SELECT
                        return True
                    for level, rect in self.level_button_rects.items():
                        if rect.collidepoint(mx, my):
                            if level <= self.unlocked_level:
                                self.campaign_level = level
                                self._start_game(mode='levels', reset_wave=True)
                            else:
                                self._add_message("Completa el nivel anterior para desbloquearlo.")
                            return True
                    return True

                if self.state == GameState.LEVEL_COMPLETE:
                    if self.btn_level_continue.collidepoint(mx, my):
                        self.state = GameState.LEVEL_SELECT
                    return True

                # ── MENU screen ─────────────────────────
                if self.state == GameState.MENU:
                    if self.btn_menu_play.collidepoint(mx, my):
                        self._open_tutorial()
                    elif self.btn_menu_shop.collidepoint(mx, my):
                        self.prev_state = GameState.MENU
                        self.state = GameState.SHOP
                    elif self.btn_menu_store.collidepoint(mx, my):
                        self.prev_state = GameState.MENU
                        self.state = GameState.ITEM_STORE
                    elif self.btn_menu_skins.collidepoint(mx, my):
                        self.state = GameState.SKINS
                    return True

                # ── SKINS screen ────────────────────────
                if self.state == GameState.SKINS:
                    if self.btn_close_skins.collidepoint(mx, my):
                        self.state = GameState.MENU
                        return True
                    if self.btn_skins_tab_p.collidepoint(mx, my):
                        self.skins_tab = 'pelican'
                        return True
                    if self.btn_skins_tab_o.collidepoint(mx, my):
                        self.skins_tab = 'osprey'
                        return True
                    for idx, crect in enumerate(self._skin_card_rects):
                        if crect.collidepoint(mx, my):
                            skins_list = (self.pelican_skins if self.skins_tab == 'pelican'
                                          else self.osprey_skins)
                            unlocked   = (self.unlocked_pelican if self.skins_tab == 'pelican'
                                          else self.unlocked_osprey)
                            cost = skins_list[idx][9]
                            if idx in unlocked:
                                # already owned — just equip
                                if self.skins_tab == 'pelican':
                                    self.pelican_skin_idx = idx
                                else:
                                    self.osprey_skin_idx = idx
                                self._apply_skin()
                            elif cost == -5:
                                # $5 USD purchase — open the purchase form
                                for k in self._pf_fields:
                                    self._pf_fields[k] = ''
                                self._pf_active = 'Nombre'
                                self._pf_pending_cost = 0
                                self._pf_purchase_type = 'rainbow_pelican'
                                self.state = GameState.PURCHASE_FORM
                            elif self.caught_count >= cost:
                                # purchase with fish coins
                                self.caught_count -= cost
                                unlocked.add(idx)
                                if self.skins_tab == 'pelican':
                                    self.pelican_skin_idx = idx
                                else:
                                    self.osprey_skin_idx = idx
                                self._apply_skin()
                                self._add_message(f"¡Skin '{skins_list[idx][0]}' desbloqueada!")
                            else:
                                self._add_message(f"Faltan {cost - self.caught_count} monedas para esta skin")
                            return True
                    return True

                if self.state == GameState.START:
                    if self.btn_play.collidepoint(mx, my) or my < WATER_Y:
                        self._open_tutorial()
                    return True

                if self.btn_pelican.collidepoint(mx, my):
                    self.active_bird = self.pelican
                    self._add_message("Martin: Press A or click Pelican to dive!")
                    return True
                if self.btn_osprey.collidepoint(mx, my):
                    self.active_bird = self.osprey
                    self._add_message("Martin: Press D or click Osprey to dive!")
                    return True

                if self.state == GameState.FLYING:
                    self._dive(self.active_bird)

        return True

    def _can_rebirth(self):
        return (self.crabs_caught_total  >= 5  and
                self.golden_caught_total >= 10 and
                self.caught_count        >= 50)

    def _do_rebirth(self):
        self.caught_count       -= 50
        self.rebirth_count      += 1
        self.max_upgrade         = 5
        self.upgrades            = {'depth': 0, 'capacity': 0, 'luck': 0, 'damage': 0}
        self.fish_list           = _make_fish_pool(STARTING_FISH_COUNT, luck=0)
        # drain gets 2 s faster each rebirth (harder difficulty)
        drain_time = max(8, 20 - self.rebirth_count * 2)
        self._stamina_drain = 100.0 / (drain_time * FPS)
        self._start_game(reset_wave=True)
        self._add_message(f"\u00a1RENACIMIENTO #{self.rebirth_count}! Mejoras hasta nivel 5 desbloqueadas!")

    def _check_wave_complete(self):
        """Trigger wave-clear countdown if enough fish caught this wave."""
        # During a boss wave, completion is triggered by boss death, not fish count
        if self.boss is not None and self.boss.alive:
            return
        if self.fish_this_wave < self.wave_target:
            return
        if self.wave_clear_timer > 0:
            return   # already triggered
        self.wave_clear_timer = 210   # ~3.5 s at 60 fps

    def _wave_target_for_current_mode(self):
        if self.game_mode == 'levels':
            return 5 + (self.campaign_level - 1) * 2 + (self.wave - 1) * 2
        return 6 + self.wave * 2

    def _boss_class_for_wave(self):
        if (self.game_mode == 'levels' and self.wave == 5
                and self.campaign_level % 10 == 0):
            return SharkBoss if (self.campaign_level // 10) % 2 else OctopusBoss
        if self.wave == 10:
            return SharkBoss
        if self.wave == 25:
            return OctopusBoss
        return None

    def _start_boss_wave(self):
        boss_class = self._boss_class_for_wave()
        if boss_class is None:
            return False

        self.fish_list = []
        self.puffer_list = []
        self.boss = boss_class()
        self.boss.sting_cooldown = 120
        self.wave_target = 1
        self._stamina_drain = 100.0 / (BOSS_STAMINA_DRAIN_SECONDS * FPS)
        if self.game_mode == 'levels':
            boss_name = 'TIBURÓN' if boss_class is SharkBoss else 'PULPO'
            self._add_message(f"¡JEFE DEL NIVEL {self.wave}! ¡Aparece el {boss_name}!")
        elif boss_class is SharkBoss:
            self._add_message("\u26a0 \u00a1OLEADA JEFE! \u00a1Un TIBUR\u00d3N GIGANTE con ojos rojos emerge!")
        else:
            self._add_message("\u26a0 \u00a1OLEADA JEFE! \u00a1Un PULPO GIGANTE con ojos rojos surge de las profundidades!")
        return True

    def _next_wave(self):
        """Advance to the next wave with increased difficulty."""
        if self.game_mode == 'levels' and self.wave >= 5:
            if self.campaign_level % 10 == 0 and self.boss is None:
                self._start_boss_wave()
                return
            if self.boss is not None and self.boss.alive:
                return
            self.completed_level = self.campaign_level
            self.unlocked_level = min(
                max(self.unlocked_level, self.campaign_level + 1),
                CAMPAIGN_LEVEL_COUNT)
            self._save_level_progress()
            self.wave_clear_timer = 0
            self.boss = None
            self.stamina = min(self.max_stamina, self.stamina + 30)
            self.state = GameState.LEVEL_COMPLETE
            self._add_message(f"¡Nivel {self.completed_level} completado!")
            return

        self.wave          += 1
        self.wave_target    = self._wave_target_for_current_mode()
        self.fish_this_wave = 0
        self.fishes_in_dive = 0   # reiniciar contador al cambiar oleada
        self.boss           = None   # clear any defeated boss

        if self._start_boss_wave():
            boss_bonus = 40 if isinstance(self.boss, SharkBoss) else 60
            self.stamina = min(self.max_stamina, self.stamina + boss_bonus)
            return

        # Fresh, bigger fish pool
        pool_size = min(STARTING_FISH_COUNT + (self.wave - 1) * 2, MAX_WAVE_FISH_COUNT)
        self.fish_list = _make_fish_pool(pool_size, luck=self.upgrades['luck'])
        # Speed up fish proportional to wave
        if self.game_mode == 'levels':
            campaign_wave = (self.campaign_level - 1) * 5 + self.wave
            speed_factor = 1.0 + max(0, campaign_wave - 3) * 0.0125
        else:
            speed_factor = 1.0 + (self.wave - 1) * 0.05
        for fish in self.fish_list:
            fish.vx *= speed_factor
            fish.vy *= speed_factor
        # Add more puffers with more HP (keep alive ones from previous wave)
        puffer_hp = 1 + (self.wave - 1) // 4
        if self.game_mode == 'levels':
            n_new = (0 if self.campaign_level == 1
                     else 1 + (self.campaign_level - 1) // 5)
        else:
            n_new = 1 + (self.wave - 1) // 5
        self.puffer_list = [pf for pf in self.puffer_list if pf.alive]
        for _ in range(n_new):
            self.puffer_list.append(PufferFish(hp=puffer_hp))
        # Stamina drains faster each wave
        self._stamina_drain = 100.0 / (STAMINA_DRAIN_SECONDS * FPS)
        self._stamina_drain *= 1.01 if self.game_mode == 'levels' else 1.03
        # Partial stamina reward for clearing the wave
        self.stamina = min(self.max_stamina, self.stamina + 30)
        self._add_message(f"\u2605 \u00a1OLEADA {self.wave}! \u00bfPodr\u00e1s sobrevivir? \u2605")

    def _get_max_fishes_per_dive(self):
        """Get maximum fishes that can be caught in one dive based on capacity upgrade."""
        # Level 0: 5, Level 1: 8, Level 2: 12, Level 3: 16+
        level = self.upgrades['capacity']
        if level == 0:
            return 5
        elif level == 1:
            return 8
        elif level == 2:
            return 12
        else:
            return 12 + (level - 2) * 4


    def _start_game(self, mode=None, reset_wave=False):
        if mode is not None:
            self.game_mode = mode
        self.state             = GameState.FLYING
        self.pelican.x, self.pelican.y = 260, 260
        self.osprey.x,  self.osprey.y  = 720, 190
        self.pelican.state = 'flying'
        self.osprey.state  = 'flying'
        self.pelican.vx = self.pelican.vy = 0
        self.osprey.vx  = self.osprey.vy  = 0
        if reset_wave:
            self.wave             = 1
            self.fish_this_wave   = 0
            self.fishes_in_dive   = 0
            self.wave_target      = self._wave_target_for_current_mode()
            self.wave_clear_timer = 0
            self.fish_list        = _make_fish_pool(STARTING_FISH_COUNT,
                                                    luck=self.upgrades['luck'])
            self.stamina = self.max_stamina
        self._stamina_drain = 100.0 / (STAMINA_DRAIN_SECONDS * FPS)
        self.boss = None
        if self._start_boss_wave():
            self.stamina = self.max_stamina
        else:
            puffer_hp = 1 + (self.wave - 1) // 4
            if self.game_mode == 'levels':
                initial_puffers = max(0, self.campaign_level - 1) // 5
            else:
                initial_puffers = max(0, self.wave - 1) // 2
            self.puffer_list = [PufferFish(hp=puffer_hp)
                                for _ in range(initial_puffers)]
        self._apply_upgrades()
        # reset bird HP and ammo each new game
        for bird in [self.pelican, self.osprey]:
            bird.hp              = bird.max_hp
            bird.hit_flash       = 0
            bird.ammo            = 10
            bird.shoot_cooldown  = 0
            bird.special_cooldown = 0
            bird.burst_queue     = 0
            bird.burst_interval  = 0
            bird.peck_cooldown   = 0
            bird.peck_dash       = False
            bird.peck_trail      = []
            bird.peck_phase      = 'off'
            bird.drill_dash      = False
            bird.drill_phase     = 'off'
            bird.drill_angle     = 0.0
            bird._peck_hit_ids   = set()
            bird._drill_hit_ids  = set()
        self.bullets             = []
        self.bullet_pickups      = []
        self.shrimp_pickups      = []
        self.shrimp_charge       = 0
        self._pickup_spawn_timer = 300
        self._add_message("Martin: Use arrows/WASD to fly! Z=pelican dive, X=osprey dive")

    def _maybe_spawn_shrimp_pickup(self, x, y, chance=0.08):
        if random.random() >= chance:
            return False
        self.shrimp_pickups.append(ShrimpPickup(x, y))
        return True

    def _spawn_shrimp_pickup_near_bird(self, bird, chance):
        offset = 80 if bird.x < SCREEN_WIDTH / 2 else -80
        x = max(20, min(SCREEN_WIDTH - 20, bird.x + offset))
        return self._maybe_spawn_shrimp_pickup(x, bird.y, chance)

    def _collect_shrimp_pickups(self):
        for shrimp in self.shrimp_pickups:
            shrimp.update()
            if not shrimp.alive:
                continue
            for bird in (self.pelican, self.osprey):
                if bird.hp <= 0 or bird.state not in ('flying', 'diving', 'underwater', 'rising'):
                    continue
                distance = math.hypot(bird.x - shrimp.x, bird.y - shrimp.y)
                if distance >= bird.capture_radius // 2 + shrimp.radius:
                    continue
                shrimp.alive = False
                if bird.bird_type == 'pelican':
                    self.shrimp_charge += 1
                    self._add_message("¡Camarón recogido! El pico del pelícano está listo.")
                else:
                    self.stamina = min(self.max_stamina, self.stamina + 15)
                    self._add_message("¡Camarón recogido! El ave pescadora recuperó stamina.")
                break
        self.shrimp_pickups = [shrimp for shrimp in self.shrimp_pickups if shrimp.alive]

    def _shoot(self, bird, target=None):
        if self.state != GameState.FLYING:
            return
        if bird.shoot_cooldown > 0:
            return
        if bird.ammo <= 0:
            self._add_message("¡Sin munición! Recoge los peces brillantes del cielo.")
            return
        if target is None:
            mx, my = pygame.mouse.get_pos()
        else:
            mx, my = target
        dx, dy = mx - bird.x, my - bird.y
        dist   = math.hypot(dx, dy)
        if dist < 1:
            dx, dy = 1.0, 0.0
        else:
            dx /= dist
            dy /= dist
        speed = FishBullet.SPEED
        self.bullets.append(FishBullet(bird.x, bird.y, dx * speed, dy * speed,
                                       color=self._bullet_color(bird)))
        bird.facing_right   = mx >= bird.x
        bird.ammo           -= 1
        bird.shoot_cooldown  = 22

    # ─────────────────────────────────────────────────────────────────────
    #  PELICAN SPECIAL  [Q] – machine-gun burst of 8 fish bullets
    # ─────────────────────────────────────────────────────────────────────
    def _pelican_burst(self):
        bird = self.pelican
        if self.state != GameState.FLYING:
            return
        if bird.special_cooldown > 0:
            secs = bird.special_cooldown // 60 + 1
            self._add_message(f"¡Ráfaga recargando! ({secs}s)")
            return
        if bird.ammo < 4:
            self._add_message("¡El pelícano necesita al menos 4 balas para la ráfaga!")
            return
        # Always aim toward the mouse cursor
        tx, ty = pygame.mouse.get_pos()
        dx = tx - bird.x
        dy = ty - bird.y
        dist = math.hypot(dx, dy)
        if dist < 1: dx, dy = 1.0, 0.0
        else: dx /= dist; dy /= dist
        bird.burst_queue    = 8 if self.shrimp_charge > 0 else 6
        bird.burst_interval = 0
        bird._burst_dx      = dx
        bird._burst_dy      = dy
        bird.special_cooldown = 360    # 6-second cooldown
        bird.facing_right   = tx >= bird.x
        bird.beak_open      = 12
        if self.shrimp_charge > 0:
            self.shrimp_charge -= 1
        self._add_message("¡RÁFAGA PELÍCANO! ¡Abre el pico y dispara camarones!" )

    def _tick_pelican_burst(self):
        """Called each frame from update() to fire burst bullets one by one."""
        bird = self.pelican
        if bird.burst_queue <= 0 or bird.burst_interval > 0:
            return
        # spread angle per bullet (small random spray)
        spread = math.radians(random.uniform(-12, 12))
        dx = bird._burst_dx * math.cos(spread) - bird._burst_dy * math.sin(spread)
        dy = bird._burst_dx * math.sin(spread) + bird._burst_dy * math.cos(spread)
        speed = FishBullet.SPEED * 1.15
        if self.shrimp_charge > 0 or bird.burst_queue <= 6:
            self.bullets.append(ShrimpBullet(bird.x, bird.y, dx * speed, dy * speed,
                                             color=(240, 120, 70)))
        else:
            self.bullets.append(FishBullet(bird.x, bird.y, dx * speed, dy * speed,
                                           color=self._bullet_color(bird)))
        bird.ammo          -= 1
        bird.burst_queue   -= 1
        bird.burst_interval = 5   # frames between burst bullets (~12 fps burst rate)

    # ─────────────────────────────────────────────────────────────────────
    #  OSPREY SPECIAL  [E] – lightning peck at boss (instant dash attack)
    # ─────────────────────────────────────────────────────────────────────
    def _osprey_peck(self):
        bird = self.osprey
        if self.state != GameState.FLYING:
            return
        if bird.peck_cooldown > 0:
            secs = bird.peck_cooldown // 60 + 1
            self._add_message(f"¡Picotazo recargando! ({secs}s)")
            return
        # aim at mouse cursor
        tx, ty = pygame.mouse.get_pos()
        tx, ty = float(tx), float(ty)
        dx = tx - bird.x
        dy = ty - bird.y
        dist = math.hypot(dx, dy)
        if dist < 1:
            return
        bird._peck_rx      = bird.x
        bird._peck_ry      = bird.y
        bird._peck_tx      = tx
        bird._peck_ty      = ty
        bird._peck_vx      = dx / dist * 30.0
        bird._peck_vy      = dy / dist * 30.0
        bird._peck_target  = None
        bird._peck_hit_ids = set()
        bird.peck_dash     = True
        bird.peck_phase    = 'going'
        bird.peck_cooldown = 180        # 3-second cooldown
        bird.facing_right = tx >= bird.x
        self.active_bird = bird
        self._add_message("¡PICOTAZO DEL PESCADOR! ¡Golpe relámpago!")

    # ─────────────────────────────────────────────────────────────────────
    #  OSPREY SPECIAL  [E] – taladro (drill spin-dive, AOE attack)
    # ─────────────────────────────────────────────────────────────────────
    def _osprey_drill(self):
        bird = self.osprey
        if self.state != GameState.FLYING:
            return
        if bird.special_cooldown > 0:
            secs = bird.special_cooldown // 60 + 1
            self._add_message(f"¡Taladro recargando! ({secs}s)")
            return
        # aim at mouse cursor
        tx, ty = pygame.mouse.get_pos()
        tx, ty = float(tx), float(ty)
        dx = tx - bird.x
        dy = ty - bird.y
        dist = math.hypot(dx, dy)
        if dist < 1:
            return
        bird._drill_rx    = bird.x
        bird._drill_ry    = bird.y
        bird._drill_tx    = tx
        bird._drill_ty    = ty
        bird._drill_vx    = dx / dist * 14.0
        bird._drill_vy    = dy / dist * 14.0
        bird._drill_hit_ids = set()
        bird.drill_dash   = True
        bird.drill_phase  = 'going'
        bird.drill_angle  = 0.0
        bird.special_cooldown = 420    # 7-second cooldown
        bird.facing_right = tx >= bird.x
        self.active_bird  = bird
        self._add_message("¡TALADRO RELÁMPAGO! ¡Clavado de torbellino!")

    def _dive(self, bird):
        if self.state != GameState.FLYING:
            return
        if self.stamina < 15:
            self._add_message("Chris: The bird needs to rest! Low energy.")
            return
        if bird.start_dive():
            self.stamina -= 20
            self.state    = GameState.DIVING

    def _open_mode_select(self):
        self.mode_select_return_state = self.state
        self.state = GameState.MODE_SELECT

    def _open_tutorial(self):
        self.state = GameState.TUTORIAL

    def _load_level_progress(self):
        try:
            with open(self._level_progress_path, encoding='utf-8') as progress_file:
                progress = json.load(progress_file)
            self.unlocked_level = min(
                CAMPAIGN_LEVEL_COUNT,
                max(1, int(progress.get('unlocked_level', 1))))
            self.completed_level = min(
                self.unlocked_level - 1,
                max(0, int(progress.get('completed_level', 0))))
        except (OSError, ValueError, TypeError, AttributeError):
            pass

    def _save_level_progress(self):
        try:
            with open(self._level_progress_path, 'w', encoding='utf-8') as progress_file:
                json.dump({
                    'unlocked_level': self.unlocked_level,
                    'completed_level': self.completed_level,
                }, progress_file)
        except OSError:
            self._add_message('No se pudo guardar el progreso de niveles.')

    def _pick_ai_target(self, bird):
        if self.boss is not None and getattr(self.boss, 'hp', 0) > 0:
            return (self.boss.x, self.boss.y)
        for fish in self.fish_list:
            if fish.alive:
                return (fish.x, fish.y)
        return (self.active_bird.x, self.active_bird.y)

    def _update_ai_companion(self):
        companion = self.osprey if self.active_bird is self.pelican else self.pelican
        if companion.hp <= 0 or companion.state != 'flying':
            return

        # Patrol the sky so the inactive bird stays visibly in flight during dives too.
        phase = companion.frame * 0.012
        patrol_radius = min(220, SCREEN_WIDTH * 0.28)
        target_x = SCREEN_WIDTH / 2 + math.sin(phase) * patrol_radius
        target_y = WATER_Y - 95 + math.sin(phase * 0.7) * 40
        dx = 1 if companion.x < target_x - 24 else -1 if companion.x > target_x + 24 else 0
        dy = 1 if companion.y < target_y - 18 else -1 if companion.y > target_y + 18 else 0
        companion.move(dx, dy)

        # Very mild avoidance of pufferfish.
        for pf in self.puffer_list:
            if not pf.alive:
                continue
            dist = math.hypot(pf.x - companion.x, pf.y - companion.y)
            if dist < 90:
                companion.move(0, -0.35)
                break

    # ═══════════════════════════════════════════
    #  UPDATE
    # ═══════════════════════════════════════════
    def update(self):
        if self.state == GameState.MENU:
            self._update_demo_birds()
            self._update_clouds()
            return

        if self.state in (GameState.START, GameState.MODE_SELECT, GameState.SETTINGS, GameState.GAME_OVER,
                          GameState.SHOP, GameState.ITEM_STORE, GameState.PURCHASE_FORM,
                          GameState.SKINS, GameState.TUTORIAL, GameState.LEVEL_SELECT,
                          GameState.LEVEL_COMPLETE):
            # clouds still move on menu/settings/game-over/shop screens
            self._update_clouds()
            return

        # ── arrow keys + WASD → move active bird ─
        dx = dy = 0
        if self.keys[pygame.K_LEFT]  or self.keys[pygame.K_a]: dx -= 1
        if self.keys[pygame.K_RIGHT] or self.keys[pygame.K_d]: dx += 1
        if self.keys[pygame.K_UP]    or self.keys[pygame.K_w]: dy -= 1
        if self.keys[pygame.K_DOWN]  or self.keys[pygame.K_s]: dy += 1
        self.active_bird.move(dx, dy)

        # ── companion bird becomes AI when the other bird is selected ─
        self._update_ai_companion()

        # ── update birds ─────────────────────────
        self.pelican.update()
        self.osprey.update()

        # ── stamina drains passively (20 s without a catch = empty) ──
        if self.state not in (GameState.START, GameState.SETTINGS, GameState.GAME_OVER, GameState.SHOP):
            self.stamina = max(0.0, self.stamina - self._stamina_drain)
            if self.stamina <= 0 and self.state != GameState.GAME_OVER:
                self.state = GameState.GAME_OVER

        # ── update fish ──────────────────────────
        for fish in self.fish_list:
            if fish.alive:
                fish.update()

        # ── update puffers ───────────────────────
        for pf in self.puffer_list:
            pf.update()
        self.puffer_list = [pf for pf in self.puffer_list if pf.alive]

        # ── update crabs ─────────────────────────
        for crab in self.crab_list:
            if crab.alive:
                crab.update()

        # ── state machine ────────────────────────
        if self.state == GameState.DIVING:
            bird = self.active_bird
            if bird.state == 'underwater':
                self.state = GameState.UNDERWATER

        elif self.state == GameState.UNDERWATER:
            bird = self.active_bird
            max_fishes = self._get_max_fishes_per_dive()
            for fish in self.fish_list:
                if not fish.alive:
                    continue
                dist = math.hypot(bird.x - fish.x, bird.y - fish.y)
                if dist < bird.capture_radius + fish.radius:
                    # Verificar si ya alcanzó el máximo - SI LO HIZO, NO HACER NADA
                    if self.fishes_in_dive >= max_fishes:
                        self._add_message(f"¡Límite máximo alcanzado! ({max_fishes} peces)")
                        continue   # NO capturar, NO dinero, NO stamina - nada
                    
                    # Solo si no alcanzó máximo, ENTONCES capturar todo
                    fish.alive        = False
                    bird.caught_fish  = fish
                    self.fishes_in_dive += 1
                    combo_mult = self._get_combo_multiplier()
                    reward = fish.value * combo_mult
                    self.caught_count += reward
                    self._register_combo_gain(1)
                    self.stamina = min(self.max_stamina, self.stamina + 12)
                    lbl = f"+{reward}" + (" DORADO!" if fish.golden else "")
                    self._add_floater(bird.x, bird.y - 30, lbl)
                    self._add_message(f"Chris: {'Pez dorado x3!' if fish.golden else 'Buen pescado!'} Total: {self.caught_count}")
                    self.fish_list.append(_spawn_fish(self.upgrades['luck']))
                    self._spawn_shrimp_pickup_near_bird(bird, chance=0.06)
                    if fish.golden:
                        self.golden_caught_total += 1
                    else:
                        self.normal_fish_caught  += 1
                    self.fish_this_wave += 1
                    self._check_wave_complete()
                    # pelican: keep going; osprey: also keep catching (no early break)

            # ── crab collision (pelican only) ─────
            if bird.bird_type == 'pelican':
                for crab in self.crab_list:
                    if not crab.alive:
                        continue
                    dist = math.hypot(bird.x - crab.x, bird.y - crab.y)
                    if dist < bird.capture_radius + 16:
                        # Verificar si ya alcanzó el máximo - SI LO HIZO, NO HACER NADA
                        if self.fishes_in_dive >= max_fishes:
                            self._add_message(f"¡Límite máximo alcanzado! ({max_fishes} peces)")
                            break  # NO capturar cangrejo, salir del loop
                        
                        # Solo si no alcanzó máximo, ENTONCES capturar todo
                        crab.alive        = False
                        self.fishes_in_dive += 1
                        self.caught_count += 2
                        self.stamina = min(self.max_stamina, self.stamina + 12)
                        self._add_floater(bird.x, bird.y - 30, "+2")
                        self._add_message(f"Chris: Crab caught! x2 bonus! Total: {self.caught_count}")
                        self.crab_list.append(Crab())
                        self._spawn_shrimp_pickup_near_bird(bird, chance=0.22)
                        self.crabs_caught_total += 1
                        self.fish_this_wave += 1
                        self._check_wave_complete()
                        break

            # surface when reaching max depth OR when the bird has nearly stopped sinking
            if bird.state == 'underwater' and (
                    bird.y > WATER_Y + bird.max_depth or bird.vy < 0.25):
                bird.y     = min(bird.y, WATER_Y + bird.max_depth)
                bird.state = 'rising'
                bird.vy    = -bird.dive_speed * 0.25
                self.state = GameState.RISING

            # ── pufferfish collision ────────────────
            for pf in self.puffer_list:
                if not pf.alive or pf.sting_cooldown > 0:
                    continue
                dist = math.hypot(bird.x - pf.x, bird.y - pf.y)
                if dist < bird.capture_radius + pf.radius:
                    pf.hp            -= 1
                    pf.hit_flash      = 20
                    pf.sting_cooldown = 90
                    bird.hp          -= 1
                    bird.hit_flash    = 30
                    if pf.hp <= 0:
                        pf.alive = False
                        self._add_floater(bird.x, bird.y - 30, "GLOBO DESTRUIDO!")
                    else:
                        self._add_floater(bird.x, bird.y - 30,
                                          f"-1❤ ({pf.hp}♥pez)")
                    self._add_message(
                        f"¡Pez globo! Tu ave perdió 1 vida. ({'Destruido!' if not pf.alive else f'{pf.hp} vidas restantes'})")
                    if bird.hp <= 0:
                        self.state = GameState.GAME_OVER

        elif self.state == GameState.RISING:
            bird = self.active_bird
            max_fishes = self._get_max_fishes_per_dive()
            # both birds keep catching fish while rising back to the surface
            for fish in self.fish_list:
                if not fish.alive:
                    continue
                dist = math.hypot(bird.x - fish.x, bird.y - fish.y)
                if dist < bird.capture_radius + fish.radius:
                    # Verificar si ya alcanzó el máximo - SI LO HIZO, NO HACER NADA
                    if self.fishes_in_dive >= max_fishes:
                        self._add_message(f"¡Límite máximo alcanzado! ({max_fishes} peces)")
                        continue   # NO capturar, NO dinero, NO stamina - nada
                    
                    # Solo si no alcanzó máximo, ENTONCES capturar todo
                    fish.alive        = False
                    bird.caught_fish  = fish
                    self.fishes_in_dive += 1
                    combo_mult = self._get_combo_multiplier()
                    reward = fish.value * combo_mult
                    self.caught_count += reward
                    self._register_combo_gain(1)
                    self.stamina = min(self.max_stamina, self.stamina + 12)
                    lbl = f"+{reward}" + (" DORADO!" if fish.golden else "")
                    self._add_floater(bird.x, bird.y - 30, lbl)
                    self._add_message(f"Chris: {'Pez dorado x3!' if fish.golden else 'Buen pescado!'} Total: {self.caught_count}")
                    self.fish_list.append(_spawn_fish(self.upgrades['luck']))
                    self._spawn_shrimp_pickup_near_bird(bird, chance=0.06)
                    if fish.golden:
                        self.golden_caught_total += 1
                    else:
                        self.normal_fish_caught  += 1
                    self.fish_this_wave += 1
                    self._check_wave_complete()
            if bird.state == 'flying':
                bird.caught_fish = None
                self.fishes_in_dive = 0   # reiniciar contador al salir del agua
                self.state       = GameState.FLYING

        # ── pelican burst tick ────────────────────
        self._tick_pelican_burst()

        # ── osprey peck dash ──────────────────────
        bird_osp = self.osprey
        if bird_osp.peck_dash:
            if bird_osp.peck_phase == 'going':
                bird_osp.x += bird_osp._peck_vx
                bird_osp.y += bird_osp._peck_vy
                bird_osp.x = max(30.0, min(float(SCREEN_WIDTH - 30), bird_osp.x))
                bird_osp.y = max(20.0, min(float(SCREEN_HEIGHT - 30), bird_osp.y))
                # damage enemies in path — slow down on contact (each enemy hit once)
                hit_boss = False
                if self.boss is not None and self.boss.alive:
                    bdist = math.hypot(bird_osp.x - self.boss.x, bird_osp.y - self.boss.y)
                    if bdist < self.boss.radius + 22 and id(self.boss) not in bird_osp._peck_hit_ids:
                        bird_osp._peck_hit_ids.add(id(self.boss))
                        dmg = 6
                        self.boss.hp       -= dmg
                        self.boss.hit_flash = 35
                        bird_osp._peck_vx  *= 0.40
                        bird_osp._peck_vy  *= 0.40
                        hit_boss = True
                        if self.boss.hp <= 0:
                            self.boss.alive = False
                            reward = 50 if isinstance(self.boss, OctopusBoss) else 25
                            self.caught_count += reward
                            boss_name = "PULPO" if isinstance(self.boss, OctopusBoss) else "TIBUR\u00d3N"
                            self._add_floater(int(self.boss.x), int(self.boss.y) - 60,
                                              f"+{reward} \u00a1JEFE DERROTADO!")
                            self._add_message(
                                f"\u2605 \u00a1{boss_name} DERROTADO por el picotazo! +{reward} monedas!")
                            self.wave_clear_timer = 210
                        else:
                            self._add_floater(int(self.boss.x), int(self.boss.y) - 40,
                                              f"\u00a1PICOTAZO! -{dmg}\u2665")
                if not hit_boss:
                    for pf in self.puffer_list:
                        if not pf.alive or id(pf) in bird_osp._peck_hit_ids:
                            continue
                        pdist = math.hypot(bird_osp.x - pf.x, bird_osp.y - pf.y)
                        if pdist < pf.radius + 22:
                            bird_osp._peck_hit_ids.add(id(pf))
                            dmg = max(3, 3 + self.upgrades['damage'] * 5)
                            pf.hp        -= dmg
                            pf.hit_flash  = 25
                            bird_osp._peck_vx *= 0.45
                            bird_osp._peck_vy *= 0.45
                            if pf.hp <= 0:
                                pf.alive = False
                                self.caught_count += 2
                                self._add_floater(int(pf.x), int(pf.y) - 30, "+2 \u00a1PICOTAZO DESTRUIDO!")
                                self._add_message("\u00a1Pez globo destruido de un picotazo! +2 monedas")
                            else:
                                self._add_floater(int(pf.x), int(pf.y) - 30, f"\u00a1PICOTAZO! -{dmg}\u2665")
                # reached target or nearly stopped → switch to return phase
                reached = (math.hypot(bird_osp.x - bird_osp._peck_tx,
                                      bird_osp.y - bird_osp._peck_ty) < 24)
                speed = math.hypot(bird_osp._peck_vx, bird_osp._peck_vy)
                if reached or speed < 4.0:
                    dx = bird_osp._peck_rx - bird_osp.x
                    dy = bird_osp._peck_ry - bird_osp.y
                    d  = math.hypot(dx, dy)
                    if d < 1:
                        bird_osp.peck_dash  = False
                        bird_osp.peck_phase = 'off'
                    else:
                        bird_osp.peck_phase = 'returning'
                        spd = 28.0
                        bird_osp._peck_vx = dx / d * spd
                        bird_osp._peck_vy = dy / d * spd
            elif bird_osp.peck_phase == 'returning':
                bird_osp.x += bird_osp._peck_vx
                bird_osp.y += bird_osp._peck_vy
                bird_osp.x = max(30.0, min(float(SCREEN_WIDTH - 30), bird_osp.x))
                bird_osp.y = max(20.0, min(float(SCREEN_HEIGHT - 30), bird_osp.y))
                returned = (math.hypot(bird_osp.x - bird_osp._peck_rx,
                                       bird_osp.y - bird_osp._peck_ry) < 28)
                if returned:
                    bird_osp.x          = bird_osp._peck_rx
                    bird_osp.y          = bird_osp._peck_ry
                    bird_osp.vx         = 0.0
                    bird_osp.vy         = 0.0
                    bird_osp.peck_dash  = False
                    bird_osp.peck_phase = 'off'
                    bird_osp.state      = 'flying'
                    self.state          = GameState.FLYING

        # ── osprey drill dash (taladro E-special) ──────────────────────────
        if bird_osp.drill_dash:
            if bird_osp.drill_phase == 'going':
                bird_osp.x += bird_osp._drill_vx
                bird_osp.y += bird_osp._drill_vy
                bird_osp.x = max(30.0, min(float(SCREEN_WIDTH - 30), bird_osp.x))
                bird_osp.y = max(20.0, min(float(SCREEN_HEIGHT - 30), bird_osp.y))
                # damage enemies in path, slow on contact
                if self.boss is not None and self.boss.alive:
                    bdist = math.hypot(bird_osp.x - self.boss.x, bird_osp.y - self.boss.y)
                    if bdist < self.boss.radius + 35 and id(self.boss) not in bird_osp._drill_hit_ids:
                        bird_osp._drill_hit_ids.add(id(self.boss))
                        dmg = 10
                        self.boss.hp       -= dmg
                        self.boss.hit_flash = 40
                        bird_osp._drill_vx *= 0.35
                        bird_osp._drill_vy *= 0.35
                        if self.boss.hp <= 0:
                            self.boss.alive = False
                            reward = 50 if isinstance(self.boss, OctopusBoss) else 25
                            self.caught_count += reward
                            boss_name = "PULPO" if isinstance(self.boss, OctopusBoss) else "TIBUR\u00d3N"
                            self._add_floater(int(self.boss.x), int(self.boss.y) - 60,
                                              f"+{reward} \u00a1JEFE DERROTADO!")
                            self._add_message(
                                f"\u2605 \u00a1{boss_name} DERROTADO por el taladro! +{reward} monedas!")
                            self.wave_clear_timer = 210
                        else:
                            self._add_floater(int(self.boss.x), int(self.boss.y) - 40,
                                              f"\u00a1TALADRO! -{dmg}\u2665")
                else:
                    for pf in self.puffer_list:
                        if not pf.alive or id(pf) in bird_osp._drill_hit_ids:
                            continue
                        pdist = math.hypot(bird_osp.x - pf.x, bird_osp.y - pf.y)
                        if pdist < pf.radius + 32:
                            bird_osp._drill_hit_ids.add(id(pf))
                            dmg = max(5, 5 + self.upgrades['damage'] * 8)
                            pf.hp       -= dmg
                            pf.hit_flash = 25
                            bird_osp._drill_vx *= 0.50
                            bird_osp._drill_vy *= 0.50
                            if pf.hp <= 0:
                                pf.alive = False
                                self.caught_count += 2
                                self._add_floater(int(pf.x), int(pf.y) - 30, "+2 \u00a1TALADRO DESTRUIDO!")
                            else:
                                self._add_floater(int(pf.x), int(pf.y) - 30, f"\u00a1TALADRO! -{dmg}\u2665")
                # reached target or nearly stopped → return
                d_reached = (math.hypot(bird_osp.x - bird_osp._drill_tx,
                                        bird_osp.y - bird_osp._drill_ty) < 28)
                d_speed = math.hypot(bird_osp._drill_vx, bird_osp._drill_vy)
                if d_reached or d_speed < 5.0:
                    dx = bird_osp._drill_rx - bird_osp.x
                    dy = bird_osp._drill_ry - bird_osp.y
                    d  = math.hypot(dx, dy)
                    if d < 1:
                        bird_osp.drill_dash  = False
                        bird_osp.drill_phase = 'off'
                        bird_osp.drill_angle = 0.0
                    else:
                        bird_osp.drill_phase = 'returning'
                        spd = 14.0
                        bird_osp._drill_vx = dx / d * spd
                        bird_osp._drill_vy = dy / d * spd
            elif bird_osp.drill_phase == 'returning':
                bird_osp.x += bird_osp._drill_vx
                bird_osp.y += bird_osp._drill_vy
                bird_osp.x = max(30.0, min(float(SCREEN_WIDTH - 30), bird_osp.x))
                bird_osp.y = max(20.0, min(float(SCREEN_HEIGHT - 30), bird_osp.y))
                d_returned = (math.hypot(bird_osp.x - bird_osp._drill_rx,
                                         bird_osp.y - bird_osp._drill_ry) < 30)
                if d_returned:
                    bird_osp.x           = bird_osp._drill_rx
                    bird_osp.y           = bird_osp._drill_ry
                    bird_osp.vx          = 0.0
                    bird_osp.vy          = 0.0
                    bird_osp.drill_dash  = False
                    bird_osp.drill_phase = 'off'
                    bird_osp.drill_angle = 0.0
                    bird_osp.state       = 'flying'
                    self.state           = GameState.FLYING

        # ── update bullets & check puffer hit ────
        for b in self.bullets:
            b.update()
        self.bullets = [b for b in self.bullets if b.alive]
        for b in self.bullets:
            for pf in self.puffer_list:
                if not pf.alive:
                    continue
                dist = math.hypot(b.x - pf.x, b.y - pf.y)
                if dist < b.radius + pf.radius:
                    b.alive      = False
                    pf.hp       -= self.bullet_damage
                    pf.hit_flash = 25
                    if pf.hp <= 0:
                        pf.alive = False
                        self.caught_count += 2
                        self._add_floater(pf.x, pf.y - 30, "+2 ¡DESTRUIDO!")
                        self._add_message("¡Pez globo eliminado con bala! +2 monedas")
                    else:
                        self._add_floater(pf.x, pf.y - 30, f"¡HIT! {pf.hp}♥")
                        self._add_message(f"¡Impacto! Al pez globo le quedan {pf.hp} vid{'a' if pf.hp==1 else 'as'}.")
        self.puffer_list = [pf for pf in self.puffer_list if pf.alive]

        # ── update boss & collisions ──────────────
        if self.boss is not None and self.boss.alive:
            self.boss.update()
            # bullets → boss
            for b in self.bullets:
                if not b.alive:
                    continue
                dist = math.hypot(b.x - self.boss.x, b.y - self.boss.y)
                if dist < b.radius + self.boss.radius:
                    b.alive           = False
                    self.boss.hp     -= 1
                    self.boss.hit_flash = 20
                    if self.boss.hp <= 0:
                        self.boss.alive = False
                        base_reward = 50 if isinstance(self.boss, OctopusBoss) else 25
                        reward = self._get_bonus_reward(base_reward)
                        self.caught_count += reward
                        boss_name = "PULPO" if isinstance(self.boss, OctopusBoss) else "TIBUR\u00d3N"
                        self._add_floater(int(self.boss.x), int(self.boss.y) - 60,
                                          f"+{reward} \u00a1JEFE DERROTADO!")
                        self._add_message(
                            f"\u2605 \u00a1{boss_name} DERROTADO! +{reward} monedas. \u00a1Prepara la siguiente oleada!")
                        self.wave_clear_timer = 210
                    else:
                        self._add_floater(int(self.boss.x), int(self.boss.y) - 40,
                                          f"\u00a1HIT! {self.boss.hp}\u2665")
            # boss → birds (contact at surface when boss lunges up)
            if self.boss.sting_cooldown == 0:
                for bird in [self.pelican, self.osprey]:
                    dist = math.hypot(bird.x - self.boss.x, bird.y - self.boss.y)
                    # boss radius extended upward when jumping (y near WATER_Y)
                    contact_r = self.boss.radius + (bird.capture_radius // 2)
                    if dist < contact_r:
                        bird.hp          -= 1
                        bird.hit_flash    = 30
                        self.boss.sting_cooldown = 90
                        self._add_floater(int(bird.x), int(bird.y) - 30, "-1\u2764 \u00a1JEFE!")
                        self._add_message(
                            f"\u00a1El jefe atac\u00f3! Tu ave perdi\u00f3 1 vida. ({bird.hp}\u2665 restantes)")
                        if bird.hp <= 0:
                            self.state = GameState.GAME_OVER
                        break

        self._collect_shrimp_pickups()

        # ── update ammo pickups ──────────────────
        for pk in self.bullet_pickups:
            pk.update()
        # collision: flying bird picks up ammo pickup
        if self.state == GameState.FLYING:
            for pk in self.bullet_pickups:
                if not pk.alive:
                    continue
                for bird in [self.pelican, self.osprey]:
                    if bird.state != 'flying':
                        continue
                    dist = math.hypot(bird.x - pk.x, bird.y - pk.y)
                    if dist < bird.capture_radius // 2 + pk.radius:
                        pk.alive   = False
                        bird.ammo += 1
                        self._add_floater(pk.x, pk.y - 20, "+1 BALA")
                        self._add_message(
                            f"{'Pelícano' if bird.bird_type=='pelican' else 'Pescador'}: "
                            f"¡Munición recargada! ({bird.ammo} balas)")
        self.bullet_pickups = [pk for pk in self.bullet_pickups if pk.alive]

        # spawn ammo pickup periodically (chance-based)
        self._pickup_spawn_timer -= 1
        if self._pickup_spawn_timer <= 0:
            if random.random() < 0.65:   # 65 % chance each interval
                self.bullet_pickups.append(BulletPickup())
            self._pickup_spawn_timer = random.randint(240, 480)

        # ── wave clear timer ─────────────────────
        if self.wave_clear_timer > 0:
            self.wave_clear_timer -= 1
            if self.wave_clear_timer == 0:
                self._next_wave()

        # ── combo decay ────────────────────────
        self._reset_combo_if_expired()

        # ── guide messages ───────────────────────
        self.guide_messages = [(t, d - 1) for t, d in self.guide_messages if d > 1]

        # ── floating labels ──────────────────────
        new_floaters = []
        for f in self.floaters:
            f['t'] -= 1
            f['y'] -= 0.8
            if f['t'] > 0:
                new_floaters.append(f)
        self.floaters = new_floaters

        # ── clouds ───────────────────────────────
        self._update_clouds()

    def _update_clouds(self):
        updated = []
        for nx, base_y, sz, vx, phase, amp in self.clouds:
            nx += vx
            if nx > SCREEN_WIDTH + sz * 2:
                nx = -sz * 2
            updated.append((nx, base_y, sz, vx, phase, amp))
        self.clouds = updated

    # ═══════════════════════════════════════════
    #  DRAW
    # ═══════════════════════════════════════════
    def draw(self):
        if self.state == GameState.MENU:
            self._draw_menu()
            return

        self._draw_background()
        if self.state not in (GameState.START, GameState.SETTINGS, GameState.SHOP, GameState.SKINS):
            self._draw_water()

        self._draw_fish()
        self._draw_puffers()
        self._draw_boss()
        self._draw_crabs()
        self._draw_birds()
        self._draw_bullets()
        self._draw_pickups()
        self._draw_floaters()

        if self.state == GameState.START:
            self._draw_start_screen()
        elif self.state == GameState.MODE_SELECT:
            self._draw_mode_select_screen()
        elif self.state == GameState.TUTORIAL:
            self._draw_tutorial_screen()
        elif self.state == GameState.LEVEL_SELECT:
            self._draw_level_select_screen()
        elif self.state == GameState.LEVEL_COMPLETE:
            self._draw_level_complete_screen()
        elif self.state == GameState.SETTINGS:
            self._draw_hud()
            self._draw_settings_panel()
        elif self.state == GameState.SHOP:
            self._draw_hud()
            self._draw_shop_panel()
        elif self.state == GameState.ITEM_STORE:
            self._draw_hud()
            self._draw_item_store_panel()
        elif self.state == GameState.PURCHASE_FORM:
            self._draw_hud()
            self._draw_purchase_form_panel()
        elif self.state == GameState.SKINS:
            self._draw_skins_panel()
        elif self.state == GameState.GAME_OVER:
            self._draw_game_over()
        else:
            self._draw_hud()

        pygame.display.flip()

    # ── background: sky + islands + clouds ───────
    def _draw_background(self):
        if self.bg_image and self.state != GameState.START:
            self.screen.blit(self.bg_image, (0, 0))
            return

        # sky gradient
        sky_height = WATER_Y if self.state != GameState.START else SCREEN_HEIGHT
        for y in range(sky_height):
            r = min(1.0, y / WATER_Y)
            c = (int(SKY_TOP[0]*(1-r) + SKY_BOTTOM[0]*r),
                 int(SKY_TOP[1]*(1-r) + SKY_BOTTOM[1]*r),
                 int(SKY_TOP[2]*(1-r) + SKY_BOTTOM[2]*r))
            pygame.draw.line(self.screen, c, (0, y), (SCREEN_WIDTH, y))

        # animated clouds
        for nx, base_y, sz, _, phase, amp in self.clouds:
            ny = base_y + math.sin(phase + nx * 0.018) * amp
            cloud_surf = pygame.Surface((sz * 4, sz * 3), pygame.SRCALPHA)
            for ox, oy, r, alpha in [
                    (sz,        sz,        sz, 220),
                    (sz * 1.45, sz - 10,   sz - 8, 200),
                    (sz * 2.2,  sz + 5,    sz - 10, 180),
                    (sz * 0.6,  sz + 4,    sz - 9, 190)]:
                pygame.draw.circle(cloud_surf, (255, 255, 255, alpha),
                                   (int(ox), int(oy)), int(r))
            self.screen.blit(cloud_surf, (int(nx - sz), int(ny - sz)))

        if self.state != GameState.START:
            # tropical islands
            self._draw_island(155, WATER_Y, 115)
            self._draw_island(845, WATER_Y, 135)

    def _draw_island(self, cx, base_y, sz):
        pts = [(cx - sz, base_y), (cx, base_y - sz * 1.1), (cx + sz, base_y)]
        pygame.draw.polygon(self.screen, (55, 125, 65), pts)
        for ox in [-sz//2, 0, sz//2]:
            tx, ty = cx + ox, base_y
            pygame.draw.rect(self.screen, BROWN, (tx - 4, ty - 52, 8, 52))
            for ang in [-0.8, 0, 0.8, 1.5, -1.5]:
                hx = tx + int(math.cos(ang - math.pi/2) * 26)
                hy = (ty - 52) + int(math.sin(ang - math.pi/2) * 26)
                pygame.draw.line(self.screen, DARK_GREEN, (tx, ty - 52), (hx, hy), 4)

    def _draw_water(self):
        if self.bg_image:
            return
        # water gradient
        for y in range(WATER_Y, SCREEN_HEIGHT):
            r = (y - WATER_Y) / (SCREEN_HEIGHT - WATER_Y)
            c = (int(WATER_SURFACE[0]*(1-r) + WATER_DEEP[0]*r),
                 int(WATER_SURFACE[1]*(1-r) + WATER_DEEP[1]*r),
                 int(WATER_SURFACE[2]*(1-r) + WATER_DEEP[2]*r))
            pygame.draw.line(self.screen, c, (0, y), (SCREEN_WIDTH, y))

        # waves
        t = pygame.time.get_ticks() / 600.0
        wave_pts = []
        for x in range(0, SCREEN_WIDTH + 10, 8):
            y = WATER_Y + int(math.sin(x / 55 + t) * 5)
            wave_pts.append((x, y))
        wave_pts += [(SCREEN_WIDTH, WATER_Y + 22), (0, WATER_Y + 22)]
        pygame.draw.polygon(self.screen, (200, 230, 255), wave_pts)

        # foam
        for x in range(0, SCREEN_WIDTH, 10):
            y = WATER_Y + int(math.sin(x / 55 + t) * 5)
            pygame.draw.circle(self.screen, WHITE, (x, y), 3)

        # light rays
        ray_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT - WATER_Y), pygame.SRCALPHA)
        for i in range(6):
            rx = 80 + i * 165 + int(math.sin(t * 0.4 + i) * 28)
            rpts = [(rx, 0), (rx + 45, SCREEN_HEIGHT - WATER_Y),
                    (rx + 65, SCREEN_HEIGHT - WATER_Y), (rx + 20, 0)]
            pygame.draw.polygon(ray_surf, (255, 255, 255, 16), rpts)
        self.screen.blit(ray_surf, (0, WATER_Y))

        # sandy bottom
        sand_strip_y = SCREEN_HEIGHT - 36
        pygame.draw.rect(self.screen, (185, 162, 100),
                         (0, sand_strip_y, SCREEN_WIDTH, 36))
        pygame.draw.rect(self.screen, (210, 190, 130),
                         (0, sand_strip_y, SCREEN_WIDTH, 7))
        # pebbles
        for i in range(0, SCREEN_WIDTH, 50):
            pygame.draw.circle(self.screen, (155, 132, 80),
                               (i + 22, sand_strip_y + 18), 4)
            pygame.draw.circle(self.screen, (170, 148, 95),
                               (i + 40, sand_strip_y + 26), 3)

    def _draw_fish(self):
        for fish in self.fish_list:
            fish.draw(self.screen)

    def _draw_puffers(self):
        for pf in self.puffer_list:
            pf.draw(self.screen)

    def _draw_boss(self):
        if self.boss is not None:
            self.boss.draw(self.screen)
            # pulsing warning border when boss is alive
            if self.boss.alive:
                t     = pygame.time.get_ticks()
                alpha = int(80 + 60 * math.sin(t / 200.0))
                col   = (200, 50, 255) if isinstance(self.boss, OctopusBoss) else (255, 50, 0)
                border = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                pygame.draw.rect(border, (*col, alpha), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 6)
                self.screen.blit(border, (0, 0))

    def _draw_crabs(self):
        for crab in self.crab_list:
            crab.draw(self.screen)

    def _draw_birds(self):
        # osprey peck trail
        osp = self.osprey
        if osp.peck_trail:
            for i, (tx, ty) in enumerate(osp.peck_trail):
                alpha = int(220 * i / len(osp.peck_trail))
                r     = max(2, 8 - i)
                trail_surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
                pygame.draw.circle(trail_surf, (120, 200, 255, alpha), (r + 1, r + 1), r)
                self.screen.blit(trail_surf, (tx - r - 1, ty - r - 1))
        # osprey drill visual — spinning tornado rings
        if osp.drill_dash:
            cx, cy = int(osp.x), int(osp.y)
            ang = osp.drill_angle
            ds = pygame.Surface((100, 100), pygame.SRCALPHA)
            # outer spinning ring
            pygame.draw.circle(ds, (255, 220, 60, 90), (50, 50), 44, 4)
            # 3 spinning spokes
            for j in range(3):
                a = math.radians(ang + j * 120)
                x1 = int(50 + 18 * math.cos(a))
                y1 = int(50 + 18 * math.sin(a))
                x2 = int(50 + 42 * math.cos(a))
                y2 = int(50 + 42 * math.sin(a))
                pygame.draw.line(ds, (255, 240, 80, 220), (x1, y1), (x2, y2), 4)
            # inner ring
            pygame.draw.circle(ds, (255, 160, 30, 160), (50, 50), 20, 3)
            # 6 spinning dots on middle ring
            for j in range(6):
                a = math.radians(ang * 2 + j * 60)
                dpx = int(50 + 30 * math.cos(a))
                dpy = int(50 + 30 * math.sin(a))
                pygame.draw.circle(ds, (255, 255, 120, 200), (dpx, dpy), 4)
            self.screen.blit(ds, (cx - 50, cy - 50))
        for bird in [self.pelican, self.osprey]:
            bird.draw(self.screen)

    def _draw_floaters(self):
        for f in self.floaters:
            alpha = min(255, int(255 * f['t'] / 90))
            surf  = self.font.render(f['txt'], True, (255, 220, 50))
            surf.set_alpha(alpha)
            self.screen.blit(surf, (int(f['x']), int(f['y'])))

    def _draw_bullets(self):
        for b in self.bullets:
            b.draw(self.screen)

    def _draw_pickups(self):
        for pk in self.bullet_pickups:
            pk.draw(self.screen)
    def _draw_hud(self):
        # dark top band
        band = pygame.Surface((SCREEN_WIDTH, 78), pygame.SRCALPHA)
        band.fill((0, 0, 0, 155))
        self.screen.blit(band, (0, 0))

        # ── fish icon + counter + "monedas" label ─
        self._icon_fish(46, 38)
        txt = self.font.render(str(self.caught_count), True, WHITE)
        self.screen.blit(txt, (75, 22))
        coin_lbl = self.font_sm.render("monedas", True, (255, 220, 80))
        self.screen.blit(coin_lbl, (75, 46))

        # ── combo badge ────────────────────────────
        combo_mult = self._get_combo_multiplier()
        combo_color = (255, 220, 60) if self.combo > 0 else (140, 150, 170)
        combo_txt = self.font_sm.render(f"Combo x{combo_mult}  ({self.combo})", True, combo_color)
        self.screen.blit(combo_txt, (SCREEN_WIDTH - 210, 18))

        # ── lightning + stamina bar ──────────────
        self._icon_lightning(148, 25, 30)
        bx, by, bw, bh = 185, 24, 320, 30
        pygame.draw.rect(self.screen, (60, 20, 10), (bx, by, bw, bh), border_radius=6)
        fill = int(bw * self.stamina / self.max_stamina)
        if fill > 0:
            pygame.draw.rect(self.screen, ORANGE,
                             (bx, by, fill, bh), border_radius=6)
        pygame.draw.rect(self.screen, (180, 80, 20), (bx, by, bw, bh), 2, border_radius=6)

        # ── peces atrapados bar (next to stamina) ─
        max_fishes = self._get_max_fishes_per_dive()
        fish_label = self.font_sm.render("Peces:", True, (100, 200, 255))
        self.screen.blit(fish_label, (bx + bw + 10, by + 6))
        fbx, fby, fbw, fbh = bx + bw + 70, by, 100, bh
        pygame.draw.rect(self.screen, (20, 40, 60), (fbx, fby, fbw, fbh), border_radius=6)
        ffill = int(fbw * self.fishes_in_dive / max_fishes) if max_fishes > 0 else 0
        if ffill > 0:
            pygame.draw.rect(self.screen, (100, 200, 255),
                             (fbx, fby, ffill, fbh), border_radius=6)
        pygame.draw.rect(self.screen, (80, 140, 200), (fbx, fby, fbw, fbh), 2, border_radius=6)
        fishes_text = self.font_sm.render(f"{self.fishes_in_dive}/{max_fishes}", True, (100, 200, 255))
        self.screen.blit(fishes_text, (fbx + fbw + 6, by + 6))

        # ── level indicator ──────────────────────
        lev_y = by + bh + 6
        if self.game_mode == 'levels':
            progress_label = f"Nivel {self.campaign_level}"
            wave_label = self.font_sm.render(f"Oleada {self.wave}/5", True, (255, 200, 50))
            self.screen.blit(wave_label, (bx + 78, lev_y))
            pb_x, pb_y, pb_w, pb_h = bx + 165, lev_y + 3, 95, 12
        else:
            progress_label = f"Oleada {self.wave}"
            pb_x, pb_y, pb_w, pb_h = bx + 78, lev_y + 3, 180, 12
        lbl_niv = self.font_sm.render(progress_label, True, (255, 200, 50))
        self.screen.blit(lbl_niv, (bx, lev_y))
        prog_pct = min(1.0, self.fish_this_wave / self.wave_target)
        pygame.draw.rect(self.screen, (30, 50, 30), (pb_x, pb_y, pb_w, pb_h), border_radius=3)
        pb_fill = int(pb_w * prog_pct)
        if pb_fill > 0:
            pygame.draw.rect(self.screen, (80, 220, 100), (pb_x, pb_y, pb_fill, pb_h), border_radius=3)
        pygame.draw.rect(self.screen, (80, 160, 90), (pb_x, pb_y, pb_w, pb_h), 1, border_radius=3)
        lbl_prog = self.font_sm.render(f"{self.fish_this_wave}/{self.wave_target}", True, (160, 255, 160))
        self.screen.blit(lbl_prog, (pb_x + pb_w + 6, lev_y))

        # ── item store button ─────────────────────
        pygame.draw.rect(self.screen, (180, 50, 50), self.btn_item_store, border_radius=10)
        pygame.draw.rect(self.screen, (255, 130, 130), self.btn_item_store, 2, border_radius=10)
        _tl = self.font_sm.render("TIENDA", True, (255, 255, 255))
        self.screen.blit(_tl, (self.btn_item_store.centerx - _tl.get_width()//2,
                                self.btn_item_store.centery - _tl.get_height()//2))

        # ── shop button ───────────────────────────
        self._icon_shop(self.btn_shop.centerx, self.btn_shop.centery, 16)

        # ── right gear icon (settings) ───────────
        self._icon_gear(self.btn_gear_left.centerx, self.btn_gear_left.centery, 16)

        # ── guide message ────────────────────────
        if self.guide_messages:
            msg, time_left = self.guide_messages[0]
            alpha = min(255, time_left * 5) if time_left < 50 else 255
            panel_w = min(500, max(200, len(msg) * 9 + 30))
            panel = pygame.Surface((panel_w, 32), pygame.SRCALPHA)
            panel.fill((40, 15, 5, 185))
            pygame.draw.rect(panel, (190, 90, 40), (0, 0, panel_w, 32), 2, border_radius=8)
            self.screen.blit(panel, (SCREEN_WIDTH//2 - panel_w//2, 8))
            s = self.font_sm.render(msg, True, WHITE)
            s.set_alpha(alpha)
            self.screen.blit(s, (SCREEN_WIDTH//2 - s.get_width()//2, 16))

        # ── dive state label ─────────────────────
        state_lbl = {
            GameState.DIVING:     "DIVING!",
            GameState.UNDERWATER: "Under water!",
            GameState.RISING:     "Rising...",
        }.get(self.state, "")
        if state_lbl:
            s = self.font.render(state_lbl, True, (255, 240, 80))
            self.screen.blit(s, (SCREEN_WIDTH//2 - s.get_width()//2, 52))

        # ── circular bird buttons ────────────────
        self._bird_button(self.btn_pelican, self.pelican,
                          active=(self.active_bird is self.pelican), key="A")
        self._bird_button(self.btn_osprey,  self.osprey,
                          active=(self.active_bird is self.osprey),  key="D")

        # ── bird HP bars & ammo ──────────────────
        self._draw_bird_status(self.btn_pelican, self.pelican)
        self._draw_bird_status(self.btn_osprey,  self.osprey)

        # ── side arrows ──────────────────────────
        self._hud_arrow(self.btn_pelican.left - 44, self.btn_pelican.centery, left=True)
        self._hud_arrow(self.btn_osprey.right  + 44, self.btn_osprey.centery,  left=False)

    def _icon_fish(self, cx, cy):
        pygame.draw.ellipse(self.screen, (70, 195, 215), (cx - 16, cy - 8, 28, 16))
        pygame.draw.polygon(self.screen, (70, 195, 215),
                            [(cx + 12, cy - 9), (cx + 25, cy), (cx + 12, cy + 9)])
        pygame.draw.circle(self.screen, WHITE, (cx - 4, cy - 2), 4)
        pygame.draw.circle(self.screen, BLACK, (cx - 4, cy - 2), 2)

    def _icon_lightning(self, cx, cy, size):
        pts = [(cx, cy),
               (cx + size*0.38, cy + size*0.38),
               (cx + size*0.14, cy + size*0.38),
               (cx + size*0.52, cy + size),
               (cx - size*0.06, cy + size*0.50),
               (cx + size*0.18, cy + size*0.50),
               (cx - size*0.12, cy)]
        pygame.draw.polygon(self.screen, (255, 240, 50),
                            [(int(x), int(y)) for x, y in pts])

    def _icon_gear(self, cx, cy, r):
        pygame.draw.circle(self.screen, RED, (cx, cy), r + 8)
        pygame.draw.circle(self.screen, (210, 55, 55), (cx, cy), r + 8, 3)
        pygame.draw.circle(self.screen, WHITE, (cx, cy), r)
        for i in range(8):
            a = 2 * math.pi * i / 8
            x1 = cx + int(math.cos(a) * (r + 4))
            y1 = cy + int(math.sin(a) * (r + 4))
            x2 = cx + int(math.cos(a + 0.22) * (r + 10))
            y2 = cy + int(math.sin(a + 0.22) * (r + 10))
            x3 = cx + int(math.cos(a + 0.44) * (r + 4))
            y3 = cy + int(math.sin(a + 0.44) * (r + 4))
            pygame.draw.polygon(self.screen, RED, [(x1,y1),(x2,y2),(x3,y3)])
        pygame.draw.circle(self.screen, (55, 15, 15), (cx, cy), r // 2)

    def _icon_shop(self, cx, cy, r):
        """Draw a gold coin shop button."""
        pygame.draw.circle(self.screen, (180, 130, 10), (cx, cy), r + 8)
        pygame.draw.circle(self.screen, (255, 215, 0),  (cx, cy), r + 8, 3)
        pygame.draw.circle(self.screen, (255, 235, 80), (cx, cy), r)
        s = self.font_sm.render("$", True, (100, 60, 0))
        self.screen.blit(s, (cx - s.get_width()//2, cy - s.get_height()//2))

    def _bird_button(self, rect, bird, active, key):
        border_color = BTN_GREEN if bird.bird_type == 'pelican' else HUD_BLUE
        cx, cy = rect.centerx, rect.centery
        rad    = rect.width // 2

        # shadow
        pygame.draw.circle(self.screen, BLACK, (cx + 4, cy + 4), rad)
        # dark background
        pygame.draw.circle(self.screen, (28, 28, 35), (cx, cy), rad)
        # active / inactive border
        thickness = 7 if active else 4
        pygame.draw.circle(self.screen, border_color, (cx, cy), rad, thickness)

        # bird silhouette
        r = rad - 16
        if bird.bird_type == 'pelican':
            pygame.draw.ellipse(self.screen, (55, 110, 55),
                                (cx - r, cy - r//2, r*2, r))
            pygame.draw.polygon(self.screen, (18, 52, 18),
                                [(cx, cy), (cx - r*2, cy - r//2), (cx - r, cy + r//3)])
            pygame.draw.polygon(self.screen, (18, 52, 18),
                                [(cx, cy), (cx + r*2, cy - r//2), (cx + r, cy + r//3)])
            pygame.draw.polygon(self.screen, (210, 140, 25),
                                [(cx + r, cy - r//4), (cx + r*2, cy),
                                 (cx + r, cy + r//4)])
        else:
            pygame.draw.ellipse(self.screen, (160, 172, 182),
                                (cx - r, cy - r//2, r*2, r))
            pygame.draw.polygon(self.screen, (36, 46, 66),
                                [(cx, cy), (cx - r*2, cy - r//2), (cx - r, cy + r//3)])
            pygame.draw.polygon(self.screen, (36, 46, 66),
                                [(cx, cy), (cx + r*2, cy - r//2), (cx + r, cy + r//3)])

        # key label [A] / [D]
        lbl = self.font_sm.render(f"[{key}]", True, border_color)
        self.screen.blit(lbl, (cx - lbl.get_width()//2, rect.bottom + 5))

    def _hud_arrow(self, cx, cy, left):
        r = pygame.Rect(cx - 19, cy - 19, 38, 38)
        pygame.draw.rect(self.screen, (55, 65, 78), r, border_radius=7)
        pygame.draw.rect(self.screen, (110, 132, 155), r, 2, border_radius=7)
        if left:
            pts = [(cx - 9, cy), (cx + 7, cy - 8), (cx + 7, cy + 8)]
        else:
            pts = [(cx + 9, cy), (cx - 7, cy - 8), (cx - 7, cy + 8)]
        pygame.draw.polygon(self.screen, WHITE, pts)

    def _draw_bird_status(self, btn_rect, bird):
        """Draw HP hearts and ammo fish count below a bird button."""
        cx   = btn_rect.centerx
        base_y = btn_rect.bottom + 24   # just below the [key] label

        # HP hearts (♥)
        heart_col  = (220, 50, 50)  if bird.hit_flash == 0 else (255, 180, 180)
        empty_col  = (80, 30, 30)
        for i in range(bird.max_hp):
            hx = cx - (bird.max_hp * 14) // 2 + i * 14 + 7
            col = heart_col if i < bird.hp else empty_col
            s = self.font_sm.render("♥", True, col)
            self.screen.blit(s, (hx - s.get_width() // 2, base_y))

        # Ammo fish icons
        ammo_y = base_y + 18
        for i in range(max(bird.ammo, 0)):
            ax = cx - (bird.ammo * 12) // 2 + i * 12 + 6
            pygame.draw.ellipse(self.screen, (80, 210, 255),
                                (ax - 7, ammo_y - 4, 14, 8))
            pygame.draw.polygon(self.screen, (80, 210, 255),
                                [(ax + 7, ammo_y - 3), (ax + 11, ammo_y),
                                 (ax + 7, ammo_y + 3)])
        # [clic der] label only for pelican (osprey shows peck cooldown in special section)
        if bird is self.active_bird and bird.bird_type == 'pelican':
            f_lbl = self.font_sm.render("[clic der] dispara", True, (80, 220, 255))
            self.screen.blit(f_lbl, (cx - f_lbl.get_width() // 2, ammo_y + 12))

        # special ability cooldown / hint (always visible)
        if bird.bird_type == 'pelican':
            if bird.special_cooldown > 0:
                pct   = 1.0 - bird.special_cooldown / 360
                label = f"[Q] Ráfaga {int(pct*100)}%"
                col   = (200, 120, 40)
            else:
                label = "[Q] ¡RÁFAGA LISTA!"
                col   = (255, 220, 60)
            sp_lbl = self.font_sm.render(label, True, col)
            self.screen.blit(sp_lbl, (cx - sp_lbl.get_width() // 2, ammo_y + 30))
        else:
            # osprey: peck (right-click) + drill [E] cooldowns
            if bird.peck_cooldown > 0:
                pct    = 1.0 - bird.peck_cooldown / 180
                pk_lbl = self.font_sm.render(f"[clic] Peck {int(pct*100)}%", True, (100, 200, 255))
            else:
                pk_lbl = self.font_sm.render("[clic] ¡PECK LISTO!", True, (80, 230, 255))
            self.screen.blit(pk_lbl, (cx - pk_lbl.get_width() // 2, ammo_y + 12))
            if bird.special_cooldown > 0:
                pct      = 1.0 - bird.special_cooldown / 420
                dr_lbl   = self.font_sm.render(f"[E] Taladro {int(pct*100)}%", True, (255, 200, 50))
            else:
                dr_lbl   = self.font_sm.render("[E] ¡TALADRO LISTO!", True, (255, 230, 60))
            self.screen.blit(dr_lbl, (cx - dr_lbl.get_width() // 2, ammo_y + 30))
    def _draw_start_screen(self):
        # overlay
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 20, 45, 150))
        self.screen.blit(ov, (0, 0))

        # guide message
        if self.guide_messages:
            txt, _ = self.guide_messages[0]
            s = self.font_sm.render(txt, True, WHITE)
            self.screen.blit(s, (SCREEN_WIDTH//2 - s.get_width()//2, 24))

        # title
        t1 = self.font_lg.render("WINGS", True, WHITE)
        t2 = self.font_lg.render("& FISH", True, (255, 200, 40))
        self.screen.blit(t1, (80, 95))
        self.screen.blit(t2, (80, 168))

        # subtitle
        sub = self.font_title.render("Catch fish with seabirds!", True, WHITE)
        self.screen.blit(sub, (80, 255))

        # instructions
        for i, line in enumerate([
            "Toca PLAY para elegir entre modo libre y niveles",
            "WASD / Flechas: mover el ave  |  Clic izq/Espacio: zambullirse  |  Clic der: disparar",
            "Z: Pelicano se zambulle  |  X: Ave pescadora se zambulle",
            "Q: Ráfaga pelicano | Clic-der osprey: peck dive | E: ¡Taladro relámpago!",
        ]):
            s = self.font_sm.render(line, True, (195, 230, 255))
            self.screen.blit(s, (80, 318 + i * 28))

        # PLAY button
        pygame.draw.rect(self.screen, ORANGE, self.btn_play, border_radius=14)
        pygame.draw.rect(self.screen, (255, 205, 55), self.btn_play, 4, border_radius=14)
        pt = self.font_title.render("MODOS", True, WHITE)
        self.screen.blit(pt, (self.btn_play.centerx - pt.get_width()//2,
                               self.btn_play.centery - pt.get_height()//2))

        # shop + gear icons + item store
        pygame.draw.rect(self.screen, (180, 50, 50), self.btn_item_store, border_radius=10)
        pygame.draw.rect(self.screen, (255, 130, 130), self.btn_item_store, 2, border_radius=10)
        _tl2 = self.font_sm.render("TIENDA", True, (255, 255, 255))
        self.screen.blit(_tl2, (self.btn_item_store.centerx - _tl2.get_width()//2,
                                 self.btn_item_store.centery - _tl2.get_height()//2))
        self._icon_shop(self.btn_shop.centerx, self.btn_shop.centery, 16)
        self._icon_gear(self.btn_gear_left.centerx, self.btn_gear_left.centery, 16)

        # bird preview
        self.pelican.x, self.pelican.y = 760, 210
        self.osprey.x,  self.osprey.y  = 620, 160
        self.pelican.facing_right = False
        self.osprey.facing_right  = True
        self._draw_birds()

    def _draw_mode_select_screen(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 12, 30, 190))
        self.screen.blit(overlay, (0, 0))

        panel = pygame.Surface(self.mode_select_panel.size, pygame.SRCALPHA)
        panel.fill((8, 24, 42, 245))
        self.screen.blit(panel, self.mode_select_panel.topleft)
        pygame.draw.rect(self.screen, (95, 190, 220), self.mode_select_panel, 3, border_radius=18)

        title = self.font_lg.render("ELIGE TU MODO", True, WHITE)
        self.screen.blit(title, (self.mode_select_panel.centerx - title.get_width() // 2,
                                 self.mode_select_panel.y + 18))

        mouse_pos = pygame.mouse.get_pos()
        cards = [
            (self.btn_mode_free, (20, 92, 82), (80, 225, 175)),
            (self.btn_mode_levels, (35, 70, 125), (100, 190, 255)),
        ]
        for rect, color, border in cards:
            fill = tuple(min(255, channel + 18) for channel in color) if rect.collidepoint(mouse_pos) else color
            pygame.draw.rect(self.screen, fill, rect, border_radius=14)
            pygame.draw.rect(self.screen, border, rect, 3, border_radius=14)

        free_title = self.font_title.render("MODO LIBRE", True, (135, 245, 205))
        self.screen.blit(free_title, (self.btn_mode_free.centerx - free_title.get_width() // 2,
                                      self.btn_mode_free.y + 30))
        free_lines = ("Explora y pesca sin una ruta fija.",
                      "Juega las oleadas de siempre.",
                      "Jefes en las oleadas 10 y 25.")
        for index, line in enumerate(free_lines):
            text = self.font.render(line, True, WHITE)
            self.screen.blit(text, (self.btn_mode_free.centerx - text.get_width() // 2,
                                    self.btn_mode_free.y + 105 + index * 42))
        free_action = self.font_title.render("JUGAR LIBRE", True, WHITE)
        self.screen.blit(free_action, (self.btn_mode_free.centerx - free_action.get_width() // 2,
                                       self.btn_mode_free.bottom - 72))

        level_title = self.font_title.render("MODO NIVELES", True, (160, 205, 255))
        self.screen.blit(level_title, (self.btn_mode_levels.centerx - level_title.get_width() // 2,
                                       self.btn_mode_levels.y + 24))
        map_label = self.font_sm.render("AVANZA NIVEL POR NIVEL", True, WHITE)
        self.screen.blit(map_label, (self.btn_mode_levels.centerx - map_label.get_width() // 2,
                                    self.btn_mode_levels.y + 76))

        node_positions = []
        for level in range(1, 11):
            row = 0 if level <= 5 else 1
            col = level - 1 if row == 0 else 10 - level
            node_x = self.btn_mode_levels.x + 54 + col * (self.btn_mode_levels.w - 108) // 4
            node_y = self.btn_mode_levels.y + 160 + row * 84
            node_positions.append((node_x, node_y))
        for index in range(9):
            pygame.draw.line(self.screen, (110, 150, 195), node_positions[index],
                             node_positions[index + 1], 4)
        for level, (node_x, node_y) in enumerate(node_positions, start=1):
            is_boss = level == 10
            color = (245, 105, 75) if is_boss else (70, 155, 210)
            pygame.draw.circle(self.screen, (10, 25, 45), (node_x, node_y), 23)
            pygame.draw.circle(self.screen, color, (node_x, node_y), 20, 4 if is_boss else 0)
            node_text = self.font_sm.render("J" if is_boss else str(level), True, WHITE)
            self.screen.blit(node_text, (node_x - node_text.get_width() // 2,
                                         node_y - node_text.get_height() // 2))
        boss_label = self.font_sm.render("JEFE CADA 10 NIVELES", True, (255, 170, 125))
        self.screen.blit(boss_label, (self.btn_mode_levels.centerx - boss_label.get_width() // 2,
                                      self.btn_mode_levels.y + 360))
        level_action = self.font_title.render("COMENZAR CAMPAÑA", True, WHITE)
        self.screen.blit(level_action, (self.btn_mode_levels.centerx - level_action.get_width() // 2,
                                        self.btn_mode_levels.bottom - 72))

        pygame.draw.rect(self.screen, (70, 85, 100), self.btn_mode_back, border_radius=8)
        pygame.draw.rect(self.screen, (170, 190, 205), self.btn_mode_back, 2, border_radius=8)
        back_text = self.font_sm.render("VOLVER", True, WHITE)
        self.screen.blit(back_text, (self.btn_mode_back.centerx - back_text.get_width() // 2,
                                     self.btn_mode_back.centery - back_text.get_height() // 2))

    def _draw_tutorial_screen(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 12, 30, 200))
        self.screen.blit(overlay, (0, 0))
        panel = self.mode_select_panel
        pygame.draw.rect(self.screen, (8, 24, 42), panel, border_radius=18)
        pygame.draw.rect(self.screen, (95, 190, 220), panel, 3, border_radius=18)

        title = self.font_lg.render("TUTORIAL", True, WHITE)
        self.screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 24))
        lines = (
            "Mueve el ave con WASD o las flechas.",
            "Pulsa ESPACIO o clic izquierdo para zambullirte.",
            "Usa 1 y 2 para elegir pelícano o ave pescadora.",
            "Atrapa peces para ganar monedas y recuperar stamina.",
            "Esquiva los peces globo y derrota a los jefes.",
        )
        for index, line in enumerate(lines):
            text = self.font.render(line, True, (225, 240, 250))
            self.screen.blit(text, (panel.centerx - text.get_width() // 2,
                                    panel.y + 150 + index * 52))

        for rect, label, color in (
                (self.btn_tutorial_continue, "ELEGIR MODO", (25, 125, 90)),
                (self.btn_tutorial_skip, "SALTAR TUTORIAL", (60, 85, 110))):
            pygame.draw.rect(self.screen, color, rect, border_radius=9)
            pygame.draw.rect(self.screen, (180, 220, 230), rect, 2, border_radius=9)
            text = self.font_sm.render(label, True, WHITE)
            self.screen.blit(text, (rect.centerx - text.get_width() // 2,
                                    rect.centery - text.get_height() // 2))

    def _draw_level_select_screen(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 12, 30, 200))
        self.screen.blit(overlay, (0, 0))
        panel = self.mode_select_panel
        pygame.draw.rect(self.screen, (8, 24, 42), panel, border_radius=18)
        pygame.draw.rect(self.screen, (95, 190, 220), panel, 3, border_radius=18)

        title = self.font_lg.render("MAPA DE NIVELES", True, WHITE)
        self.screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 22))
        subtitle = self.font_sm.render(
            f"Nivel {self.unlocked_level} desbloqueado. Completa 5 oleadas para avanzar.",
            True, (195, 220, 235))
        self.screen.blit(subtitle, (panel.centerx - subtitle.get_width() // 2, panel.y + 88))

        for level, rect in self.level_button_rects.items():
            unlocked = level <= self.unlocked_level
            completed = level <= self.completed_level
            if completed:
                fill, border = (28, 105, 75), (90, 225, 155)
                status = "COMPLETADO"
            elif unlocked:
                fill, border = (30, 80, 135), (110, 195, 255)
                status = "JUGAR"
            else:
                fill, border = (40, 48, 58), (85, 95, 105)
                status = "BLOQUEADO"
            pygame.draw.rect(self.screen, fill, rect, border_radius=9)
            pygame.draw.rect(self.screen, border, rect, 3 if unlocked else 1, border_radius=9)
            label = self.font_sm.render(f"NIVEL {level}", True, WHITE if unlocked else (155, 160, 165))
            self.screen.blit(label, (rect.centerx - label.get_width() // 2, rect.y + 10))
            status_label = self.font_sm.render(status, True, border)
            self.screen.blit(status_label, (rect.centerx - status_label.get_width() // 2,
                                            rect.y + 38))

        pygame.draw.rect(self.screen, (70, 85, 100), self.btn_levels_back, border_radius=8)
        pygame.draw.rect(self.screen, (170, 190, 205), self.btn_levels_back, 2, border_radius=8)
        back_text = self.font_sm.render("VOLVER", True, WHITE)
        self.screen.blit(back_text, (self.btn_levels_back.centerx - back_text.get_width() // 2,
                                     self.btn_levels_back.centery - back_text.get_height() // 2))

    def _draw_level_complete_screen(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 12, 30, 210))
        self.screen.blit(overlay, (0, 0))
        panel = self.mode_select_panel
        pygame.draw.rect(self.screen, (8, 24, 42), panel, border_radius=18)
        pygame.draw.rect(self.screen, (100, 220, 155), panel, 3, border_radius=18)

        title = self.font_lg.render(f"¡NIVEL {self.completed_level} COMPLETADO!", True, (135, 245, 180))
        self.screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 115))
        if self.completed_level < len(self.level_button_rects):
            message = f"Nivel {self.completed_level + 1} desbloqueado"
        else:
            message = "¡Completaste todos los niveles disponibles!"
        subtitle = self.font_title.render(message, True, WHITE)
        self.screen.blit(subtitle, (panel.centerx - subtitle.get_width() // 2, panel.y + 235))

        pygame.draw.rect(self.screen, (25, 125, 90), self.btn_level_continue, border_radius=9)
        pygame.draw.rect(self.screen, (120, 230, 170), self.btn_level_continue, 2, border_radius=9)
        continue_text = self.font_sm.render("VOLVER AL MAPA", True, WHITE)
        self.screen.blit(continue_text, (self.btn_level_continue.centerx - continue_text.get_width() // 2,
                                         self.btn_level_continue.centery - continue_text.get_height() // 2))


    # ═══════════════════════════════════════
    #  SETTINGS PANEL
    # ═══════════════════════════════════════
    def _draw_settings_panel(self):
        pw, ph = 480, 440
        px = SCREEN_WIDTH  // 2 - pw // 2
        py = SCREEN_HEIGHT // 2 - ph // 2

        # dark overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        # main panel
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((15, 30, 55, 235))
        self.screen.blit(panel, (px, py))
        pygame.draw.rect(self.screen, (80, 160, 230), (px, py, pw, ph), 3, border_radius=16)

        # title bar
        pygame.draw.rect(self.screen, (30, 70, 130), (px, py, pw, 52), border_radius=16)
        title_surf = self.font_title.render("SETTINGS", True, WHITE)
        self.screen.blit(title_surf, (px + pw//2 - title_surf.get_width()//2, py + 10))

        # decorative gear in title
        self._icon_gear(px + 30, py + 26, 14)

        # CLOSE button  X
        close_rect = self.btn_close_settings
        close_rect.topleft = (px + pw - 46, py + 6)
        pygame.draw.rect(self.screen, (180, 50, 50), close_rect, border_radius=8)
        pygame.draw.rect(self.screen, (230, 90, 90), close_rect, 2, border_radius=8)
        x_txt = self.font.render("X", True, WHITE)
        self.screen.blit(x_txt, (close_rect.centerx - x_txt.get_width()//2,
                                  close_rect.centery - x_txt.get_height()//2))

        # ── CONTROLS section ─────────────────────
        iy = py + 68
        sect_font = pygame.font.Font(None, 26)
        sect_title = sect_font.render("CONTROLS", True, (130, 200, 255))
        self.screen.blit(sect_title, (px + 20, iy))
        pygame.draw.line(self.screen, (80, 130, 200),
                         (px + 20, iy + 22), (px + pw - 20, iy + 22), 1)
        iy += 32

        line_font = pygame.font.Font(None, 22)
        controls = [
            ("Arrow LEFT / RIGHT",  "Move the active bird horizontally"),
            ("Arrow UP",            "Fly upward / gain height"),
            ("Arrow DOWN",          "Descend toward the water"),
            ("A  key",              "Select PELICAN and dive"),
            ("D  key",              "Select OSPREY and dive"),
            ("SPACE  /  Click",     "Active bird dives"),
            ("ESC",                 "Return to previous screen"),
        ]
        for key_name, desc in controls:
            key_surf  = line_font.render(key_name, True, (255, 220, 80))
            desc_surf = line_font.render(desc,     True, (210, 230, 255))
            key_bg    = pygame.Rect(px + 16, iy - 2, 148, 22)
            pygame.draw.rect(self.screen, (35, 55, 90), key_bg, border_radius=4)
            pygame.draw.rect(self.screen, (70, 100, 160), key_bg, 1, border_radius=4)
            self.screen.blit(key_surf,  (px + 20, iy))
            self.screen.blit(desc_surf, (px + 174, iy))
            iy += 26

        # ── BIRDS section ────────────────────────
        iy += 8
        sect_title2 = sect_font.render("BIRDS", True, (130, 200, 255))
        self.screen.blit(sect_title2, (px + 20, iy))
        pygame.draw.line(self.screen, (80, 130, 200),
                         (px + 20, iy + 22), (px + pw - 20, iy + 22), 1)
        iy += 32

        birds_info = [
            ("PELICAN",  "[A]", "Slow, wide capture range. Gular pouch catches big fish."),
            ("OSPREY",   "[D]", "Fast, precise dive. Best for quick single-fish catches."),
        ]
        for name, key_tag, desc in birds_info:
            n_surf = line_font.render(f"{name}  {key_tag}", True, (255, 220, 80))
            d_surf = line_font.render(desc, True, (210, 230, 255))
            self.screen.blit(n_surf, (px + 20, iy))
            self.screen.blit(d_surf, (px + 20, iy + 20))
            iy += 48

        # ── footer ───────────────────────────────
        footer = line_font.render("Press ESC or click X to close", True, (150, 160, 180))
        self.screen.blit(footer, (px + pw//2 - footer.get_width()//2, py + ph - 28))

    # ═══════════════════════════════════════════
    #  SHOP PANEL
    # ═══════════════════════════════════════════
    def _draw_shop_panel(self):
        pw, ph = 500, 640
        px = SCREEN_WIDTH  // 2 - pw // 2
        py = SCREEN_HEIGHT // 2 - ph // 2

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        if self.active_bird.hp > 0 and self.shop_image_alive:
            bg_img = self.shop_image_alive
        elif self.active_bird.hp <= 0 and self.shop_image_dead:
            bg_img = self.shop_image_dead
        else:
            bg_img = None

        if bg_img:
            bg_surf = pygame.transform.scale(bg_img, (pw, ph))
            self.screen.blit(bg_surf, (px, py))
        else:
            panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
            panel.fill((20, 40, 15, 240))
            self.screen.blit(panel, (px, py))

        pygame.draw.rect(self.screen, (255, 215, 0), (px, py, pw, ph), 3, border_radius=16)

        # title bar
        pygame.draw.rect(self.screen, (60, 100, 20), (px, py, pw, 56), border_radius=16)
        title_surf = self.font_title.render("TIENDA DE MEJORAS", True, (255, 235, 80))
        self.screen.blit(title_surf, (px + pw//2 - title_surf.get_width()//2, py + 10))
        self._icon_shop(px + 32, py + 28, 12)

        # coins display
        coins_txt = self.font.render(f"Monedas: {self.caught_count}", True, (255, 215, 0))
        self.screen.blit(coins_txt, (px + pw - coins_txt.get_width() - 20, py + 66))

        # rebirth badge
        if self.rebirth_count > 0:
            rb_txt = self.font_sm.render(f"Renacimiento #{self.rebirth_count}", True, (255, 120, 255))
            self.screen.blit(rb_txt, (px + 16, py + 66))

        # close button
        self.btn_close_shop.topleft = (px + pw - 46, py + 8)
        pygame.draw.rect(self.screen, (180, 50, 50), self.btn_close_shop, border_radius=8)
        pygame.draw.rect(self.screen, (230, 90, 90), self.btn_close_shop, 2, border_radius=8)
        x_txt = self.font.render("X", True, WHITE)
        self.screen.blit(x_txt, (self.btn_close_shop.centerx - x_txt.get_width()//2,
                                  self.btn_close_shop.centery - x_txt.get_height()//2))

        upgrade_defs = [
            ('depth',    'Bucear más hondo',    'Niv.1-3: +70px / Niv.4-5: +70px más',      (80, 160, 230)),
            ('capacity', 'Máximo de peces',     'Nivel 1: 5 peces | Nivel 2: 8 | Nivel 3: 12', (80, 210, 120)),
            ('luck',     'Suerte pez dorado',   'Cada nivel: +20% chance pez dorado',         (255, 200, 0)),
            ('damage',   '¡Más daño!',         'Cada nivel: +1 daño. MAX = 1 tiro',         (255, 80,  80)),
            ('recovery', 'Recuperación',       'Cada nivel: +20% de energía máxima',         (120, 220, 120)),
        ]

        lf = pygame.font.Font(None, 24)
        sf = pygame.font.Font(None, 20)
        iy = py + 92
        for i, (key, name, desc, color) in enumerate(upgrade_defs):
            level = self.upgrades[key]
            card_rect = pygame.Rect(px + 16, iy, pw - 32, 96)
            pygame.draw.rect(self.screen, (30, 55, 22), card_rect, border_radius=10)
            pygame.draw.rect(self.screen, color, card_rect, 2, border_radius=10)

            # name
            n_surf = lf.render(name, True, WHITE)
            self.screen.blit(n_surf, (card_rect.x + 14, iy + 10))

            # level dots (max 5 total, grey if locked above current max_upgrade)
            for d in range(5):
                if d < level:
                    dot_color = color
                elif d < self.max_upgrade:
                    dot_color = (60, 60, 60)
                else:
                    dot_color = (35, 35, 35)   # locked (rebirth needed)
                dot_border = (200, 200, 200) if d < self.max_upgrade else (70, 70, 70)
                pygame.draw.circle(self.screen, dot_color,
                                   (card_rect.x + 14 + d * 22, iy + 36), 9)
                pygame.draw.circle(self.screen, dot_border,
                                   (card_rect.x + 14 + d * 22, iy + 36), 9, 1)
            # lock indicator on dots 4-5 before rebirth
            if self.max_upgrade < 5:
                lock_x = card_rect.x + 14 + 3 * 22 - 2
                lock_s = sf.render("[L]", True, (180, 100, 50))
                self.screen.blit(lock_s, (lock_x, iy + 26))

            d_surf = sf.render(desc, True, (180, 210, 180))
            self.screen.blit(d_surf, (card_rect.x + 14, iy + 54))

            # BUY button
            btn = self.shop_btns[i]
            btn.topleft = (card_rect.right - 184, iy + 24)
            if level >= self.max_upgrade:
                pygame.draw.rect(self.screen, (50, 50, 50), btn, border_radius=10)
                lbl = lf.render("MAX", True, (150, 150, 150))
            else:
                cost = self.upgrade_costs.get(key, [0, 0, 0, 0, 0])[level]
                can_afford = self.caught_count >= cost
                btn_color  = (40, 130, 55) if can_afford else (80, 50, 50)
                pygame.draw.rect(self.screen, btn_color, btn, border_radius=10)
                pygame.draw.rect(self.screen, color, btn, 2, border_radius=10)
                lbl = lf.render(f"Comprar  -{cost}", True,
                                WHITE if can_afford else (160, 100, 100))
            self.screen.blit(lbl, (btn.centerx - lbl.get_width()//2,
                                    btn.centery - lbl.get_height()//2))

            iy += 108

        # ── REBIRTH section ──────────────────────────
        iy += 6
        sep_y = iy
        pygame.draw.line(self.screen, (255, 120, 255),
                         (px + 16, sep_y), (px + pw - 16, sep_y), 1)
        iy += 8

        can_rb = self._can_rebirth()
        rb_bg  = (55, 15, 70) if can_rb else (30, 30, 40)
        rb_border = (255, 80, 255) if can_rb else (100, 60, 110)
        rb_card = pygame.Rect(px + 16, iy, pw - 32, 108)
        pygame.draw.rect(self.screen, rb_bg, rb_card, border_radius=12)
        pygame.draw.rect(self.screen, rb_border, rb_card, 2, border_radius=12)

        rb_title = lf.render("★  RENACIMIENTO  ★", True, (255, 130, 255) if can_rb else (120, 80, 130))
        self.screen.blit(rb_title, (rb_card.centerx - rb_title.get_width()//2, iy + 8))

        # requirements
        def req_line(text, ok):
            col = (120, 255, 120) if ok else (200, 100, 100)
            mark = "✓" if ok else "✗"
            return sf.render(f"{mark} {text}", True, col)

        r1 = req_line(f"5 cangrejos  ({self.crabs_caught_total}/5)",
                      self.crabs_caught_total >= 5)
        r2 = req_line(f"10 peces dorados  ({self.golden_caught_total}/10)",
                      self.golden_caught_total >= 10)
        r3 = req_line(f"50 monedas  ({self.caught_count}/50)",
                      self.caught_count >= 50)
        for j, rs in enumerate([r1, r2, r3]):
            self.screen.blit(rs, (rb_card.x + 14, iy + 30 + j * 20))

        # REBIRTH button
        self.btn_rebirth = pygame.Rect(rb_card.right - 148, iy + 18, 132, 72)
        if can_rb:
            pygame.draw.rect(self.screen, (130, 30, 160), self.btn_rebirth, border_radius=10)
            pygame.draw.rect(self.screen, (255, 80, 255), self.btn_rebirth, 2, border_radius=10)
            rb_lbl1 = lf.render("★ RENACER ★", True, WHITE)
            rb_lbl2 = sf.render("-50 monedas", True, (220, 160, 220))
            self.screen.blit(rb_lbl1, (self.btn_rebirth.centerx - rb_lbl1.get_width()//2,
                                        self.btn_rebirth.centery - 16))
            self.screen.blit(rb_lbl2, (self.btn_rebirth.centerx - rb_lbl2.get_width()//2,
                                        self.btn_rebirth.centery + 6))
        else:
            pygame.draw.rect(self.screen, (45, 35, 50), self.btn_rebirth, border_radius=10)
            rb_lbl = sf.render("Bloqueado", True, (110, 80, 120))
            self.screen.blit(rb_lbl, (self.btn_rebirth.centerx - rb_lbl.get_width()//2,
                                       self.btn_rebirth.centery - rb_lbl.get_height()//2))

        hint = sf.render("ESC o X para cerrar", True, (140, 150, 130))
        self.screen.blit(hint, (px + pw//2 - hint.get_width()//2, py + ph - 22))

    # ═══════════════════════════════════════════
    #  ITEM STORE PANEL
    # ═══════════════════════════════════════════
    def _draw_item_store_panel(self):
        pw, ph = 480, 530
        px = SCREEN_WIDTH  // 2 - pw // 2
        py = SCREEN_HEIGHT // 2 - ph // 2

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        if self.shop_image_alive:
            bg_surf = pygame.transform.scale(self.shop_image_alive, (pw, ph))
            panel.blit(bg_surf, (0, 0))
        else:
            panel.fill((40, 12, 12, 245))
        self.screen.blit(panel, (px, py))
        pygame.draw.rect(self.screen, (255, 100, 100), (px, py, pw, ph), 3, border_radius=16)

        # title bar
        pygame.draw.rect(self.screen, (120, 25, 25), (px, py, pw, 56), border_radius=16)
        title_surf = self.font_title.render("TIENDA", True, (255, 200, 200))
        self.screen.blit(title_surf, (px + pw//2 - title_surf.get_width()//2, py + 10))

        lf = pygame.font.Font(None, 24)
        sf = pygame.font.Font(None, 20)

        # coins display
        coins_txt = lf.render(f"Monedas: {self.caught_count}", True, (255, 215, 0))
        self.screen.blit(coins_txt, (px + 16, py + 66))

        # close button
        self.btn_close_item_store.topleft = (px + pw - 46, py + 8)
        pygame.draw.rect(self.screen, (180, 50, 50), self.btn_close_item_store, border_radius=8)
        pygame.draw.rect(self.screen, (230, 90, 90), self.btn_close_item_store, 2, border_radius=8)
        x_txt = self.font.render("X", True, (255, 255, 255))
        self.screen.blit(x_txt, (self.btn_close_item_store.centerx - x_txt.get_width()//2,
                                  self.btn_close_item_store.centery - x_txt.get_height()//2))

        items = [
            ("Curar Pelicano",       f"Vida completa ({self.pelican.max_hp} HP)",  15, (80, 160, 255),
             self.pelican.hp >= self.pelican.max_hp),
            ("Curar Ave Pescadora",  f"Vida completa ({self.osprey.max_hp} HP)",   10, (100, 220, 130),
             self.osprey.hp >= self.osprey.max_hp),
            ("Llenar Energia",       "Energia al maximo",                           20, (255, 220, 50),
             self.stamina >= self.max_stamina),
            ("Municion Extra",       "+10 balas al ave activa",                     5, (255, 140, 60),
             False),
            (f"1000 Gemas  ($5)",    f"\u00a1Llena el formulario!  \u2666 {self.gems} gemas",  5, (180, 80, 220),
             False),
        ]

        iy = py + 88
        for i, (name, desc, cost, color, maxed) in enumerate(items):
            card = pygame.Rect(px + 14, iy, pw - 28, 72)
            pygame.draw.rect(self.screen, (60, 18, 18), card, border_radius=10)
            pygame.draw.rect(self.screen, color, card, 2, border_radius=10)

            n_surf = lf.render(name, True, (255, 255, 255))
            self.screen.blit(n_surf, (card.x + 12, iy + 8))
            d_surf = sf.render(desc, True, (200, 200, 200))
            self.screen.blit(d_surf, (card.x + 12, iy + 36))

            btn = self.item_store_btns[i]
            btn.topleft = (card.right - 172, iy + 14)
            if maxed:
                pygame.draw.rect(self.screen, (50, 50, 50), btn, border_radius=8)
                lbl = sf.render("Ya al maximo", True, (130, 130, 130))
            elif self.caught_count >= cost:
                pygame.draw.rect(self.screen, (100, 30, 30), btn, border_radius=8)
                pygame.draw.rect(self.screen, color, btn, 2, border_radius=8)
                lbl = lf.render(f"Comprar  -{cost}", True, (255, 255, 255))
            else:
                pygame.draw.rect(self.screen, (50, 35, 35), btn, border_radius=8)
                lbl = sf.render(f"Faltan {cost - self.caught_count}", True, (180, 100, 100))
            self.screen.blit(lbl, (btn.centerx - lbl.get_width()//2,
                                    btn.centery - lbl.get_height()//2))
            iy += 84

        hint = sf.render("ESC o X para cerrar", True, (140, 130, 130))
        self.screen.blit(hint, (px + pw//2 - hint.get_width()//2, py + ph - 20))

    # ═══════════════════════════════════════════
    #  PURCHASE FORM helpers
    # ═══════════════════════════════════════════
    def _send_purchase_email(self, to_email, nombre, gems, cost_usd):
        """No-op placeholder so purchases don't fail on mail configuration errors."""
        return

    def _send_owner_notification(self, record, gems, cost_usd):
        """No-op placeholder so purchase notifications do not spam errors."""
        return

    def _pf_submit(self):
        """Process form submission — awards gems or unlocks rainbow skin."""
        record = {k: v for k, v in self._pf_fields.items()}
        record['id'] = len(self._pf_records) + 1
        self._pf_records.append(record)

        if self._pf_purchase_type == 'rainbow_pelican':
            # Unlock rainbow skin for BOTH birds (real $5 payment)
            self.unlocked_pelican.add(len(self.pelican_skins) - 1)
            self.unlocked_osprey.add(len(self.osprey_skins) - 1)
            self.pelican_skin_idx = len(self.pelican_skins) - 1
            self.osprey_skin_idx  = len(self.osprey_skins) - 1
            self._apply_skin()
            self._send_purchase_email(
                to_email = self._pf_fields.get('Correo', '').strip(),
                nombre   = self._pf_fields.get('Nombre', '').strip(),
                gems     = 0,
                cost_usd = 5,
            )
            self._send_owner_notification(
                record   = {k: v for k, v in self._pf_fields.items()},
                gems     = 0,
                cost_usd = 5,
            )
            for k in self._pf_fields:
                self._pf_fields[k] = ''
            self._pf_active = None
            self._pf_purchase_type = 'gems'
            self._add_message('\u00a1Skin Arcoiris desbloqueada! \U0001f308')
            self.state = GameState.SKINS
        else:
            # Default: award 1000 gems
            if self.caught_count < self._pf_pending_cost:
                self._add_message('\u00a1No tienes suficientes monedas!')
                return
            self.caught_count -= self._pf_pending_cost
            self.gems         += 1000
            self._send_purchase_email(
                to_email  = self._pf_fields.get('Correo', '').strip(),
                nombre    = self._pf_fields.get('Nombre', '').strip(),
                gems      = 1000,
                cost_usd  = 5,
            )
            self._send_owner_notification(
                record   = {k: v for k, v in self._pf_fields.items()},
                gems     = 1000,
                cost_usd = 5,
            )
            for k in self._pf_fields:
                self._pf_fields[k] = ''
            self._pf_active = None
            self._add_message(f'\u00a1Compraste 1000 Gemas! Total: {self.gems} gemas')
            self.state = GameState.ITEM_STORE

    # ═══════════════════════════════════════════
    #  PURCHASE FORM PANEL
    # ═══════════════════════════════════════════
    def _draw_purchase_form_panel(self):
        # dim background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 155))
        self.screen.blit(overlay, (0, 0))

        lf = pygame.font.Font(None, 24)
        sf = pygame.font.Font(None, 20)
        ff = pygame.font.Font(None, 22)

        # ── Tab navigation bar ───────────────────
        tabs    = ["Ventas", "Inventario", "Clientes", "Pedidos", "Proveedor", "Informacion"]
        panel_x = 15
        panel_y = 46
        panel_w = SCREEN_WIDTH - 30
        tab_h   = 34
        tab_w   = panel_w // len(tabs)

        for i, tab in enumerate(tabs):
            tx    = panel_x + i * tab_w
            trect = pygame.Rect(tx, panel_y, tab_w, tab_h)
            col   = (205, 218, 232) if tab == "Clientes" else (185, 200, 215)
            pygame.draw.rect(self.screen, col, trect)
            pygame.draw.rect(self.screen, (110, 128, 148), trect, 1)
            ts = lf.render(tab, True, BLACK)
            self.screen.blit(ts, (trect.centerx - ts.get_width()//2,
                                   trect.centery - ts.get_height()//2))

        content_y = panel_y + tab_h
        form_bg   = pygame.Rect(panel_x, content_y, panel_w,
                                SCREEN_HEIGHT - content_y - 14)
        pygame.draw.rect(self.screen, (210, 222, 235), form_bg)
        pygame.draw.rect(self.screen, (140, 155, 168), form_bg, 1)

        # ── Left groupbox "Clientes" ─────────────
        gb_w = 322
        gb   = pygame.Rect(panel_x + 6, content_y + 6, gb_w, form_bg.h - 12)
        pygame.draw.rect(self.screen, (196, 210, 225), gb)
        pygame.draw.rect(self.screen, (110, 130, 152), gb, 2)

        # Groupbox title strip
        gb_lbl = lf.render("Clientes", True, BLACK)
        gbl_x  = gb.x + 10
        gbl_y  = gb.y + 6
        pygame.draw.rect(self.screen, (196, 210, 225),
                         (gbl_x - 2, gbl_y, gb_lbl.get_width() + 4,
                          gb_lbl.get_height()))
        self.screen.blit(gb_lbl, (gbl_x, gbl_y))

        # ── Form fields ──────────────────────────
        field_order = ['Nombre', 'Cédula', 'Celular', 'Dirección', 'Correo']
        fx    = gb.x + 20
        fw    = gb.w - 40
        fh    = 26
        fy0   = gb.y + 32
        f_gap = 52

        self._pf_field_rects = {}
        for i2, fname in enumerate(field_order):
            fy  = fy0 + i2 * f_gap
            lbl = ff.render(fname + ":", True, BLACK)
            self.screen.blit(lbl, (fx, fy))
            inp = pygame.Rect(fx, fy + 17, fw, fh)
            self._pf_field_rects[fname] = inp
            active = (self._pf_active == fname)
            pygame.draw.rect(self.screen, WHITE, inp)
            pygame.draw.rect(self.screen,
                             (70, 130, 200) if active else (170, 185, 200),
                             inp, 2 if active else 1)
            val  = self._pf_fields[fname]
            vsrf = ff.render(val, True, BLACK)
            clip = self.screen.get_clip()
            self.screen.set_clip(inp)
            self.screen.blit(vsrf, (inp.x + 4, inp.y + 4))
            self.screen.set_clip(clip)
            # blinking cursor
            if active and (pygame.time.get_ticks() // 500) % 2 == 0:
                cx3 = min(inp.x + 4 + vsrf.get_width(), inp.right - 3)
                pygame.draw.line(self.screen, BLACK,
                                 (cx3, inp.y + 3), (cx3, inp.y + fh - 3), 1)

        # ── Ingresar / Modificar buttons ─────────
        btn_y2 = fy0 + len(field_order) * f_gap + 8
        self.btn_pf_ingresar  = pygame.Rect(fx,       btn_y2, 130, 34)
        self.btn_pf_modificar = pygame.Rect(fx + 148, btn_y2, 130, 34)
        for brect, blbl in [(self.btn_pf_ingresar, "Ingresar"),
                             (self.btn_pf_modificar, "Modificar")]:
            pygame.draw.rect(self.screen, (220, 220, 222), brect)
            pygame.draw.rect(self.screen, (100, 120, 145), brect, 2)
            bt = lf.render(blbl, True, BLACK)
            self.screen.blit(bt, (brect.centerx - bt.get_width()//2,
                                   brect.centery - bt.get_height()//2))

        # Gems info below buttons
        info_y = btn_y2 + 42
        g_lbl  = lf.render(f"\u2666 Tus Gemas: {self.gems}", True, (150, 50, 200))
        self.screen.blit(g_lbl, (fx, info_y))
        c_lbl  = sf.render("5 monedas  \u2192  +1000 Gemas", True, (70, 100, 160))
        self.screen.blit(c_lbl, (fx, info_y + 22))
        hint2  = sf.render("Clic en un campo y escribe con el teclado",
                           True, (90, 110, 130))
        self.screen.blit(hint2, (fx, info_y + 42))

        # ── Right table panel ────────────────────
        tbl_x  = panel_x + gb_w + 16
        tbl_y  = content_y + 6
        tbl_w  = panel_w - gb_w - 22
        tbl_h  = form_bg.h - 12
        tbl_bg = pygame.Rect(tbl_x, tbl_y, tbl_w, tbl_h)
        pygame.draw.rect(self.screen, WHITE, tbl_bg)
        pygame.draw.rect(self.screen, (190, 205, 218), tbl_bg, 1)

        # Column definitions (last col fills remaining width)
        col_defs = [('ID', 42), ('Nombre', 116), ('Cédula', 94),
                    ('Celular', 84), ('Dirección', 128), ('Correo', None)]
        used = sum(w for _, w in col_defs if w is not None)
        col_defs[-1] = ('Correo', max(58, tbl_w - used - 16))

        hdr_h2 = 24
        cx4    = tbl_x + 1
        for cname, cw in col_defs:
            hrect = pygame.Rect(cx4, tbl_y + 1, cw, hdr_h2)
            pygame.draw.rect(self.screen, (205, 218, 230), hrect)
            pygame.draw.rect(self.screen, (155, 170, 185), hrect, 1)
            ht = sf.render(cname, True, BLACK)
            self.screen.blit(ht, (hrect.centerx - ht.get_width()//2,
                                   hrect.centery - ht.get_height()//2))
            cx4 += cw

        row_y2 = tbl_y + 1 + hdr_h2
        row_h2 = 22
        for rec in self._pf_records:
            if row_y2 + row_h2 > tbl_y + tbl_h - 16:
                break
            cx4  = tbl_x + 1
            vals = [str(rec.get('id', '')), rec.get('Nombre', ''),
                    rec.get('Cédula', ''),  rec.get('Celular', ''),
                    rec.get('Dirección', ''), rec.get('Correo', '')]
            for j2, (cname, cw) in enumerate(col_defs):
                crect = pygame.Rect(cx4, row_y2, cw, row_h2)
                pygame.draw.rect(self.screen, WHITE, crect)
                pygame.draw.rect(self.screen, (200, 212, 224), crect, 1)
                vt = sf.render(str(vals[j2])[:15], True, BLACK)
                self.screen.blit(vt, (cx4 + 3, row_y2 + 3))
                cx4 += cw
            row_y2 += row_h2

        # Scrollbar decorations
        sb_x = tbl_x + tbl_w - 15
        pygame.draw.rect(self.screen, (210, 215, 222), (sb_x, tbl_y, 15, tbl_h))
        pygame.draw.rect(self.screen, (175, 182, 192), (sb_x, tbl_y, 15, tbl_h), 1)
        pygame.draw.rect(self.screen, (210, 215, 222),
                         (tbl_x, tbl_y + tbl_h - 15, tbl_w - 14, 15))
        pygame.draw.rect(self.screen, (175, 182, 192),
                         (tbl_x, tbl_y + tbl_h - 15, tbl_w - 14, 15), 1)

        # ── Close (X) button ─────────────────────
        self.btn_close_purchase_form.topleft = (SCREEN_WIDTH - 55, panel_y + 4)
        pygame.draw.rect(self.screen, (180, 50, 50),
                         self.btn_close_purchase_form, border_radius=6)
        x_txt = sf.render("X", True, WHITE)
        self.screen.blit(x_txt,
                         (self.btn_close_purchase_form.centerx - x_txt.get_width()//2,
                          self.btn_close_purchase_form.centery - x_txt.get_height()//2))

    # ═══════════════════════════════════════════
    #  ANIMATED MAIN MENU
    # ═══════════════════════════════════════════
    def _draw_menu(self):
        # ── sky background ─────────────────────
        sky_h = WATER_Y
        for y in range(sky_h):
            r = y / sky_h
            c = (int(SKY_TOP[0]*(1-r) + SKY_BOTTOM[0]*r),
                 int(SKY_TOP[1]*(1-r) + SKY_BOTTOM[1]*r),
                 int(SKY_TOP[2]*(1-r) + SKY_BOTTOM[2]*r))
            pygame.draw.line(self.screen, c, (0, y), (SCREEN_WIDTH, y))
        # ── water ──────────────────────────────
        for y in range(WATER_Y, SCREEN_HEIGHT):
            r = (y - WATER_Y) / (SCREEN_HEIGHT - WATER_Y)
            c = (int(WATER_SURFACE[0]*(1-r) + WATER_DEEP[0]*r),
                 int(WATER_SURFACE[1]*(1-r) + WATER_DEEP[1]*r),
                 int(WATER_SURFACE[2]*(1-r) + WATER_DEEP[2]*r))
            pygame.draw.line(self.screen, c, (0, y), (SCREEN_WIDTH, y))
        # wave line
        t = pygame.time.get_ticks() / 600.0
        wave_pts = []
        for wx in range(0, SCREEN_WIDTH + 10, 8):
            wy = WATER_Y + int(math.sin(wx / 55 + t) * 5)
            wave_pts.append((wx, wy))
        wave_pts += [(SCREEN_WIDTH, WATER_Y + 22), (0, WATER_Y + 22)]
        pygame.draw.polygon(self.screen, (200, 230, 255), wave_pts)
        for wx in range(0, SCREEN_WIDTH, 10):
            wy = WATER_Y + int(math.sin(wx / 55 + t) * 5)
            pygame.draw.circle(self.screen, WHITE, (wx, wy), 3)
        # sandy bottom
        pygame.draw.rect(self.screen, (185, 162, 100), (0, SCREEN_HEIGHT - 36, SCREEN_WIDTH, 36))
        pygame.draw.rect(self.screen, (210, 190, 130), (0, SCREEN_HEIGHT - 36, SCREEN_WIDTH, 7))
        # ── clouds ─────────────────────────────
        for nx, ny, sz, *_ in self.clouds:
            for ox, oy, cr in [(0, 0, sz), (sz//2, -10, sz-8), (sz, 0, sz-5)]:
                pygame.draw.circle(self.screen, WHITE, (int(nx+ox), int(ny+oy)), cr)
        # ── islands ────────────────────────────
        self._draw_island(155, WATER_Y, 115)
        self._draw_island(845, WATER_Y, 135)
        # ── demo fish ──────────────────────────
        for f in self._demo_fish:
            f.draw(self.screen)
        # ── demo birds (reuse existing Bird objects – no per-frame allocation) ──
        p_sk = self.pelican_skins[self.pelican_skin_idx]
        o_sk = self.osprey_skins[self.osprey_skin_idx]
        for bird, db, sk in [
                (self.pelican, self._demo_p, p_sk),
                (self.osprey,  self._demo_o, o_sk),
        ]:
            bird.x            = db['x']
            bird.y            = db['y']
            bird.vx           = 1.0 if db['facing_right'] else -1.0
            bird.vy           = db['vy']
            bird.frame        = db['frame']
            bird.facing_right = db['facing_right']
            bird.state        = db['state'] if db['state'] in ('flying', 'diving',
                                                                'underwater', 'rising') \
                                else 'flying'
            bird.body_color   = sk[1]
            bird.wing_color   = sk[2]
            bird.beak_color   = sk[3]
            bird.draw(self.screen)

        # ── title ──────────────────────────────
        # ── title ──────────────────────────────────
        t1  = self.font_menu_title.render("WINGS", True, WHITE)
        t2  = self.font_menu_title.render("& FISH", True, (255, 215, 40))
        sh1 = self.font_menu_title.render("WINGS", True, (0, 30, 80))
        sh2 = self.font_menu_title.render("& FISH", True, (120, 90, 0))
        self.screen.blit(sh1, (52, 42))
        self.screen.blit(sh2, (52, 132))
        self.screen.blit(t1,  (50, 40))
        self.screen.blit(t2,  (50, 130))
        sub = self.font_menu_sub.render("¡Pesca con tus aves!", True, (210, 240, 255))
        self.screen.blit(sub, (50, 232))

        # ── bottom menu bar ────────────────────────────
        bar_h = 100
        bar = pygame.Surface((SCREEN_WIDTH, bar_h), pygame.SRCALPHA)
        bar.fill((0, 15, 35, 195))
        self.screen.blit(bar, (0, SCREEN_HEIGHT - bar_h))

        conf = [
            (self.btn_menu_play,  (255, 140,  20), (255, 210,  80), "▶  JUGAR"),
            (self.btn_menu_shop,  ( 30, 120,  50), ( 80, 200, 110), "⬆  MEJORAS"),
            (self.btn_menu_store, (160,  40, 140), (220, 100, 200), "★  TIENDA"),
            (self.btn_menu_skins, ( 20,  90, 190), ( 80, 160, 255), "🎨  SKINS"),
        ]
        btn_font = self.font_menu_btn
        for brect, col, border, label in conf:
            pygame.draw.rect(self.screen, col, brect, border_radius=14)
            pygame.draw.rect(self.screen, border, brect, 3, border_radius=14)
            # hover glow
            mx2, my2 = pygame.mouse.get_pos()
            if brect.collidepoint(mx2, my2):
                glow = pygame.Surface((brect.w + 10, brect.h + 10), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*border, 80),
                                 (0, 0, brect.w + 10, brect.h + 10), border_radius=16)
                self.screen.blit(glow, (brect.x - 5, brect.y - 5))
            lt = btn_font.render(label, True, WHITE)
            self.screen.blit(lt, (brect.centerx - lt.get_width()//2,
                                   brect.centery - lt.get_height()//2))

        # ── active skin badge ──────────────────
        sf2 = self.font_menu_badge
        p_name = sf2.render(f"Pelicano: {p_sk[0]}", True, (200, 240, 200))
        o_name = sf2.render(f"Osprey: {o_sk[0]}",   True, (200, 210, 255))
        self.screen.blit(p_name, (10, SCREEN_HEIGHT - bar_h - 30))
        self.screen.blit(o_name, (10, SCREEN_HEIGHT - bar_h - 12))

        pygame.display.flip()

    # ═══════════════════════════════════════════
    #  SKINS PANEL
    # ═══════════════════════════════════════════
    def _draw_skins_panel(self):
        # draw live game world behind panel
        self._draw_background()
        self._draw_water()

        # semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 20, 180))
        self.screen.blit(overlay, (0, 0))

        pw, ph = 660, 520
        px = SCREEN_WIDTH  // 2 - pw // 2
        py = SCREEN_HEIGHT // 2 - ph // 2

        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((12, 25, 50, 245))
        self.screen.blit(panel, (px, py))
        pygame.draw.rect(self.screen, (80, 160, 255), (px, py, pw, ph), 3, border_radius=18)

        # title bar
        pygame.draw.rect(self.screen, (20, 55, 120), (px, py, pw, 54), border_radius=18)
        tf = pygame.font.Font(None, 50)
        ts = tf.render("SKINS DE AVES", True, (180, 220, 255))
        self.screen.blit(ts, (px + pw//2 - ts.get_width()//2, py + 10))

        # close button
        self.btn_close_skins.topleft = (px + pw - 46, py + 8)
        pygame.draw.rect(self.screen, (180, 50, 50), self.btn_close_skins, border_radius=8)
        xf = pygame.font.Font(None, 30)
        xt = xf.render("X", True, WHITE)
        self.screen.blit(xt, (self.btn_close_skins.centerx - xt.get_width()//2,
                               self.btn_close_skins.centery - xt.get_height()//2))

        # tabs
        tab_y = py + 62
        tab_w = 140
        self.btn_skins_tab_p.topleft = (px + 16, tab_y)
        self.btn_skins_tab_o.topleft = (px + 16 + tab_w + 10, tab_y)
        for btn, label, bird_t in [
                (self.btn_skins_tab_p, 'Pelicano', 'pelican'),
                (self.btn_skins_tab_o, 'Osprey',   'osprey'),
        ]:
            active = (self.skins_tab == bird_t)
            col    = (40, 100, 200) if active else (30, 50, 90)
            border = (120, 190, 255) if active else (60, 90, 140)
            pygame.draw.rect(self.screen, col, btn, border_radius=10)
            pygame.draw.rect(self.screen, border, btn, 2, border_radius=10)
            lf2 = pygame.font.Font(None, 26)
            lt2 = lf2.render(label, True, WHITE if active else (160, 180, 210))
            self.screen.blit(lt2, (btn.centerx - lt2.get_width()//2,
                                    btn.centery - lt2.get_height()//2))

        # skin grid (2 columns x 3 rows)
        skins_list = (self.pelican_skins if self.skins_tab == 'pelican'
                      else self.osprey_skins)
        sel_idx    = (self.pelican_skin_idx if self.skins_tab == 'pelican'
                      else self.osprey_skin_idx)

        card_w, card_h = 188, 110
        cols, rows = 3, 3
        grid_x = px + (pw - cols * card_w - (cols-1)*12) // 2
        grid_y = tab_y + 46

        self._skin_card_rects = []
        nf = pygame.font.Font(None, 24)
        sf3 = pygame.font.Font(None, 18)
        bf = pygame.font.Font(None, 17)
        for i, skin in enumerate(skins_list):
            sname, bcol, wcol, bkcol = skin[0], skin[1], skin[2], skin[3]
            luck_b, fish_b, dmg_b, sta_b, fx_type = skin[4], skin[5], skin[6], skin[7], skin[8]
            col_i = i % cols
            row_i = i // cols
            cx2 = grid_x + col_i * (card_w + 12)
            cy2 = grid_y + row_i * (card_h + 10)
            crect = pygame.Rect(cx2, cy2, card_w, card_h)
            self._skin_card_rects.append(crect)

            selected = (i == sel_idx)
            # card background and border color per effect
            _card_theme = {
                'fire':    ((80,30,0),   (255,140,0),  (50,18,0),  (180,80,0)  ),
                'water':   ((0,30,70),   (60,160,255), (0,18,50),  (30,100,200)),
                'stars':   ((30,10,60),  (200,100,255),(18,6,40),  (120,50,200)),
                'leaves':  ((10,45,10),  (80,220,60),  (6,28,6),   (40,140,30) ),
                'gold':    ((60,50,0),   (255,210,0),  (40,30,0),  (180,140,0) ),
                'silver':  ((30,40,55),  (200,220,255),(18,25,38), (120,145,180)),
                'rainbow': ((40,0,60),   (255,80,200), (22,0,40),  (160,40,140)),
            }
            if fx_type and fx_type in _card_theme:
                th = _card_theme[fx_type]
                bg  = th[0] if selected else th[2]
                brd = th[1] if selected else th[3]
            else:
                bg  = (30, 65, 120) if selected else (18, 35, 65)
                brd = (120, 220, 255) if selected else (50, 80, 130)
            pygame.draw.rect(self.screen, bg, crect, border_radius=12)
            pygame.draw.rect(self.screen, brd, crect, 3 if selected else 1, border_radius=12)

            # particle sparkles on effect skin cards
            if fx_type:
                _part_colors = {
                    'fire':   [(255,80,0,170),(255,160,0,150),(255,220,60,110)],
                    'water':  [(60,140,255,160),(120,200,255,130),(180,230,255,100)],
                    'stars':  [(200,140,255,160),(255,200,255,130),(255,255,255,180)],
                    'leaves': [(60,200,60,160),(100,240,70,130),(160,255,90,110)],
                    'gold':   [(255,220,0,180),(255,200,50,150),(255,240,120,120)],
                    'silver': [(200,220,255,180),(220,240,255,150),(255,255,255,200)],
                }
                if fx_type == 'rainbow':
                    for _ in range(5):
                        rx2 = cx2 + random.randint(10, card_w - 10)
                        ry2 = cy2 + random.randint(10, card_h - 10)
                        rr2 = random.randint(2, 6)
                        rh2 = random.randint(0, 359)
                        rc4, gc4, bc4 = colorsys.hsv_to_rgb(rh2/360, 1.0, 1.0)
                        rs2 = pygame.Surface((rr2*2, rr2*2), pygame.SRCALPHA)
                        pygame.draw.circle(rs2, (int(rc4*255), int(gc4*255), int(bc4*255), 180),
                                           (rr2, rr2), rr2)
                        self.screen.blit(rs2, (rx2 - rr2, ry2 - rr2))
                else:
                    pcols = _part_colors.get(fx_type, [])
                    if pcols:
                        for _ in range(4):
                            fx2 = cx2 + random.randint(10, card_w - 10)
                            fy2 = cy2 + random.randint(10, card_h - 10)
                            fr2 = random.randint(2, 5)
                            fc  = random.choice(pcols)
                            ps2 = pygame.Surface((fr2*2, fr2*2), pygame.SRCALPHA)
                            pygame.draw.circle(ps2, fc, (fr2, fr2), fr2)
                            self.screen.blit(ps2, (fx2 - fr2, fy2 - fr2))

            # mini bird preview
            mcx = cx2 + card_w // 2
            mcy = cy2 + card_h // 2 - 14
            env = 42
            if fx_type == 'rainbow':
                import time as _time
                _t = int(_time.time() * 80 + i * 60) % 360
                rb2, gb2, bb2  = colorsys.hsv_to_rgb(_t/360, 0.9, 1.0)
                rw2, gw2, bw2  = colorsys.hsv_to_rgb((_t+120)%360/360, 0.9, 1.0)
                rbk2,gbk2,bbk2 = colorsys.hsv_to_rgb((_t+240)%360/360, 0.9, 1.0)
                _body_c = (int(rb2*255),  int(gb2*255),  int(bb2*255))
                _wing_c = (int(rw2*255),  int(gw2*255),  int(bw2*255))
                _beak_c = (int(rbk2*255), int(gbk2*255), int(bbk2*255))
            else:
                _body_c, _wing_c, _beak_c = bcol, wcol, bkcol
            body_pts = [(mcx + int(math.cos(2*math.pi*j/14)*env*0.38),
                         mcy + int(math.sin(2*math.pi*j/14)*env*0.19))
                        for j in range(14)]
            pygame.draw.polygon(self.screen, _body_c, body_pts)
            wL = [(mcx, mcy),
                  (mcx - int(env*0.75), mcy - int(env*0.22)),
                  (mcx - int(env*0.52), mcy + int(env*0.06))]
            wR = [(mcx, mcy),
                  (mcx + int(env*0.75), mcy - int(env*0.22)),
                  (mcx + int(env*0.52), mcy + int(env*0.06))]
            pygame.draw.polygon(self.screen, _wing_c, wL)
            pygame.draw.polygon(self.screen, _wing_c, wR)
            beak = [(mcx + int(env*0.30), mcy - int(env*0.05)),
                    (mcx + int(env*0.58), mcy + int(env*0.04)),
                    (mcx + int(env*0.58), mcy - int(env*0.12))]
            pygame.draw.polygon(self.screen, _beak_c, beak)

            # name
            _name_col = {
                'fire': (255,180,0), 'water': (120,210,255), 'stars': (220,160,255),
                'leaves': (120,255,100), 'gold': (255,230,60), 'silver': (210,230,255),
                'rainbow': (255,120,255),
            }
            name_color = _name_col.get(fx_type, WHITE if selected else (160, 195, 240))
            nt = nf.render(sname, True, name_color)
            self.screen.blit(nt, (crect.centerx - nt.get_width()//2, cy2 + card_h - 32))

            # bonus line
            if dmg_b > 0:
                pct = int(dmg_b * 100)
                bonus_txt = f"+{pct}% dano  +{pct}% stamina  +{fish_b} pez"
                bonus_col = _name_col.get(fx_type, (120, 230, 120))
                bt2 = bf.render(bonus_txt, True, bonus_col)
                self.screen.blit(bt2, (crect.centerx - bt2.get_width()//2, cy2 + card_h - 16))

            _active_col = {
                'fire': (255,140,0), 'water': (80,200,255), 'stars': (200,100,255),
                'leaves': (80,220,60), 'gold': (255,210,0), 'silver': (190,215,255),
                'rainbow': (255,100,255),
            }
            if selected:
                et = sf3.render("ACTIVO", True, _active_col.get(fx_type, (100, 255, 150)))
                self.screen.blit(et, (crect.centerx - et.get_width()//2, cy2 + 4))
            else:
                unlocked = (self.unlocked_pelican if self.skins_tab == 'pelican'
                            else self.unlocked_osprey)
                cost = skin[9]
                if i in unlocked:
                    et = sf3.render("Equipar", True, (180, 220, 255))
                    self.screen.blit(et, (crect.centerx - et.get_width()//2, cy2 + 4))
                elif cost == -5:
                    pt = sf3.render("COMPRAR  $5 USD", True, (255, 200, 255))
                    self.screen.blit(pt, (crect.centerx - pt.get_width()//2, cy2 + 4))
                else:
                    can_buy = self.caught_count >= cost
                    price_col = (80, 220, 120) if can_buy else (200, 80, 80)
                    pt = sf3.render(f"{cost} monedas", True, price_col)
                    self.screen.blit(pt, (crect.centerx - pt.get_width()//2, cy2 + 4))
                    if not can_buy:
                        dim = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
                        dim.fill((0, 0, 0, 90))
                        self.screen.blit(dim, (cx2, cy2))

        # monedas disponibles
        coins_txt = sf3.render(f"Tus monedas: {self.caught_count} 🐟", True, (255, 230, 100))
        self.screen.blit(coins_txt, (px + 14, py + ph - 22))
        # hint
        ht = sf3.render("Clic para comprar/equipar  |  ESC para volver", True, (120, 150, 190))
        self.screen.blit(ht, (px + pw//2 - ht.get_width()//2 + 40, py + ph - 22))

        pygame.display.flip()

    # ═══════════════════════════════════════════
    #  GAME OVER SCREEN
    # ═══════════════════════════════════════════
    def _draw_game_over(self):
        # dim the background
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 185))
        self.screen.blit(overlay, (0, 0))

        cx = SCREEN_WIDTH // 2

        # ── "SIN ENERGÍA" title ────────────────
        title = self.font_lg.render("SIN ENERGÍA", True, (255, 80, 60))
        self.screen.blit(title, (cx - title.get_width() // 2, 170))

        # ── fish count ─────────────────────────
        count_txt = self.font_title.render(
            f"¡Atrapaste {self.caught_count} pescado{'s' if self.caught_count != 1 else ''}!",
            True, (255, 220, 60))
        self.screen.blit(count_txt, (cx - count_txt.get_width() // 2, 268))

        # ── decorative fish icons ──────────────
        for i, ox in enumerate([-80, 0, 80]):
            self._icon_fish(cx + ox, 340)

        # ── helper to draw a button ────────────
        def draw_btn(rect, color, border_color, label):
            pygame.draw.rect(self.screen, color,        rect, border_radius=14)
            pygame.draw.rect(self.screen, border_color, rect, 3, border_radius=14)
            s = self.font_sm.render(label, True, WHITE)
            self.screen.blit(s, (rect.centerx - s.get_width() // 2,
                                  rect.centery - s.get_height() // 2))

        draw_btn(self.btn_retry,     (40, 130, 55),  (80, 210, 100),  "Volverle a intentar")
        draw_btn(self.btn_restart,   (30,  80, 160), (80, 150, 230),  "Volver a empezar")
        draw_btn(self.btn_quit_game, (160, 40,  40), (230, 90,  90),  "Salir del juego")

        # ── hint ──────────────────────────────
        hint = self.font_sm.render(
            '"Intentar" mantiene tu puntaje  ·  "Empezar" lo reinicia a 0',
            True, (180, 190, 210))
        self.screen.blit(hint, (cx - hint.get_width() // 2, 570))


def main():
    """Start the game when the script is executed directly."""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()


# ═════════════