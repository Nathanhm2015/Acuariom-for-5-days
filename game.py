import pygame
import math
import random
import sys
from enum import Enum

pygame.init()

SCREEN_WIDTH  = 1000
SCREEN_HEIGHT = 700
FPS           = 60

# ── Paleta de colores ──────────────────────────────────────────────────────
CIELO_TOP     = (100, 190, 240)
CIELO_BOTTOM  = (160, 220, 255)
AGUA_SURFACE  = ( 30, 140, 200)
AGUA_PROFUNDA = ( 10,  60, 130)
BLANCO        = (255, 255, 255)
NEGRO         = (  0,   0,   0)
NARANJA       = (255, 140,  30)
ROJO          = (220,  50,  50)
VERDE         = ( 50, 200,  80)
GRIS          = (150, 150, 160)
MARRON        = (120,  70,  30)
AZUL_HUD      = ( 40, 130, 200)
VERDE_BOTON   = ( 50, 160,  60)
VERDE_OSCURO  = ( 30,  90,  40)

AGUA_Y = 370   # y de la superficie del agua


# ═══════════════════════════════════════════════════════════════════════════
#  ESTADO DEL JUEGO
# ═══════════════════════════════════════════════════════════════════════════
class EstadoJuego(Enum):
    INICIO    = 1
    VOLANDO   = 2
    PICANDO   = 3
    BAJO_AGUA = 4
    SUBIENDO  = 5
    SETTINGS  = 6


