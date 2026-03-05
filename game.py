import pygame
import math
import random
import sys
from enum import Enum

pygame.init()

SCREEN_WIDTH  = 1000
SCREEN_HEIGHT = 700
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


# ═══════════════════════════════════════════════════════════════════════════
#  GAME STATE
# ═══════════════════════════════════════════════════════════════════════════
class GameState(Enum):
    START      = 1
    FLYING     = 2
    DIVING     = 3
    UNDERWATER = 4
    RISING     = 5
    SETTINGS   = 6


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
        flip = self.vx >= 0

        pygame.draw.ellipse(screen, self.color,
                            (cx - r, cy - r // 2, r * 2, r))
        wobble = math.sin(self.frame * 0.18) * 3
        if flip:
            pts = [(cx + r, cy - r//3 + wobble),
                   (cx + r + r//2, cy + wobble * 1.4),
                   (cx + r, cy + r//3 + wobble)]
        else:
            pts = [(cx - r, cy - r//3 + wobble),
                   (cx - r - r//2, cy + wobble * 1.4),
                   (cx - r, cy + r//3 + wobble)]
        pygame.draw.polygon(screen, self.color, [(int(a), int(b)) for a, b in pts])

        ex = cx + (r // 3 if flip else -r // 3)
        ey = cy - r // 6
        pygame.draw.circle(screen, WHITE, (ex, ey), max(3, r // 4))
        pygame.draw.circle(screen, BLACK, (ex, ey), max(1, r // 7))


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
        'pelican': dict(speed=3.5, dive_speed=9,  capture_radius=48, wingspan=95),
        'osprey':  dict(speed=5.0, dive_speed=13, capture_radius=32, wingspan=78),
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
        self.angle          = 0.0
        self.frame          = 0
        self.caught_fish    = None
        self.facing_right   = True
        # Visual colors
        pal = self._COLORS[bird_type]
        self.body_color = pal['body']
        self.wing_color = pal['wing']
        self.beak_color = pal['beak']

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

        if self.state == 'flying':
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
                self.vy = self.dive_speed * 0.3

        elif self.state == 'underwater':
            self.x += self.vx
            self.y += self.vy
            self.vy *= 0.91
            self.y   = min(self.y, SCREEN_HEIGHT - 20)

        elif self.state == 'rising':
            self.x += self.vx
            self.y += self.vy
            self.vy -= 0.55
            if self.y < WATER_Y - 25:
                self.state = 'flying'
                self.vy = -2.0

        # visual angle
        if abs(self.vx) > 0.1 or abs(self.vy) > 0.1:
            self.angle = math.atan2(self.vy, max(0.01, abs(self.vx)))
        if abs(self.vx) > 0.05:
            self.facing_right = self.vx >= 0

    # ── draw ──────────────────────────────────────
    def draw(self, screen):
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
        beak_pts = [rot( env*0.30, -env*0.05),
                    rot( env*0.58,  env*0.04),
                    rot( env*0.58, -env*0.12)]
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
#  GAME CLASS
# ═══════════════════════════════════════════════════════════════════════════
class Game:
    def __init__(self):
        self.screen     = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Wings & Fish")
        self.clock      = pygame.time.Clock()
        self.font       = pygame.font.Font(None, 36)
        self.font_sm    = pygame.font.Font(None, 24)
        self.font_lg    = pygame.font.Font(None, 80)
        self.font_title = pygame.font.Font(None, 52)

        self.state = GameState.START

        # ── optional background image ────────────
        self.bg_image = None
        try:
            img = pygame.image.load('background.png')
            self.bg_image = pygame.transform.scale(
                img.convert(), (SCREEN_WIDTH, SCREEN_HEIGHT))
            print("background.png loaded")
        except Exception as e:
            print(f"No background.png: {e}")

        # ── birds ────────────────────────────────
        self.pelican     = Bird('pelican', 260, 260)
        self.osprey      = Bird('osprey',  720, 190)
        self.active_bird = self.pelican

        # ── fish ─────────────────────────────────
        self.fish_list = [Fish() for _ in range(14)]

        # ── HUD ──────────────────────────────────
        self.caught_count = 0
        self.stamina      = 100.0
        self.max_stamina  = 100.0

        self.guide_messages = []
        self._add_message("Chris: Press Play to begin the game.")

        # ── floating +1 labels ───────────────────
        self.floaters = []

        # ── input ────────────────────────────────
        self.keys = {
            pygame.K_UP:    False,
            pygame.K_DOWN:  False,
            pygame.K_LEFT:  False,
            pygame.K_RIGHT: False,
        }

        # ── HUD rects ────────────────────────────
        self.btn_play           = pygame.Rect(SCREEN_WIDTH - 200, 18, 178, 58)
        self.btn_pelican        = pygame.Rect(18,  SCREEN_HEIGHT - 132, 110, 110)
        self.btn_osprey         = pygame.Rect(SCREEN_WIDTH - 128, SCREEN_HEIGHT - 132, 110, 110)
        self.btn_gear           = pygame.Rect(SCREEN_WIDTH - 58, 10, 48, 48)   # right gear
        self.btn_gear_left      = pygame.Rect(10, 10, 48, 48)                  # left gear (settings)
        self.prev_state         = GameState.FLYING   # state to restore when closing settings
        self.btn_close_settings = pygame.Rect(SCREEN_WIDTH//2 + 210, SCREEN_HEIGHT//2 - 220, 40, 40)

        # ── animated clouds ──────────────────────
        self.clouds = [(random.randint(0, SCREEN_WIDTH),
                        random.randint(30, 120),
                        random.randint(25, 55),
                        random.uniform(0.2, 0.6))
                       for _ in range(5)]

    # ── helpers ──────────────────────────────────
    def _add_message(self, text, duration=260):
        self.guide_messages = [(text, duration)]

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

                # ESC closes settings or returns to start
                if ev.key == pygame.K_ESCAPE:
                    if self.state == GameState.SETTINGS:
                        self.state = self.prev_state
                    else:
                        self.state = GameState.START

                if self.state == GameState.SETTINGS:
                    continue

                if ev.key == pygame.K_SPACE:
                    self._dive(self.active_bird)

                if ev.key == pygame.K_a:
                    self.active_bird = self.pelican
                    self._dive(self.pelican)
                    self._add_message("Martin: Pelican dives for big fish!")

                if ev.key == pygame.K_d:
                    self.active_bird = self.osprey
                    self._dive(self.osprey)
                    self._add_message("Martin: Osprey dives with precision!")

            if ev.type == pygame.KEYUP:
                if ev.key in self.keys:
                    self.keys[ev.key] = False

            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = pygame.mouse.get_pos()

                # ── SETTINGS screen ──────────────────────
                if self.state == GameState.SETTINGS:
                    if self.btn_close_settings.collidepoint(mx, my):
                        self.state = self.prev_state
                    return True

                # ── left gear button → open settings ─────
                if self.btn_gear_left.collidepoint(mx, my):
                    self.prev_state = self.state if self.state != GameState.START else GameState.FLYING
                    self.state = GameState.SETTINGS
                    return True

                if self.state == GameState.START:
                    if self.btn_play.collidepoint(mx, my):
                        self._start_game()
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

    def _start_game(self):
        self.state             = GameState.FLYING
        self.pelican.x, self.pelican.y = 260, 260
        self.osprey.x,  self.osprey.y  = 720, 190
        self.pelican.state = 'flying'
        self.osprey.state  = 'flying'
        self.pelican.vx = self.pelican.vy = 0
        self.osprey.vx  = self.osprey.vy  = 0
        self._add_message("Martin: Use arrows to fly! A=pelican dive, D=osprey dive")

    def _dive(self, bird):
        if self.state != GameState.FLYING:
            return
        if self.stamina < 15:
            self._add_message("Chris: The bird needs to rest! Low energy.")
            return
        if bird.start_dive():
            self.stamina -= 20
            self.state    = GameState.DIVING

    # ═══════════════════════════════════════════
    #  UPDATE
    # ═══════════════════════════════════════════
    def update(self):
        if self.state in (GameState.START, GameState.SETTINGS):
            # clouds still move on menu/settings screens
            self._update_clouds()
            return

        # ── arrow keys → move active bird ────────
        dx = dy = 0
        if self.keys[pygame.K_LEFT]:  dx -= 1
        if self.keys[pygame.K_RIGHT]: dx += 1
        if self.keys[pygame.K_UP]:    dy -= 1
        if self.keys[pygame.K_DOWN]:  dy += 1
        self.active_bird.move(dx, dy)

        # ── update birds ─────────────────────────
        self.pelican.update()
        self.osprey.update()

        # ── stamina recharges while flying ───────
        if self.state == GameState.FLYING:
            self.stamina = min(self.max_stamina, self.stamina + 0.18)

        # ── update fish ──────────────────────────
        for fish in self.fish_list:
            if fish.alive:
                fish.update()

        # ── state machine ────────────────────────
        if self.state == GameState.DIVING:
            bird = self.active_bird
            if bird.state == 'underwater':
                self.state = GameState.UNDERWATER

        elif self.state == GameState.UNDERWATER:
            bird = self.active_bird
            captured = False
            for fish in self.fish_list:
                if not fish.alive:
                    continue
                dist = math.hypot(bird.x - fish.x, bird.y - fish.y)
                if dist < bird.capture_radius + fish.radius:
                    fish.alive        = False
                    bird.caught_fish  = fish
                    bird.state        = 'rising'
                    bird.vy           = -bird.dive_speed * 0.75
                    self.caught_count += 1
                    self._add_floater(bird.x, bird.y - 30)
                    self._add_message(f"Chris: Great catch! Fish: {self.caught_count}")
                    self.state        = GameState.RISING
                    self.fish_list.append(Fish())
                    captured = True
                    break

            # no fish caught → surface if deep enough
            if not captured and bird.state == 'underwater' and bird.y > WATER_Y + 90:
                bird.state = 'rising'
                bird.vy    = -bird.dive_speed * 0.5
                self.state = GameState.RISING

        elif self.state == GameState.RISING:
            bird = self.active_bird
            if bird.state == 'flying':
                bird.caught_fish = None
                self.state       = GameState.FLYING

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
        for nx, ny, sz, vx in self.clouds:
            nx += vx
            if nx > SCREEN_WIDTH + sz * 2:
                nx = -sz * 2
            updated.append((nx, ny, sz, vx))
        self.clouds = updated

    # ═══════════════════════════════════════════
    #  DRAW
    # ═══════════════════════════════════════════
    def draw(self):
        self._draw_background()
        if self.state not in (GameState.START, GameState.SETTINGS):
            self._draw_water()

        self._draw_fish()
        self._draw_birds()
        self._draw_floaters()

        if self.state == GameState.START:
            self._draw_start_screen()
        elif self.state == GameState.SETTINGS:
            self._draw_hud()
            self._draw_settings_panel()
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
        for nx, ny, sz, _ in self.clouds:
            for ox, oy, r in [(0, 0, sz), (sz//2, -10, sz-8), (sz, 0, sz-5)]:
                pygame.draw.circle(self.screen, WHITE, (int(nx+ox), int(ny+oy)), r)

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

    def _draw_fish(self):
        for fish in self.fish_list:
            fish.draw(self.screen)

    def _draw_birds(self):
        for bird in [self.pelican, self.osprey]:
            bird.draw(self.screen)

    def _draw_floaters(self):
        for f in self.floaters:
            alpha = min(255, int(255 * f['t'] / 90))
            surf  = self.font.render(f['txt'], True, (255, 220, 50))
            surf.set_alpha(alpha)
            self.screen.blit(surf, (int(f['x']), int(f['y'])))

    # ═══════════════════════════════════════════
    #  HUD
    # ═══════════════════════════════════════════
    def _draw_hud(self):
        # dark top band
        band = pygame.Surface((SCREEN_WIDTH, 78), pygame.SRCALPHA)
        band.fill((0, 0, 0, 155))
        self.screen.blit(band, (0, 0))

        # ── fish icon + counter ──────────────────
        self._icon_fish(46, 38)
        txt = self.font.render(str(self.caught_count), True, WHITE)
        self.screen.blit(txt, (75, 22))

        # ── lightning + stamina bar ──────────────
        self._icon_lightning(148, 25, 30)
        bx, by, bw, bh = 185, 24, 320, 30
        pygame.draw.rect(self.screen, (60, 20, 10), (bx, by, bw, bh), border_radius=6)
        fill = int(bw * self.stamina / self.max_stamina)
        if fill > 0:
            pygame.draw.rect(self.screen, ORANGE,
                             (bx, by, fill, bh), border_radius=6)
        pygame.draw.rect(self.screen, (180, 80, 20), (bx, by, bw, bh), 2, border_radius=6)

        # ── right gear icon ──────────────────────
        self._icon_gear(SCREEN_WIDTH - 34, 34, 22)
        # ── left gear icon (settings) ─────────────
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

    # ═══════════════════════════════════════════
    #  START SCREEN
    # ═══════════════════════════════════════════
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
            "Arrow keys: fly the active bird",
            "A: Pelican dives  |  D: Osprey dives",
            "Space / Click: active bird dives",
        ]):
            s = self.font_sm.render(line, True, (195, 230, 255))
            self.screen.blit(s, (80, 318 + i * 28))

        # PLAY button
        pygame.draw.rect(self.screen, ORANGE, self.btn_play, border_radius=14)
        pygame.draw.rect(self.screen, (255, 205, 55), self.btn_play, 4, border_radius=14)
        pt = self.font_title.render("PLAY", True, WHITE)
        self.screen.blit(pt, (self.btn_play.centerx - pt.get_width()//2,
                               self.btn_play.centery - pt.get_height()//2))

        # gear icons
        self._icon_gear(SCREEN_WIDTH - 34, 34, 22)
        self._icon_gear(self.btn_gear_left.centerx, self.btn_gear_left.centery, 16)

        # bird preview
        self.pelican.x, self.pelican.y = 760, 210
        self.osprey.x,  self.osprey.y  = 620, 160
        self.pelican.facing_right = False
        self.osprey.facing_right  = True
        self._draw_birds()


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


# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    game = Game()
    game.run()