# ═══════════════════════════════════════════════════════════════════════════
#  CLASE PEZ
# ═══════════════════════════════════════════════════════════════════════════
class Pez:
    TIPOS = {
        'rojo':     (230,  80,  80),
        'naranja':  (255, 160,  50),
        'amarillo': (255, 220,  60),
        'verde':    ( 80, 200, 100),
        'azul':     ( 80, 160, 255),
        'morado':   (190, 100, 200),
    }

    def __init__(self, x=None, y=None):
        self.x     = float(x if x is not None else random.randint(120, SCREEN_WIDTH - 120))
        self.y     = float(y if y is not None else random.randint(AGUA_Y + 40, SCREEN_HEIGHT - 40))
        self.vx    = random.uniform(-1.5, 1.5)
        self.vy    = random.uniform(-0.4, 0.4)
        self.radio = random.randint(13, 22)
        self.tipo  = random.choice(list(self.TIPOS.keys()))
        self.color = self.TIPOS[self.tipo]
        self.vivo  = True
        self.frame = 0

    def actualizar(self):
        self.x += self.vx
        self.y += self.vy
        self.frame += 1
        if self.x < 80 or self.x > SCREEN_WIDTH - 80:
            self.vx *= -1
        if self.y < AGUA_Y + 20 or self.y > SCREEN_HEIGHT - 20:
            self.vy *= -1
        self.x = max(80, min(SCREEN_WIDTH - 80, self.x))
        self.y = max(AGUA_Y + 20, min(SCREEN_HEIGHT - 20, self.y))

    def dibujar(self, pantalla):
        if not self.vivo:
            return
        r  = self.radio
        cx = int(self.x)
        cy = int(self.y)
        flip = self.vx >= 0

        pygame.draw.ellipse(pantalla, self.color,
                            (cx - r, cy - r // 2, r * 2, r))
        ondula = math.sin(self.frame * 0.18) * 3
        if flip:
            pts = [(cx + r, cy - r//3 + ondula),
                   (cx + r + r//2, cy + ondula * 1.4),
                   (cx + r, cy + r//3 + ondula)]
        else:
            pts = [(cx - r, cy - r//3 + ondula),
                   (cx - r - r//2, cy + ondula * 1.4),
                   (cx - r, cy + r//3 + ondula)]
        pygame.draw.polygon(pantalla, self.color, [(int(a), int(b)) for a, b in pts])

        ex = cx + (r // 3 if flip else -r // 3)
        ey = cy - r // 6
        pygame.draw.circle(pantalla, BLANCO, (ex, ey), max(3, r // 4))
        pygame.draw.circle(pantalla, NEGRO,  (ex, ey), max(1, r // 7))


# ═══════════════════════════════════════════════════════════════════════════
#  CLASE AVE
# ═══════════════════════════════════════════════════════════════════════════
class Ave:
    """
    tipo: 'pelicano' | 'osprey'
      Pelícano pardo  → blanco/crema + alas marrón oscuro, pico gris, bolsa naranja
      Osprey          → espalda marrón, pecho blanco, máscara ocular oscura, ojo amarillo
    """
    CONFIGS = {
        'pelicano': dict(vel=3.5, vel_picada=9,  radio_captura=48, envergadura=95),
        'osprey':   dict(vel=5.0, vel_picada=13, radio_captura=32, envergadura=78),
    }

    def __init__(self, tipo, x, y):
        self.tipo   = tipo
        self.x      = float(x)
        self.y      = float(y)
        self.vx     = 0.0
        self.vy     = 0.0
        self.estado = 'volando'
        cfg = self.CONFIGS[tipo]
        self.vel            = cfg['vel']
        self.vel_picada     = cfg['vel_picada']
        self.radio_captura  = cfg['radio_captura']
        self.envergadura    = cfg['envergadura']
        self.angulo         = 0.0
        self.frame          = 0
        self.pez_capturado  = None
        self.mirando_der    = True

    # ── movimiento con flechas ───────────────────
    def mover(self, dx, dy):
        if self.estado != 'volando':
            return
        self.vx += dx * 0.65
        self.vy += dy * 0.65
        self.vx *= 0.84
        self.vy *= 0.84
        spd = math.hypot(self.vx, self.vy)
        if spd > self.vel:
            self.vx = self.vx / spd * self.vel
            self.vy = self.vy / spd * self.vel

    def iniciar_picada(self):
        if self.estado != 'volando':
            return False
        if self.y > AGUA_Y - 30:
            return False
        self.estado = 'picando'
        self.vy     = self.vel_picada
        self.vx    *= 0.25
        return True

    def actualizar(self):
        self.frame += 1

        if self.estado == 'volando':
            self.x += self.vx
            self.y += self.vy
            # gravedad suave
            if self.vy < 0.5:
                self.vy += 0.06
            self.x = max(30, min(SCREEN_WIDTH - 30, self.x))
            self.y = max(30, min(AGUA_Y - 15, self.y))

        elif self.estado == 'picando':
            self.x += self.vx
            self.y += self.vy
            if self.y >= AGUA_Y + 15:
                self.estado = 'bajo_agua'
                self.vy = self.vel_picada * 0.3

        elif self.estado == 'bajo_agua':
            self.x += self.vx
            self.y += self.vy
            self.vy *= 0.91
            self.y   = min(self.y, SCREEN_HEIGHT - 20)

        elif self.estado == 'subiendo':
            self.x += self.vx
            self.y += self.vy
            self.vy -= 0.55
            if self.y < AGUA_Y - 25:
                self.estado = 'volando'
                self.vy = -2.0

        # ángulo visual
        if abs(self.vx) > 0.1 or abs(self.vy) > 0.1:
            self.angulo = math.atan2(self.vy, max(0.01, abs(self.vx)))
        if abs(self.vx) > 0.05:
            self.mirando_der = self.vx >= 0

    # ── dibujar ─────────────────────────────────
    def dibujar(self, pantalla):
        cx  = int(self.x)
        cy  = int(self.y)
        env = self.envergadura

        ang = self.angulo
        if self.estado == 'picando':
            ang = math.pi / 2
        elif self.estado == 'bajo_agua':
            ang = math.pi / 2 * 0.6
        elif self.estado == 'subiendo':
            ang = -math.pi / 4

        # espejear si mira a la izquierda
        sign = 1 if self.mirando_der else -1

        def rot(ox, oy):
            c, s = math.cos(ang), math.sin(ang)
            rx = ox * c - oy * s
            ry = ox * s + oy * c
            return int(cx + sign * rx), int(cy + ry)

        # ── cuerpo ──────────────────────────────
        body_pts = []
        for i in range(14):
            a = 2 * math.pi * i / 14
            body_pts.append(rot(math.cos(a) * env * 0.38,
                                math.sin(a) * env * 0.19))
        pygame.draw.polygon(pantalla, self.color_cuerpo, body_pts)

        # ── alas ────────────────────────────────
        bat = math.sin(self.frame * 0.22) * env * 0.14 \
              if self.estado == 'volando' else 0

        if self.estado in ('picando', 'bajo_agua'):
            # alas recogidas
            wL = [rot(0, -env*0.08), rot(-env*0.55, -env*0.04),
                  rot(-env*0.42,  env*0.03)]
            wR = [rot(0, -env*0.08), rot( env*0.55, -env*0.04),
                  rot( env*0.42,  env*0.03)]
        else:
            wL = [rot(0,0), rot(-env*0.75, -env*0.22+bat), rot(-env*0.52,  env*0.06)]
            wR = [rot(0,0), rot( env*0.75, -env*0.22+bat), rot( env*0.52,  env*0.06)]

        pygame.draw.polygon(pantalla, self.color_ala, wL)
        pygame.draw.polygon(pantalla, self.color_ala, wR)

        # ── pico ────────────────────────────────
        pico = [rot( env*0.30, -env*0.05),
                rot( env*0.58,  env*0.04),
                rot( env*0.58, -env*0.12)]
        pygame.draw.polygon(pantalla, self.color_pico, pico)

        # ── bolsa gular (solo pelícano) ──────────
        if self.tipo == 'pelicano':
            bolsa = [rot(env*0.28,  env*0.04),
                     rot(env*0.56,  env*0.04),
                     rot(env*0.53,  env*0.22),
                     rot(env*0.26,  env*0.17)]
            pygame.draw.polygon(pantalla, (215, 135, 25), bolsa)

        # ── ojo ─────────────────────────────────
        ex1, ey1 = rot(env * 0.21, -env * 0.07)
        pygame.draw.circle(pantalla, BLANCO, (ex1, ey1), max(3, env // 10))
        pygame.draw.circle(pantalla, NEGRO,  (ex1, ey1), max(1, env // 18))

        # ── pez capturado ────────────────────────
        if self.pez_capturado and self.estado == 'subiendo':
            fx, fy = rot(env * 0.52, env * 0.16)
            pygame.draw.ellipse(pantalla, self.pez_capturado.color,
                                (fx - 11, fy - 6, 22, 12))

        # ── burbujas bajo el agua ───────────────
        if self.estado == 'bajo_agua' and self.frame % 7 == 0:
            bx = int(self.x) + random.randint(-14, 14)
            by = int(self.y) - random.randint(5, 22)
            pygame.draw.circle(pantalla, (180, 220, 255), (bx, by), 4, 1)


# ═══════════════════════════════════════════════════════════════════════════
#  CLASE JUEGO
# ═══════════════════════════════════════════════════════════════════════════
class Juego:
    def __init__(self):
        self.pantalla = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Wings & Fish")
        self.reloj    = pygame.time.Clock()
        self.fuente   = pygame.font.Font(None, 36)
        self.fpeq     = pygame.font.Font(None, 24)
        self.fgrande  = pygame.font.Font(None, 80)
        self.ftitulo  = pygame.font.Font(None, 52)

        self.estado   = EstadoJuego.INICIO

        # ── fondo opcional ──────────────────────
        self.imagen_fondo = None
        try:
            img = pygame.image.load('fondo.png')
            self.imagen_fondo = pygame.transform.scale(
                img.convert(), (SCREEN_WIDTH, SCREEN_HEIGHT))
            print("fondo.png cargado")
        except Exception as e:
            print(f"Sin fondo.png: {e}")

        # ── aves ───────────────────────────────
        self.pelicano     = Ave('pelicano', 260, 260)
        self.osprey       = Ave('osprey',   720, 190)
        self.ave_activa   = self.pelicano

        # ── peces ──────────────────────────────
        self.peces = [Pez() for _ in range(14)]

        # ── HUD ────────────────────────────────
        self.pescados    = 0
        self.stamina     = 100.0
        self.max_stamina = 100.0

        self.mensajes_guia = []
        self._agregar_mensaje("Chris: Press Play to begin the game.")

        # ── flotantes +1 ───────────────────────
        self.flotantes = []

        # ── input ──────────────────────────────
        self.teclas = {
            pygame.K_UP:    False,
            pygame.K_DOWN:  False,
            pygame.K_LEFT:  False,
            pygame.K_RIGHT: False,
        }

        # ── rects HUD ──────────────────────────
        self.btn_play          = pygame.Rect(SCREEN_WIDTH - 200, 18, 178, 58)
        self.btn_pelicano      = pygame.Rect(18,  SCREEN_HEIGHT - 132, 110, 110)
        self.btn_osprey        = pygame.Rect(SCREEN_WIDTH - 128, SCREEN_HEIGHT - 132, 110, 110)
        self.btn_gear          = pygame.Rect(SCREEN_WIDTH - 58, 10, 48, 48)   # engranaje derecha
        self.btn_gear_izq      = pygame.Rect(10, 10, 48, 48)                  # engranaje izquierda
        self.estado_prev       = EstadoJuego.VOLANDO   # para volver al salir de settings
        self.btn_cerrar_settings = pygame.Rect(SCREEN_WIDTH//2 + 210, SCREEN_HEIGHT//2 - 220, 40, 40)

        # ── nubes animadas ──────────────────────
        self.nubes = [(random.randint(0, SCREEN_WIDTH),
                       random.randint(30, 120),
                       random.randint(25, 55),
                       random.uniform(0.2, 0.6))
                      for _ in range(5)]

    # ── helpers ─────────────────────────────────
    def _agregar_mensaje(self, texto, duracion=260):
        self.mensajes_guia = [(texto, duracion)]

    def _agregar_flotante(self, x, y, txt="+1"):
        self.flotantes.append({'x': float(x), 'y': float(y), 't': 90, 'txt': txt})

    # ── loop ────────────────────────────────────
    def correr(self):
        corriendo = True
        while corriendo:
            corriendo = self.manejar_eventos()
            self.actualizar()
            self.dibujar()
            self.reloj.tick(FPS)
        pygame.quit()
        sys.exit()

    # ═══════════════════════════════════════════
    #  EVENTOS
    # ═══════════════════════════════════════════
    def manejar_eventos(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return False

            if ev.type == pygame.KEYDOWN:
                if ev.key in self.teclas:
                    self.teclas[ev.key] = True

                # ESC cierra settings o vuelve al inicio
                if ev.key == pygame.K_ESCAPE:
                    if self.estado == EstadoJuego.SETTINGS:
                        self.estado = self.estado_prev
                    else:
                        self.estado = EstadoJuego.INICIO

                if self.estado == EstadoJuego.SETTINGS:
                    continue

                if ev.key == pygame.K_SPACE:
                    self._zambullir(self.ave_activa)

                if ev.key == pygame.K_a:
                    self.ave_activa = self.pelicano
                    self._zambullir(self.pelicano)
                    self._agregar_mensaje("Martin: Pelican dives for big fish!")

                if ev.key == pygame.K_d:
                    self.ave_activa = self.osprey
                    self._zambullir(self.osprey)
                    self._agregar_mensaje("Martin: Osprey button to dive!")

            if ev.type == pygame.KEYUP:
                if ev.key in self.teclas:
                    self.teclas[ev.key] = False

            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = pygame.mouse.get_pos()

                # ── Pantalla SETTINGS ────────────────────
                if self.estado == EstadoJuego.SETTINGS:
                    if self.btn_cerrar_settings.collidepoint(mx, my):
                        self.estado = self.estado_prev
                    return True

                # ── Botón engranaje izquierdo → settings ─
                if self.btn_gear_izq.collidepoint(mx, my):
                    self.estado_prev = self.estado if self.estado != EstadoJuego.INICIO else EstadoJuego.VOLANDO
                    self.estado = EstadoJuego.SETTINGS
                    return True

                if self.estado == EstadoJuego.INICIO:
                    if self.btn_play.collidepoint(mx, my):
                        self._iniciar_juego()
                    return True

                if self.btn_pelicano.collidepoint(mx, my):
                    self.ave_activa = self.pelicano
                    self._agregar_mensaje("Martin: Press the pelican or A to dive!")
                    return True
                if self.btn_osprey.collidepoint(mx, my):
                    self.ave_activa = self.osprey
                    self._agregar_mensaje("Martin: Osprey button to dive!")
                    return True

                if self.estado == EstadoJuego.VOLANDO:
                    self._zambullir(self.ave_activa)

        return True

    def _iniciar_juego(self):
        self.estado         = EstadoJuego.VOLANDO
        self.pelicano.x,  self.pelicano.y  = 260, 260
        self.osprey.x,    self.osprey.y    = 720, 190
        self.pelicano.estado = 'volando'
        self.osprey.estado   = 'volando'
        self.pelicano.vx = self.pelicano.vy = 0
        self.osprey.vx   = self.osprey.vy   = 0
        self._agregar_mensaje("Martin: Use arrows to fly! A=pelican dive, D=osprey dive")

    def _zambullir(self, ave):
        if self.estado != EstadoJuego.VOLANDO:
            return
        if self.stamina < 15:
            self._agregar_mensaje("Chris: The bird needs to rest! Low energy.")
            return
        if ave.iniciar_picada():
            self.stamina -= 20
            self.estado   = EstadoJuego.PICANDO

    # ═══════════════════════════════════════════
    #  ACTUALIZAR
    # ═══════════════════════════════════════════
    def actualizar(self):
        if self.estado in (EstadoJuego.INICIO, EstadoJuego.SETTINGS):
            # mover nubes igualmente
            self._actualizar_nubes()
            return

        # ── flechas → mover ave activa ──────────
        dx = dy = 0
        if self.teclas[pygame.K_LEFT]:  dx -= 1
        if self.teclas[pygame.K_RIGHT]: dx += 1
        if self.teclas[pygame.K_UP]:    dy -= 1
        if self.teclas[pygame.K_DOWN]:  dy += 1
        self.ave_activa.mover(dx, dy)

        # ── actualizar aves ─────────────────────
        self.pelicano.actualizar()
        self.osprey.actualizar()

        # ── stamina ─────────────────────────────
        if self.estado == EstadoJuego.VOLANDO:
            self.stamina = min(self.max_stamina, self.stamina + 0.18)

        # ── peces ───────────────────────────────
        for pez in self.peces:
            if pez.vivo:
                pez.actualizar()

        # ── máquina de estados ──────────────────
        if self.estado == EstadoJuego.PICANDO:
            ave = self.ave_activa
            if ave.estado == 'bajo_agua':
                self.estado = EstadoJuego.BAJO_AGUA

        elif self.estado == EstadoJuego.BAJO_AGUA:
            ave = self.ave_activa
            capturado = False
            for pez in self.peces:
                if not pez.vivo:
                    continue
                dist = math.hypot(ave.x - pez.x, ave.y - pez.y)
                if dist < ave.radio_captura + pez.radio:
                    pez.vivo          = False
                    ave.pez_capturado = pez
                    ave.estado        = 'subiendo'
                    ave.vy            = -ave.vel_picada * 0.75
                    self.pescados    += 1
                    self._agregar_flotante(ave.x, ave.y - 30)
                    self._agregar_mensaje(f"Chris: Great catch! Fish: {self.pescados}")
                    self.estado       = EstadoJuego.SUBIENDO
                    self.peces.append(Pez())
                    capturado = True
                    break

            # sin pez → subir si bajó suficiente
            if not capturado and ave.estado == 'bajo_agua' and ave.y > AGUA_Y + 90:
                ave.estado = 'subiendo'
                ave.vy     = -ave.vel_picada * 0.5
                self.estado = EstadoJuego.SUBIENDO

        elif self.estado == EstadoJuego.SUBIENDO:
            ave = self.ave_activa
            if ave.estado == 'volando':
                ave.pez_capturado = None
                self.estado       = EstadoJuego.VOLANDO

        # ── mensajes guía ───────────────────────
        self.mensajes_guia = [(t, d - 1) for t, d in self.mensajes_guia if d > 1]

        # ── flotantes ──────────────────────────
        nuevos = []
        for f in self.flotantes:
            f['t']  -= 1
            f['y']  -= 0.8
            if f['t'] > 0:
                nuevos.append(f)
        self.flotantes = nuevos

        # ── nubes ──────────────────────────────
        self._actualizar_nubes()

    def _actualizar_nubes(self):
        nuevas = []
        for nx, ny, sz, vx in self.nubes:
            nx += vx
            if nx > SCREEN_WIDTH + sz * 2:
                nx = -sz * 2
            nuevas.append((nx, ny, sz, vx))
        self.nubes = nuevas

    # ═══════════════════════════════════════════
    #  DIBUJAR
    # ═══════════════════════════════════════════
    def dibujar(self):
        self._dibujar_fondo()
        if self.estado not in (EstadoJuego.INICIO, EstadoJuego.SETTINGS):
            self._dibujar_agua()

        self._dibujar_peces()
        self._dibujar_aves()
        self._dibujar_flotantes()

        if self.estado == EstadoJuego.INICIO:
            self._dibujar_pantalla_inicio()
        elif self.estado == EstadoJuego.SETTINGS:
            self._dibujar_hud()
            self._dibujar_panel_settings()
        else:
            self._dibujar_hud()

        pygame.display.flip()

    # ── fondo: cielo + islas + nubes ──────────
    def _dibujar_fondo(self):
        if self.imagen_fondo and self.estado != EstadoJuego.INICIO:
            self.pantalla.blit(self.imagen_fondo, (0, 0))
            return

        # degradado cielo
        for y in range(AGUA_Y if self.estado != EstadoJuego.INICIO else SCREEN_HEIGHT):
            r = y / AGUA_Y
            r = min(1.0, r)
            c = (int(CIELO_TOP[0]*(1-r) + CIELO_BOTTOM[0]*r),
                 int(CIELO_TOP[1]*(1-r) + CIELO_BOTTOM[1]*r),
                 int(CIELO_TOP[2]*(1-r) + CIELO_BOTTOM[2]*r))
            pygame.draw.line(self.pantalla, c, (0, y), (SCREEN_WIDTH, y))

        # nubes animadas
        for nx, ny, sz, _ in self.nubes:
            for ox, oy, r in [(0, 0, sz), (sz//2, -10, sz-8), (sz, 0, sz-5)]:
                pygame.draw.circle(self.pantalla, BLANCO, (int(nx+ox), int(ny+oy)), r)

        if self.estado != EstadoJuego.INICIO:
            # islas
            self._dibujar_isla(155, AGUA_Y, 115)
            self._dibujar_isla(845, AGUA_Y, 135)

    def _dibujar_isla(self, cx, base_y, sz):
        pts = [(cx - sz, base_y), (cx, base_y - sz * 1.1), (cx + sz, base_y)]
        pygame.draw.polygon(self.pantalla, (55, 125, 65), pts)
        for ox in [-sz//2, 0, sz//2]:
            tx, ty = cx + ox, base_y
            pygame.draw.rect(self.pantalla, MARRON, (tx - 4, ty - 52, 8, 52))
            for ang in [-0.8, 0, 0.8, 1.5, -1.5]:
                hx = tx + int(math.cos(ang - math.pi/2) * 26)
                hy = (ty - 52) + int(math.sin(ang - math.pi/2) * 26)
                pygame.draw.line(self.pantalla, VERDE_OSCURO, (tx, ty - 52), (hx, hy), 4)

    def _dibujar_agua(self):
        if self.imagen_fondo:
            return
        # degradado agua
        for y in range(AGUA_Y, SCREEN_HEIGHT):
            r = (y - AGUA_Y) / (SCREEN_HEIGHT - AGUA_Y)
            c = (int(AGUA_SURFACE[0]*(1-r) + AGUA_PROFUNDA[0]*r),
                 int(AGUA_SURFACE[1]*(1-r) + AGUA_PROFUNDA[1]*r),
                 int(AGUA_SURFACE[2]*(1-r) + AGUA_PROFUNDA[2]*r))
            pygame.draw.line(self.pantalla, c, (0, y), (SCREEN_WIDTH, y))

        # olas
        t = pygame.time.get_ticks() / 600.0
        pts_ola = []
        for x in range(0, SCREEN_WIDTH + 10, 8):
            y = AGUA_Y + int(math.sin(x / 55 + t) * 5)
            pts_ola.append((x, y))
        pts_ola += [(SCREEN_WIDTH, AGUA_Y + 22), (0, AGUA_Y + 22)]
        pygame.draw.polygon(self.pantalla, (200, 230, 255), pts_ola)

        # espuma
        for x in range(0, SCREEN_WIDTH, 10):
            y = AGUA_Y + int(math.sin(x / 55 + t) * 5)
            pygame.draw.circle(self.pantalla, BLANCO, (x, y), 3)

        # rayos de luz
        ray_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT - AGUA_Y), pygame.SRCALPHA)
        for i in range(6):
            rx = 80 + i * 165 + int(math.sin(t * 0.4 + i) * 28)
            rpts = [(rx, 0), (rx + 45, SCREEN_HEIGHT - AGUA_Y),
                    (rx + 65, SCREEN_HEIGHT - AGUA_Y), (rx + 20, 0)]
            pygame.draw.polygon(ray_surf, (255, 255, 255, 16), rpts)
        self.pantalla.blit(ray_surf, (0, AGUA_Y))

    def _dibujar_peces(self):
        for pez in self.peces:
            pez.dibujar(self.pantalla)

    def _dibujar_aves(self):
        for ave in [self.pelicano, self.osprey]:
            ave.dibujar(self.pantalla)

    def _dibujar_flotantes(self):
        for f in self.flotantes:
            alpha = min(255, int(255 * f['t'] / 90))
            surf  = self.fuente.render(f['txt'], True, (255, 220, 50))
            surf.set_alpha(alpha)
            self.pantalla.blit(surf, (int(f['x']), int(f['y'])))

    # ═══════════════════════════════════════════
    #  HUD (como en las imágenes de referencia)
    # ═══════════════════════════════════════════
    def _dibujar_hud(self):
        # banda oscura superior
        banda = pygame.Surface((SCREEN_WIDTH, 78), pygame.SRCALPHA)
        banda.fill((0, 0, 0, 155))
        self.pantalla.blit(banda, (0, 0))

        # ── ícono de pez + contador ─────────────
        self._icono_pez(46, 38)
        txt = self.fuente.render(str(self.pescados), True, BLANCO)
        self.pantalla.blit(txt, (75, 22))

        # ── rayo + stamina ──────────────────────
        self._icono_rayo(148, 25, 30)
        bx, by, bw, bh = 185, 24, 320, 30
        pygame.draw.rect(self.pantalla, (60, 20, 10), (bx, by, bw, bh), border_radius=6)
        relleno = int(bw * self.stamina / self.max_stamina)
        if relleno > 0:
            pygame.draw.rect(self.pantalla, NARANJA,
                             (bx, by, relleno, bh), border_radius=6)
        pygame.draw.rect(self.pantalla, (180, 80, 20), (bx, by, bw, bh), 2, border_radius=6)

        # ── engranaje derecha ──────────────────
        self._icono_engranaje(SCREEN_WIDTH - 34, 34, 22)
        # ── engranaje izquierda (settings) ───────
        self._icono_engranaje(self.btn_gear_izq.centerx, self.btn_gear_izq.centery, 16)

        # ── mensaje de guía ─────────────────────
        if self.mensajes_guia:
            txt_msg, tiempo = self.mensajes_guia[0]
            alpha = min(255, tiempo * 5) if tiempo < 50 else 255
            panel_w = min(500, max(200, len(txt_msg) * 9 + 30))
            panel = pygame.Surface((panel_w, 32), pygame.SRCALPHA)
            panel.fill((40, 15, 5, 185))
            pygame.draw.rect(panel, (190, 90, 40), (0, 0, panel_w, 32), 2, border_radius=8)
            self.pantalla.blit(panel, (SCREEN_WIDTH//2 - panel_w//2, 8))
            s = self.fpeq.render(txt_msg, True, BLANCO)
            s.set_alpha(alpha)
            self.pantalla.blit(s, (SCREEN_WIDTH//2 - s.get_width()//2, 16))

        # ── estado del dive ─────────────────────
        estado_lbl = {
            EstadoJuego.PICANDO:   "DIVING!",
            EstadoJuego.BAJO_AGUA: "Under water!",
            EstadoJuego.SUBIENDO:  "Rising...",
        }.get(self.estado, "")
        if estado_lbl:
            s = self.fuente.render(estado_lbl, True, (255, 240, 80))
            self.pantalla.blit(s, (SCREEN_WIDTH//2 - s.get_width()//2, 52))

        # ── botones circulares de aves ───────────
        self._boton_ave(self.btn_pelicano, self.pelicano,
                        activo=(self.ave_activa is self.pelicano), tecla="A")
        self._boton_ave(self.btn_osprey,   self.osprey,
                        activo=(self.ave_activa is self.osprey),   tecla="D")

        # ── flechas laterales ───────────────────
        self._flecha_hud(self.btn_pelicano.left - 44, self.btn_pelicano.centery, True)
        self._flecha_hud(self.btn_osprey.right  + 44, self.btn_osprey.centery,   False)

    def _icono_pez(self, cx, cy):
        pygame.draw.ellipse(self.pantalla, (70, 195, 215), (cx - 16, cy - 8, 28, 16))
        pygame.draw.polygon(self.pantalla, (70, 195, 215),
                            [(cx + 12, cy - 9), (cx + 25, cy), (cx + 12, cy + 9)])
        pygame.draw.circle(self.pantalla, BLANCO, (cx - 4, cy - 2), 4)
        pygame.draw.circle(self.pantalla, NEGRO,  (cx - 4, cy - 2), 2)

    def _icono_rayo(self, cx, cy, tam):
        pts = [(cx, cy),
               (cx + tam*0.38, cy + tam*0.38),
               (cx + tam*0.14, cy + tam*0.38),
               (cx + tam*0.52, cy + tam),
               (cx - tam*0.06, cy + tam*0.50),
               (cx + tam*0.18, cy + tam*0.50),
               (cx - tam*0.12, cy)]
        pygame.draw.polygon(self.pantalla, (255, 240, 50),
                            [(int(x), int(y)) for x, y in pts])

    def _icono_engranaje(self, cx, cy, r):
        pygame.draw.circle(self.pantalla, ROJO, (cx, cy), r + 8)
        pygame.draw.circle(self.pantalla, (210, 55, 55), (cx, cy), r + 8, 3)
        pygame.draw.circle(self.pantalla, BLANCO, (cx, cy), r)
        for i in range(8):
            a = 2 * math.pi * i / 8
            x1 = cx + int(math.cos(a) * (r + 4))
            y1 = cy + int(math.sin(a) * (r + 4))
            x2 = cx + int(math.cos(a + 0.22) * (r + 10))
            y2 = cy + int(math.sin(a + 0.22) * (r + 10))
            x3 = cx + int(math.cos(a + 0.44) * (r + 4))
            y3 = cy + int(math.sin(a + 0.44) * (r + 4))
            pygame.draw.polygon(self.pantalla, ROJO, [(x1,y1),(x2,y2),(x3,y3)])
        pygame.draw.circle(self.pantalla, (55, 15, 15), (cx, cy), r // 2)

    def _boton_ave(self, rect, ave, activo, tecla):
        color_borde = VERDE_BOTON if ave.tipo == 'pelicano' else AZUL_HUD
        cx, cy = rect.centerx, rect.centery
        rad    = rect.width // 2

        # sombra
        pygame.draw.circle(self.pantalla, (0, 0, 0), (cx + 4, cy + 4), rad)
        # fondo oscuro
        pygame.draw.circle(self.pantalla, (28, 28, 35), (cx, cy), rad)
        # borde activo / inactivo
        grosor = 7 if activo else 4
        pygame.draw.circle(self.pantalla, color_borde, (cx, cy), rad, grosor)

        # silueta de ave
        r = rad - 16
        if ave.tipo == 'pelicano':
            pygame.draw.ellipse(self.pantalla, (55, 110, 55),
                                (cx - r, cy - r//2, r*2, r))
            pygame.draw.polygon(self.pantalla, (18, 52, 18),
                                [(cx, cy), (cx - r*2, cy - r//2), (cx - r, cy + r//3)])
            pygame.draw.polygon(self.pantalla, (18, 52, 18),
                                [(cx, cy), (cx + r*2, cy - r//2), (cx + r, cy + r//3)])
            pygame.draw.polygon(self.pantalla, (210, 140, 25),
                                [(cx + r, cy - r//4), (cx + r*2, cy),
                                 (cx + r, cy + r//4)])
        else:
            pygame.draw.ellipse(self.pantalla, (160, 172, 182),
                                (cx - r, cy - r//2, r*2, r))
            pygame.draw.polygon(self.pantalla, (36, 46, 66),
                                [(cx, cy), (cx - r*2, cy - r//2), (cx - r, cy + r//3)])
            pygame.draw.polygon(self.pantalla, (36, 46, 66),
                                [(cx, cy), (cx + r*2, cy - r//2), (cx + r, cy + r//3)])

        # etiqueta [A] / [D]
        lbl = self.fpeq.render(f"[{tecla}]", True, color_borde)
        self.pantalla.blit(lbl, (cx - lbl.get_width()//2, rect.bottom + 5))

    def _flecha_hud(self, cx, cy, izquierda):
        r = pygame.Rect(cx - 19, cy - 19, 38, 38)
        pygame.draw.rect(self.pantalla, (55, 65, 78), r, border_radius=7)
        pygame.draw.rect(self.pantalla, (110, 132, 155), r, 2, border_radius=7)
        if izquierda:
            pts = [(cx - 9, cy), (cx + 7, cy - 8), (cx + 7, cy + 8)]
        else:
            pts = [(cx + 9, cy), (cx - 7, cy - 8), (cx - 7, cy + 8)]
        pygame.draw.polygon(self.pantalla, BLANCO, pts)

    # ═══════════════════════════════════════════
    #  PANTALLA INICIO
    # ═══════════════════════════════════════════
    def _dibujar_pantalla_inicio(self):
        # overlay
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 20, 45, 150))
        self.pantalla.blit(ov, (0, 0))

        # mensaje guía
        if self.mensajes_guia:
            txt, _ = self.mensajes_guia[0]
            s = self.fpeq.render(txt, True, BLANCO)
            self.pantalla.blit(s, (SCREEN_WIDTH//2 - s.get_width()//2, 24))

        # título
        t1 = self.fgrande.render("WINGS", True, BLANCO)
        t2 = self.fgrande.render("& FISH", True, (255, 200, 40))
        self.pantalla.blit(t1, (80, 95))
        self.pantalla.blit(t2, (80, 168))

        # subtítulo
        sub = self.ftitulo.render("Catch fish with seabirds!", True, BLANCO)
        self.pantalla.blit(sub, (80, 255))

        # instrucciones
        for i, txt in enumerate([
            "Arrow keys: fly the active bird",
            "A: Pelican dives  |  D: Osprey dives",
            "Space / Click: active bird dives",
        ]):
            s = self.fpeq.render(txt, True, (195, 230, 255))
            self.pantalla.blit(s, (80, 318 + i * 28))

        # botón PLAY
        pygame.draw.rect(self.pantalla, NARANJA, self.btn_play, border_radius=14)
        pygame.draw.rect(self.pantalla, (255, 205, 55), self.btn_play, 4, border_radius=14)
        pt = self.ftitulo.render("PLAY", True, BLANCO)
        self.pantalla.blit(pt, (self.btn_play.centerx - pt.get_width()//2,
                                self.btn_play.centery - pt.get_height()//2))

        # engranaje derecha
        self._icono_engranaje(SCREEN_WIDTH - 34, 34, 22)
        # engranaje izquierda
        self._icono_engranaje(self.btn_gear_izq.centerx, self.btn_gear_izq.centery, 16)

        # preview de las aves
        self.pelicano.x, self.pelicano.y = 760, 210
        self.osprey.x,   self.osprey.y   = 620, 160
        self.pelicano.mirando_der = False
        self.osprey.mirando_der   = True
        self._dibujar_aves()


    # ═══════════════════════════════════════
    #  PANEL DE SETTINGS / INSTRUCCIONES
    # ═══════════════════════════════════════
    def _dibujar_panel_settings(self):
        pw, ph = 480, 440
        px = SCREEN_WIDTH  // 2 - pw // 2
        py = SCREEN_HEIGHT // 2 - ph // 2

        # fondo oscuro con transparencia
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.pantalla.blit(overlay, (0, 0))

        # panel principal
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((15, 30, 55, 235))
        self.pantalla.blit(panel, (px, py))
        pygame.draw.rect(self.pantalla, (80, 160, 230), (px, py, pw, ph), 3, border_radius=16)

        # franja de título
        pygame.draw.rect(self.pantalla, (30, 70, 130), (px, py, pw, 52), border_radius=16)
        titulo = self.ftitulo.render("SETTINGS", True, BLANCO)
        self.pantalla.blit(titulo, (px + pw//2 - titulo.get_width()//2, py + 10))

        # engranaje decorativo en título
        self._icono_engranaje(px + 30, py + 26, 14)

        # botón CERRAR  ✕
        cerrar_rect = self.btn_cerrar_settings
        cerrar_rect.topleft = (px + pw - 46, py + 6)
        pygame.draw.rect(self.pantalla, (180, 50, 50), cerrar_rect, border_radius=8)
        pygame.draw.rect(self.pantalla, (230, 90, 90), cerrar_rect, 2, border_radius=8)
        x_txt = self.fuente.render("X", True, BLANCO)
        self.pantalla.blit(x_txt, (cerrar_rect.centerx - x_txt.get_width()//2,
                                    cerrar_rect.centery - x_txt.get_height()//2))

        # ── sección: CONTROLES ──────────────────
        iy = py + 68
        secc_font = pygame.font.Font(None, 26)
        titulo_secc = secc_font.render("CONTROLS", True, (130, 200, 255))
        self.pantalla.blit(titulo_secc, (px + 20, iy))
        pygame.draw.line(self.pantalla, (80, 130, 200),
                         (px + 20, iy + 22), (px + pw - 20, iy + 22), 1)
        iy += 32

        linea_font = pygame.font.Font(None, 22)
        controles = [
            ("Arrow LEFT / RIGHT",  "Move the active bird horizontally"),
            ("Arrow UP",            "Fly upward / gain height"),
            ("Arrow DOWN",          "Descend toward the water"),
            ("A  key",              "Select PELICAN and dive"),
            ("D  key",              "Select OSPREY and dive"),
            ("SPACE  /  Click",     "Active bird dives"),
            ("ESC",                 "Return to previous screen"),
        ]
        for tecla, desc in controles:
            # tecla en caja
            tecla_sur = linea_font.render(tecla, True, (255, 220, 80))
            desc_sur  = linea_font.render(desc,  True, (210, 230, 255))
            tecla_bg  = pygame.Rect(px + 16, iy - 2, 148, 22)
            pygame.draw.rect(self.pantalla, (35, 55, 90), tecla_bg, border_radius=4)
            pygame.draw.rect(self.pantalla, (70, 100, 160), tecla_bg, 1, border_radius=4)
            self.pantalla.blit(tecla_sur, (px + 20, iy))
            self.pantalla.blit(desc_sur,  (px + 174, iy))
            iy += 26

        # ── sección: BIRDS ──────────────────────
        iy += 8
        titulo_secc2 = secc_font.render("BIRDS", True, (130, 200, 255))
        self.pantalla.blit(titulo_secc2, (px + 20, iy))
        pygame.draw.line(self.pantalla, (80, 130, 200),
                         (px + 20, iy + 22), (px + pw - 20, iy + 22), 1)
        iy += 32

        aves_info = [
            ("PELICAN",  "[A]", "Slow, wide capture range. Gular pouch catches big fish."),
            ("OSPREY",   "[D]", "Fast, precise dive. Best for quick single-fish catches."),
        ]
        for nombre, tecla, desc in aves_info:
            n_sur = linea_font.render(f"{nombre}  {tecla}", True, (255, 220, 80))
            d_sur = linea_font.render(desc, True, (210, 230, 255))
            self.pantalla.blit(n_sur, (px + 20, iy))
            self.pantalla.blit(d_sur, (px + 20, iy + 20))
            iy += 48

        # ── pie: ESC para cerrar ─────────────────
        esc_sur = linea_font.render("Press ESC or click X to close", True, (150, 160, 180))
        self.pantalla.blit(esc_sur, (px + pw//2 - esc_sur.get_width()//2, py + ph - 28))


# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    juego = Juego()
    juego.correr()
