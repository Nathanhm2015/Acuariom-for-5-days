import pygame
import math
import random
from enum import Enum

# Inicializar Pygame
pygame.init()

# Constantes
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FPS = 60

# Colores - Flat Design Palette
CIELO_CLARO = (255, 220, 120)  # Amarillo brillante para el cielo
CIELO_HORIZON = (200, 160, 90)   # Degradado hacia el horizonte
AGUA_SURFACE = (0, 220, 160)    # Verde turquesa brillante en la superficie
AGUA_MEDIA = (0, 180, 180)      # Verde agua media profundidad
AGUA_PROFUNDA = (20, 120, 180)  # Azul-verde oscuro
BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)
AMARILLO = (255, 255, 0)
NARANJA = (255, 165, 0)
NARANJA_ANZUELO = (255, 140, 50)  # Para la bolita del anzuelo
ROJO = (255, 0, 0)
VERDE = (0, 255, 0)
GRIS = (128, 128, 128)
MARRON = (139, 69, 19)
AZUL_DETALLE = (70, 150, 200)  # Detalle azul del anzuelo
VERDE_OSCURO = (40, 100, 60)  # Para plantas marinas

class EstadoJuego(Enum):
    ESPERANDO = 1
    CARGANDO = 2
    LANZADO = 3
    PESCANDO = 4
    RECOMPENSAS = 5

class Pez:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-1.5, 1.5)
        self.vy = random.uniform(-0.5, 0.5)
        self.radio = random.randint(12, 22)
        self.tipo = random.choice(['rojo', 'naranja', 'amarillo', 'verde', 'azul', 'morado'])
        self.colores = {
            'rojo': (255, 80, 80),
            'naranja': (255, 150, 50),
            'amarillo': (255, 220, 60),
            'verde': (80, 200, 100),
            'azul': (80, 150, 255),
            'morado': (200, 100, 200)
        }
        self.color_primario = self.colores[self.tipo]
        self.vivo = True
        self.frame = 0

    def actualizar(self):
        self.x += self.vx
        self.y += self.vy
        self.frame += 1

        # Cambiar dirección en bordes
        if self.x - self.radio < 100 or self.x + self.radio > SCREEN_WIDTH - 100:
            self.vx *= -1
        if self.y - self.radio < 400 or self.y + self.radio > SCREEN_HEIGHT - 40:
            self.vy *= -1

        # Mantener en límites
        self.x = max(100 + self.radio, min(SCREEN_WIDTH - 100 - self.radio, self.x))
        self.y = max(400 + self.radio, min(SCREEN_HEIGHT - 40 - self.radio, self.y))

    def dibujar(self, pantalla):
        if self.vivo:
            # Cuerpo simple y redondeado (flat design)
            cuerpo_ancho = int(self.radio * 2.2)
            cuerpo_alto = int(self.radio * 1.4)

            # Cuerpo principal redondeado
            pygame.draw.ellipse(pantalla, self.color_primario,
                               (int(self.x - cuerpo_ancho // 2), int(self.y - cuerpo_alto // 2),
                                cuerpo_ancho, cuerpo_alto))

            # Cola triangular ondulante
            ondulacion = math.sin(self.frame * 0.15) * 3
            cola_x1 = int(self.x + cuerpo_ancho // 2)
            cola_y1 = int(self.y - cuerpo_alto // 3 + ondulacion)
            cola_x2 = int(self.x + cuerpo_ancho // 2 + self.radio)
            cola_y2 = int(self.y + ondulacion * 1.5)
            cola_x3 = int(self.x + cuerpo_ancho // 2)
            cola_y3 = int(self.y + cuerpo_alto // 3 + ondulacion)

            pygame.draw.polygon(pantalla, self.color_primario,
                               [(cola_x1, cola_y1), (cola_x2, cola_y2), (cola_x3, cola_y3)])

            # OJOS GRANDES y expresivos (estilo caricaturesco)
            ojo_x = int(self.x - cuerpo_ancho // 4)
            ojo_y = int(self.y - cuerpo_alto // 3)
            ojo_radio = max(5, self.radio // 2.5)

            # Ojo blanco grande
            pygame.draw.circle(pantalla, BLANCO, (ojo_x, ojo_y), ojo_radio)
            # Pupila negra
            pygame.draw.circle(pantalla, NEGRO, (ojo_x, ojo_y), ojo_radio // 2)

            # Sonrisa simple (línea curvada)
            sonrisa_y = int(self.y + cuerpo_alto // 4)
            pygame.draw.arc(pantalla, NEGRO,
                           (int(self.x - cuerpo_ancho // 5), sonrisa_y - 2,
                            int(cuerpo_ancho // 2.5), 8),
                           0, math.pi, 2)

class Linea:
    def __init__(self, x_inicio, y_inicio, potencia, angulo, distancia_base=400):
        self.x_inicio = x_inicio
        self.y_inicio = y_inicio
        self.potencia = potencia  # 0 a 100
        self.angulo = angulo

        # Distancia máxima calculada según potencia y base
        self.distancia_max = (potencia / 100) * distancia_base

        # Posición dinámica del anzuelo
        self.x_pos = x_inicio
        self.y_pos = y_inicio

        # Velocidad inicial basada en potencia
        max_speed = 40.0
        speed = (potencia / 100) * max_speed
        self.vx = math.cos(angulo) * speed
        self.vy = math.sin(angulo) * speed

        # Gravedad
        self.gravity = 0.9
        self.en_agua = False
        self.pez_enganchado = None
        self.tiempo_linea = 0

    def actualizar(self):
        # Física tipo proyectil
        if not self.en_agua:
            self.x_pos += self.vx
            self.y_pos += self.vy
            self.vy += self.gravity

            # Distancia recorrida
            distancia_recorrida = math.hypot(self.x_pos - self.x_inicio, self.y_pos - self.y_inicio)

            # Si alcanza la distancia máxima, cae al agua
            if distancia_recorrida >= self.distancia_max or self.y_pos >= 350:
                self.y_pos = min(self.y_pos, 350)
                self.en_agua = True

        self.tiempo_linea += 1

    def dibujar(self, pantalla):
        # Dibujar la línea desde el inicio hasta el anzuelo
        puntos = []
        segmentos = 22

        x_final = int(self.x_pos)
        y_final = int(self.y_pos)

        for i in range(segmentos + 1):
            t = i / segmentos
            x = self.x_inicio + (x_final - self.x_inicio) * t
            y = self.y_inicio + (y_final - self.y_inicio) * t

            # Ondulación pequeña
            perpendicular_x = -(y_final - self.y_inicio) / (self.distancia_max + 1)
            perpendicular_y = (x_final - self.x_inicio) / (self.distancia_max + 1)
            ondulacion = math.sin(self.tiempo_linea * 0.12 + i * 0.35) * (2 if self.en_agua else 4 * (self.potencia/100))
            x += perpendicular_x * ondulacion
            y += perpendicular_y * ondulacion

            puntos.append((int(x), int(y)))

        # Dibujar línea negra delgada
        for i in range(len(puntos) - 1):
            grosor = max(1, int(2))
            pygame.draw.line(pantalla, NEGRO, puntos[i], puntos[i + 1], grosor)

        # Dibujar anzuelo - Bolita naranja simple con detalle azul
        pygame.draw.circle(pantalla, NARANJA_ANZUELO, (x_final, y_final), 6)
        # Pequeño detalle azul en el anzuelo
        pygame.draw.circle(pantalla, AZUL_DETALLE, (x_final + 2, y_final - 2), 3)

class Bote:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.ancho = 140
        self.alto = 70
        self.angulo_cana = -math.pi / 4  # Ángulo inicial
        self.flexion_cana = 0
        self.tiempo_lanzamiento = 0
        self.animando_lanzamiento = False

    def dibujar(self, pantalla):
        # Bote simple en estilo flat
        # Casco
        casco_color = (200, 140, 80)
        casco_puntos = [
            (int(self.x - self.ancho // 2), int(self.y)),
            (int(self.x - self.ancho // 2 + 10), int(self.y - self.alto // 3)),
            (int(self.x - self.ancho // 4), int(self.y - self.alto)),
            (int(self.x + self.ancho // 4), int(self.y - self.alto)),
            (int(self.x + self.ancho // 2 - 10), int(self.y - self.alto // 3)),
            (int(self.x + self.ancho // 2), int(self.y)),
        ]

        pygame.draw.polygon(pantalla, casco_color, casco_puntos)
        pygame.draw.polygon(pantalla, NEGRO, casco_puntos, 2)

        # Banda decorativa naranja en el bote
        banda_rect = (int(self.x - self.ancho // 2 + 10), int(self.y - self.alto // 2 - 4), int(self.ancho - 20), 10)
        pygame.draw.rect(pantalla, (255, 140, 0), banda_rect, border_radius=5)

        # Personaje pescador (caricaturesco)
        jugador_x = self.x - 20
        jugador_y = self.y - self.alto + 30

        # Cabeza
        pygame.draw.circle(pantalla, (255, 200, 160), (int(jugador_x), int(jugador_y - 18)), 10)

        # Barba grande
        pygame.draw.ellipse(pantalla, (120, 80, 40), (int(jugador_x - 8), int(jugador_y - 6), 16, 12))

        # Gorro
        gorro_puntos = [(int(jugador_x - 12), int(jugador_y - 20)),
                        (int(jugador_x), int(jugador_y - 28)),
                        (int(jugador_x + 12), int(jugador_y - 20))]
        pygame.draw.polygon(pantalla, (220, 100, 100), gorro_puntos)

        # Ojos simples
        pygame.draw.circle(pantalla, NEGRO, (int(jugador_x - 3), int(jugador_y - 20)), 2)
        pygame.draw.circle(pantalla, NEGRO, (int(jugador_x + 3), int(jugador_y - 20)), 2)

        # Torso
        pygame.draw.rect(pantalla, (80, 140, 100), (int(jugador_x - 10), int(jugador_y - 2), 20, 18))

        # Piernas
        pygame.draw.line(pantalla, (40, 80, 120), (int(jugador_x - 4), int(jugador_y + 16)),
                        (int(jugador_x - 4), int(jugador_y + 28)), 4)
        pygame.draw.line(pantalla, (40, 80, 120), (int(jugador_x + 4), int(jugador_y + 16)),
                        (int(jugador_x + 4), int(jugador_y + 28)), 4)

        # Caña de pescar simple
        punto_agarre_x = jugador_x + 8
        punto_agarre_y = jugador_y + 2

        cana_largo = 95
        x_cana = punto_agarre_x + math.cos(self.angulo_cana) * cana_largo * (1 - self.flexion_cana * 0.3)
        y_cana = punto_agarre_y + math.sin(self.angulo_cana) * cana_largo * (1 - self.flexion_cana * 0.2)

        # Línea de la caña
        pygame.draw.line(pantalla, (100, 60, 30), (int(punto_agarre_x), int(punto_agarre_y)),
                        (int(x_cana), int(y_cana)), 3)

    def iniciar_lanzamiento(self):
        self.animando_lanzamiento = True
        self.tiempo_lanzamiento = 0
        try:
            potencia = getattr(self, 'potencia_lanzamiento', 50)
            self.flexion_cana = min(1.0, potencia / 100)
        except Exception:
            self.flexion_cana = 0.5

    def actualizar_lanzamiento(self):
        if self.animando_lanzamiento:
            self.tiempo_lanzamiento += 1
            if self.tiempo_lanzamiento >= 30:
                self.animando_lanzamiento = False
                self.tiempo_lanzamiento = 0

class Juego:
    def __init__(self):
        self.pantalla = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Acuariom - Juego de Pesca")
        self.reloj = pygame.time.Clock()
        self.fuente = pygame.font.Font(None, 36)
        self.fuente_pequeña = pygame.font.Font(None, 24)
        self.fuente_grande = pygame.font.Font(None, 60)
        self.fuente_titulo = pygame.font.Font(None, 48)

        self.estado = EstadoJuego.ESPERANDO
        self.potencia = 0
        self.incremento_potencia = 1.5
        self.angulo_cana_reposo = -math.pi / 2.5

        self.bote = Bote(140, SCREEN_HEIGHT - 120)
        self.bote.angulo_cana = self.angulo_cana_reposo
        self.bote.game_ref = self
        self.linea = None
        self.peces = []
        self.generar_peces(10)

        self.pescados = 0
        self.monedas = 0
        self.moneda_por_pez = 10
        self.mensaje = ""
        self.tiempo_mensaje = 0

        self.mouse_presionado = False
        self.angulo_lanzamiento = self.angulo_cana_reposo
        
        # Sistema de tienda mejorado
        self.upgrades = {
            'strength': 0,
            'weight': 0,
            'rebound': 0,
            'resistance': 0
        }
        self.upgrade_costs = {
            'strength': 25,
            'weight': 30,
            'rebound': 20,
            'resistance': 35
        }
        self.base_distance = 400
        
        # Profundidad actual del anzuelo
        self.profundidad_actual = 0
        
        # Sistema de recompensas
        self.peces_session = []
        self.tiempo_recompensa = 0
        self.jackpot_valor = 0
        self.botones_recompensa = []
        
        # Partículas (burbujas, chispas)
        self.particulas = []

    def generar_peces(self, cantidad):
        self.peces = []
        for _ in range(cantidad):
            x = random.randint(150, SCREEN_WIDTH - 150)
            y = random.randint(420, SCREEN_HEIGHT - 80)
            self.peces.append(Pez(x, y))
    
    def agregar_particula(self, x, y, tipo='burbuja'):
        self.particulas.append({'x': x, 'y': y, 'tipo': tipo, 'tiempo': 0, 'duracion': 60})
    
    def cambiar_a_recompensas(self):
        self.estado = EstadoJuego.RECOMPENSAS
        self.jackpot_valor = self.monedas
        self.tiempo_recompensa = 0
        # Botones
        self.botones_recompensa = [
            {'rect': pygame.Rect(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT - 120, 140, 50), 'label': 'Collect', 'multiplicador': 1},
            {'rect': pygame.Rect(SCREEN_WIDTH//2 + 20, SCREEN_HEIGHT - 120, 140, 50), 'label': 'Collect x3', 'multiplicador': 3}
        ]

    def actualizar(self):
        self.bote.actualizar_lanzamiento()

        for pez in self.peces:
            if pez.vivo:
                pez.actualizar()
        
        # Actualizar partículas
        for p in self.particulas[:]:
            p['tiempo'] += 1
            if p['tiempo'] > p['duracion']:
                self.particulas.remove(p)

        if self.linea:
            self.linea.actualizar()
            # Actualizar profundidad
            profundidad_px = self.linea.y_pos - 350
            self.profundidad_actual = max(0, profundidad_px / (SCREEN_HEIGHT - 350) * 200)

        if self.estado == EstadoJuego.CARGANDO:
            self.potencia = min(100, self.potencia + self.incremento_potencia)
            self.bote.flexion_cana = self.potencia / 100

            if self.potencia >= 100:
                self.incremento_potencia = -1.5
            elif self.potencia <= 0:
                self.incremento_potencia = 1.5

        if self.estado == EstadoJuego.LANZADO:
            self.linea.pez_enganchado = None

            for pez in self.peces:
                if pez.vivo:
                    distancia = math.hypot(pez.x - self.linea.x_pos,
                                         pez.y - self.linea.y_pos)
                    extra_hook = 5 + self.upgrades.get('weight', 0) * 3
                    if distancia < pez.radio + extra_hook:
                        self.linea.pez_enganchado = pez
                        self.estado = EstadoJuego.PESCANDO
                        break

        if self.estado == EstadoJuego.PESCANDO:
            if not self.mouse_presionado:
                pez = None
                if self.linea:
                    pez = self.linea.pez_enganchado
                if pez:
                    pez.vivo = False
                    self.pescados += 1
                    self.peces_session.append(pez)
                    self.monedas += self.moneda_por_pez
                    self.mensaje = f"+{self.moneda_por_pez} monedas! Pescados: {self.pescados}"
                    self.tiempo_mensaje = 120
                    
                    # Partículas
                    for _ in range(5):
                        self.agregar_particula(pez.x, pez.y, 'chispa')

                    self.peces.append(Pez(random.randint(150, SCREEN_WIDTH - 150),
                                         random.randint(420, SCREEN_HEIGHT - 80)))

                self.estado = EstadoJuego.ESPERANDO
                self.bote.flexion_cana = 0
                self.linea = None

        if self.tiempo_mensaje > 0:
            self.tiempo_mensaje -= 1

    def dibujar(self):
        if self.estado == EstadoJuego.RECOMPENSAS:
            self.dibujar_pantalla_recompensas()
            return
        
        # Fondo - Cielo degradado (amarillo)
        for y in range(0, 350):
            ratio = y / 350
            color_cielo = (
                int(CIELO_CLARO[0] + (CIELO_HORIZON[0] - CIELO_CLARO[0]) * ratio),
                int(CIELO_CLARO[1] + (CIELO_HORIZON[1] - CIELO_CLARO[1]) * ratio),
                int(CIELO_CLARO[2] + (CIELO_HORIZON[2] - CIELO_CLARO[2]) * ratio)
            )
            pygame.draw.line(self.pantalla, color_cielo, (0, y), (SCREEN_WIDTH, y))

        # Montañas simples en el fondo
        self.dibujar_montanas()
        
        # Árboles
        self.dibujar_arboles()

        # Nubes simples
        self.dibujar_nubes()

        # Sol en el horizonte
        sol_x = SCREEN_WIDTH // 2 + 150
        sol_y = 200
        pygame.draw.circle(self.pantalla, (255, 255, 100), (sol_x, sol_y), 80)

        # Línea del horizonte (agua)
        pygame.draw.line(self.pantalla, NEGRO, (0, 350), (SCREEN_WIDTH, 350), 2)

        # Fondo - Agua degradada
        for y in range(350, SCREEN_HEIGHT):
            ratio = (y - 350) / (SCREEN_HEIGHT - 350)
            color_agua = (
                int(AGUA_SURFACE[0] + (AGUA_PROFUNDA[0] - AGUA_SURFACE[0]) * ratio),
                int(AGUA_SURFACE[1] + (AGUA_PROFUNDA[1] - AGUA_SURFACE[1]) * ratio),
                int(AGUA_SURFACE[2] + (AGUA_PROFUNDA[2] - AGUA_SURFACE[2]) * ratio)
            )
            pygame.draw.line(self.pantalla, color_agua, (0, y), (SCREEN_WIDTH, y))

        # Rocas submarinas
        self.dibujar_rocas()

        # Plantas marinas simples
        self.dibujar_plantas()

        # Burbujas
        self.dibujar_burbujas()
        
        # Partículas
        self.dibujar_particulas()

        # Peces
        for pez in self.peces:
            pez.dibujar(self.pantalla)

        # Bote
        self.bote.dibujar(self.pantalla)

        # Línea
        if self.linea:
            self.linea.dibujar(self.pantalla)

        # Panel de interfaz superior oscuro
        panel_surf = pygame.Surface((SCREEN_WIDTH, 90))
        panel_surf.set_alpha(220)
        panel_surf.fill((20, 20, 40))
        self.pantalla.blit(panel_surf, (0, 0))

        # UI
        self.dibujar_ui()
        
        # Tienda a la izquierda
        self.dibujar_tienda()

        pygame.display.flip()
    
    def dibujar_montanas(self):
        # Montañas triangulares simples en el fondo
        montañas = [
            [(50, 350), (150, 150), (250, 350)],
            [(600, 350), (750, 120), (900, 350)],
        ]
        for montana in montañas:
            pygame.draw.polygon(self.pantalla, (100, 150, 80), montana)
            pygame.draw.polygon(self.pantalla, NEGRO, montana, 2)
    
    def dibujar_arboles(self):
        # Árboles simples para decoración
        arboles = [(100, 280), (850, 300)]
        for ax, ay in arboles:
            # Tronco
            pygame.draw.rect(self.pantalla, MARRON, (ax - 8, ay, 16, 70))
            # Follaje (círculos)
            pygame.draw.circle(self.pantalla, VERDE, (ax - 15, ay - 20), 25)
            pygame.draw.circle(self.pantalla, VERDE, (ax + 15, ay - 20), 25)
            pygame.draw.circle(self.pantalla, VERDE, (ax, ay - 40), 28)
    
    def dibujar_rocas(self):
        # Rocas submarinas simples a los lados
        rocas = [
            (80, 500, 60),
            (920, 480, 70),
            (150, 600, 50),
        ]
        for rx, ry, size in rocas:
            # Roca principal
            pygame.draw.circle(self.pantalla, (100, 100, 100), (rx, ry), size)
            pygame.draw.circle(self.pantalla, (80, 80, 80), (rx, ry), size, 2)
            # Pequeño hueco
            pygame.draw.circle(self.pantalla, (60, 60, 60), (rx - size//3, ry - size//3), size//4)

        pygame.display.flip()
    
    def dibujar_nubes(self):
        # Nubes simples (círculos)
        nubes = [
            (150, 80, 35),
            (500, 100, 30),
            (800, 70, 40),
        ]

        for x, y, size in nubes:
            pygame.draw.circle(self.pantalla, BLANCO, (x, y), size)
            pygame.draw.circle(self.pantalla, BLANCO, (x + size // 2, y - 10), size - 5)
            pygame.draw.circle(self.pantalla, BLANCO, (x + size, y), size)

    def dibujar_plantas(self):
        # Plantas marinas simples
        plantas = [
            (50, 500, 100),
            (200, 550, 80),
            (900, 480, 110),
            (750, 520, 90),
        ]

        for x, y, alto in plantas:
            # Tallo simple ondulante
            num_puntos = 10
            puntos = []
            for i in range(num_puntos):
                px = x + math.sin(i * 0.3) * 8
                py = y - (alto / num_puntos) * i
                puntos.append((int(px), int(py)))
            
            for i in range(len(puntos) - 1):
                pygame.draw.line(self.pantalla, VERDE_OSCURO, puntos[i], puntos[i+1], 6)
            
            # Pequeñas hojas
            pygame.draw.line(self.pantalla, VERDE_OSCURO, (x - 10, y - 20), (x - 25, y - 40), 4)
            pygame.draw.line(self.pantalla, VERDE_OSCURO, (x + 10, y - 50), (x + 25, y - 70), 4)

    def dibujar_burbujas(self):
        # Burbujas flotantes simples
        ticks = int(pygame.time.get_ticks() / 50)

        for i in range(0, SCREEN_WIDTH, 200):
            x = (i + ticks) % SCREEN_WIDTH
            y = SCREEN_HEIGHT - 100 - (ticks + i // 50) % 300
            if 350 < y < SCREEN_HEIGHT:
                pygame.draw.circle(self.pantalla, (100, 200, 255), (x, y), 5, 1)
    
    def dibujar_particulas(self):
        for p in self.particulas:
            progreso = p['tiempo'] / p['duracion']
            if p['tipo'] == 'burbuja':
                pygame.draw.circle(self.pantalla, (100, 200, 255), (int(p['x']), int(p['y'])), 4, 1)
            elif p['tipo'] == 'chispa':
                # Chispas doradas
                alpha = int(255 * (1 - progreso))
                color = (255, 220, 0)
                pygame.draw.circle(self.pantalla, color, (int(p['x']), int(p['y'])), 3)

    def dibujar_ui(self):
        # Medidor de potencia / lanzamiento mejorado
        medidor_x = 20
        medidor_y = 15
        medidor_ancho = 280
        medidor_alto = 25

        # Fondo del medidor
        pygame.draw.rect(self.pantalla, (50, 50, 80), (medidor_x, medidor_y, medidor_ancho, medidor_alto))
        pygame.draw.rect(self.pantalla, (150, 150, 200), (medidor_x, medidor_y, medidor_ancho, medidor_alto), 2)

        if self.estado == EstadoJuego.CARGANDO:
            relleno_ancho = (self.potencia / 100) * medidor_ancho
            
            # Colores según potencia (rojo malo, amarillo medio, verde perfecto)
            if self.potencia < 33:
                color_relleno = (0, 200, 100)  # Verde
            elif self.potencia < 66:
                color_relleno = (255, 200, 0)  # Amarillo
            else:
                color_relleno = (255, 0, 0)  # Rojo

            pygame.draw.rect(self.pantalla, color_relleno, (medidor_x, medidor_y, relleno_ancho, medidor_alto))
            
            # Marcas de zonas (verde, amarillo, rojo)
            marca1 = medidor_x + (medidor_ancho // 3)
            marca2 = medidor_x + (medidor_ancho * 2 // 3)
            pygame.draw.line(self.pantalla, BLANCO, (marca1, medidor_y), (marca1, medidor_y + medidor_alto), 1)
            pygame.draw.line(self.pantalla, BLANCO, (marca2, medidor_y), (marca2, medidor_y + medidor_alto), 1)
            
            # Texto
            texto_potencia = self.fuente.render(f"{int(self.potencia)}%", True, BLANCO)
            self.pantalla.blit(texto_potencia, (medidor_x + medidor_ancho + 10, medidor_y))
            
            # Indicación de zona
            if self.potencia < 33:
                zona_texto = self.fuente_pequeña.render("PERFECT!", True, (0, 200, 100))
            elif self.potencia < 66:
                zona_texto = self.fuente_pequeña.render("Good", True, (255, 200, 0))
            else:
                zona_texto = self.fuente_pequeña.render("Too much!", True, (255, 0, 0))
            self.pantalla.blit(zona_texto, (medidor_x + medidor_ancho + 10, medidor_y + 30))
        else:
            if self.estado == EstadoJuego.ESPERANDO:
                texto_estado = self.fuente_pequeña.render("Haz CLICK y mantén para cargar", True, BLANCO)
            else:
                texto_estado = self.fuente_pequeña.render("Pescando...", True, (100, 255, 100))
            self.pantalla.blit(texto_estado, (medidor_x, medidor_y + 5))

        # Profundidad - Medidor
        prof_x = SCREEN_WIDTH - 120
        prof_y = 15
        
        prof_texto = self.fuente_pequeña.render(f"Profundidad:", True, BLANCO)
        self.pantalla.blit(prof_texto, (prof_x, prof_y))
        
        prof_valor = self.fuente.render(f"{int(self.profundidad_actual)} ft", True, (100, 200, 255))
        self.pantalla.blit(prof_valor, (prof_x, prof_y + 25))
        
        # Barra de profundidad
        barra_prof_h = 50
        barra_prof_w = 15
        pygame.draw.rect(self.pantalla, (50, 50, 80), (prof_x + 110, prof_y, barra_prof_w, barra_prof_h))
        pygame.draw.rect(self.pantalla, (100, 200, 255), (prof_x + 110, prof_y, barra_prof_w, barra_prof_h), 1)
        
        if self.profundidad_actual > 0:
            relleno_prof = (self.profundidad_actual / 200) * barra_prof_h
            pygame.draw.rect(self.pantalla, (100, 200, 255), (prof_x + 110, prof_y + barra_prof_h - relleno_prof, barra_prof_w, relleno_prof))

        # Estadísticas - Centro
        stats_x = SCREEN_WIDTH // 2 - 100
        stats_y = 15

        texto_pescados = self.fuente.render(f"🐟 {self.pescados}", True, (255, 200, 0))
        texto_monedas = self.fuente.render(f"💰 {self.monedas}", True, (255, 200, 0))

        self.pantalla.blit(texto_pescados, (stats_x, stats_y))
        self.pantalla.blit(texto_monedas, (stats_x, stats_y + 35))

        # Mensaje de logro
        if self.tiempo_mensaje > 0:
            alpha = int(255 * (self.tiempo_mensaje / 120))
            texto_mensaje = self.fuente.render(self.mensaje, True, (100, 255, 100))
            self.pantalla.blit(texto_mensaje, (SCREEN_WIDTH // 2 - 150, 120))

        # Estado PESCANDO
        if self.estado == EstadoJuego.PESCANDO:
            texto_pescando = self.fuente_grande.render("¡PESCADO!", True, (255, 100, 0))
            self.pantalla.blit(texto_pescando, (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2 - 50))

            instruccion = self.fuente_pequeña.render("Haz CLICK para retirar", True, BLANCO)
            self.pantalla.blit(instruccion, (SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 + 20))
    
    def dibujar_tienda(self):
        # Panel de tienda a la izquierda
        tienda_x = 10
        tienda_y = 110
        tienda_w = 120
        tienda_h = SCREEN_HEIGHT - 130
        
        # Fondo
        tienda_surf = pygame.Surface((tienda_w, tienda_h))
        tienda_surf.set_alpha(200)
        tienda_surf.fill((40, 30, 50))
        self.pantalla.blit(tienda_surf, (tienda_x, tienda_y))
        pygame.draw.rect(self.pantalla, (150, 100, 200), (tienda_x, tienda_y, tienda_w, tienda_h), 2)
        
        # Título
        titulo = self.fuente_pequeña.render("MEJORAS", True, (200, 150, 255))
        self.pantalla.blit(titulo, (tienda_x + 10, tienda_y + 8))
        
        # Mejoras disponibles
        mejoras_info = [
            ('Strength', 'Fuerza', 'strength'),
            ('Weight', 'Peso', 'weight'),
            ('Rebound', 'Rebote', 'rebound'),
            ('Resistance', 'Resist.', 'resistance'),
        ]
        
        item_h = 35
        for idx, (nombre_en, nombre_esp, key) in enumerate(mejoras_info):
            y_pos = tienda_y + 40 + idx * item_h
            
            # Nivel actual
            nivel = self.upgrades.get(key, 0)
            costo = self.upgrade_costs.get(key, 0)
            
            # Nombre
            texto_name = self.fuente_pequeña.render(nombre_esp, True, (255, 200, 100))
            self.pantalla.blit(texto_name, (tienda_x + 10, y_pos))
            
            # Nivel y costo
            texto_info = pygame.font.Font(None, 18).render(f"Lv{nivel} ${costo}", True, (100, 200, 50))
            self.pantalla.blit(texto_info, (tienda_x + 10, y_pos + 16))
    
    def dibujar_pantalla_recompensas(self):
        # Pantalla de recompensas con jackpot
        self.pantalla.fill((20, 20, 40))
        
        # Panel de fondo
        panel_surf = pygame.Surface((SCREEN_WIDTH - 100, SCREEN_HEIGHT - 100))
        panel_surf.set_alpha(220)
        panel_surf.fill((30, 40, 60))
        self.pantalla.blit(panel_surf, (50, 50))
        pygame.draw.rect(self.pantalla, (150, 200, 255), (50, 50, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 100), 3)
        
        # Título
        titulo = self.fuente_titulo.render("¡RECOMPENSAS!", True, (255, 200, 0))
        self.pantalla.blit(titulo, (SCREEN_WIDTH // 2 - 150, 80))
        
        # Estadísticas
        stats_texto = [
            f"Peces atrapados: {len(self.peces_session)}",
            f"Monedas: {self.jackpot_valor}",
        ]
        
        for idx, texto in enumerate(stats_texto):
            t = self.fuente.render(texto, True, (100, 255, 100))
            self.pantalla.blit(t, (SCREEN_WIDTH // 2 - 100, 180 + idx * 50))
        
        # Barra de progreso jackpot
        barra_x = SCREEN_WIDTH // 2 - 150
        barra_y = 320
        barra_ancho = 300
        barra_alto = 40
        
        pygame.draw.rect(self.pantalla, (50, 50, 80), (barra_x, barra_y, barra_ancho, barra_alto))
        
        progreso = min(1.0, self.jackpot_valor / 500)
        relleno = progreso * barra_ancho
        pygame.draw.rect(self.pantalla, (255, 200, 0), (barra_x, barra_y, relleno, barra_alto))
        pygame.draw.rect(self.pantalla, (255, 200, 0), (barra_x, barra_y, barra_ancho, barra_alto), 2)
        
        # Texto en barra
        texto_barra = self.fuente.render(f"JACKPOT: {int(progreso * 100)}%", True, NEGRO)
        self.pantalla.blit(texto_barra, (barra_x + barra_ancho // 2 - 80, barra_y + 8))
        
        # Botones
        for btn in self.botones_recompensa:
            rect = btn['rect']
            pygame.draw.rect(self.pantalla, (100, 150, 200), rect)
            pygame.draw.rect(self.pantalla, BLANCO, rect, 3)
            
            texto = self.fuente_pequeña.render(btn['label'], True, BLANCO)
            self.pantalla.blit(texto, (rect.x + 20, rect.y + 12))
        
        pygame.display.flip()

    def manejar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return False

            if evento.type == pygame.MOUSEBUTTONDOWN:
                self.mouse_presionado = True
                mx, my = pygame.mouse.get_pos()
                
                # Si estamos en pantalla de recompensas
                if self.estado == EstadoJuego.RECOMPENSAS:
                    for btn in self.botones_recompensa:
                        if btn['rect'].collidepoint(mx, my):
                            # Multiplicar monedas
                            self.monedas *= btn['multiplicador']
                            # Volver a juego normal
                            self.estado = EstadoJuego.ESPERANDO
                            self.potencia = 0
                            self.profundidad_actual = 0
                            self.peces_session = []
                    return True

                if self.estado == EstadoJuego.ESPERANDO:
                    self.estado = EstadoJuego.CARGANDO
                    self.potencia = 0
                    self.incremento_potencia = 1.5

                    dx = mx - self.bote.x
                    dy = my - (self.bote.y - 70)
                    self.angulo_lanzamiento = math.atan2(dy, dx)
                    self.bote.angulo_cana = self.angulo_lanzamiento

                elif self.estado == EstadoJuego.LANZADO:
                    self.estado = EstadoJuego.ESPERANDO
                    self.linea = None
                    self.bote.angulo_cana = self.angulo_cana_reposo
                    self.bote.flexion_cana = 0
                    self.bote.animando_lanzamiento = False

            if evento.type == pygame.MOUSEBUTTONUP:
                self.mouse_presionado = False

                if self.estado == EstadoJuego.CARGANDO:
                    distancia_base = self.base_distance + self.upgrades.get('strength', 0) * 100
                    self.linea = Linea(self.bote.x, self.bote.y - 70, self.potencia,
                                      self.angulo_lanzamiento, distancia_base)
                    self.bote.iniciar_lanzamiento()
                    self.estado = EstadoJuego.LANZADO

            if evento.type == pygame.MOUSEMOTION and self.estado == EstadoJuego.CARGANDO:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                dx = mouse_x - self.bote.x
                dy = mouse_y - (self.bote.y - 70)
                self.angulo_lanzamiento = math.atan2(dy, dx)
                self.bote.angulo_cana = self.angulo_lanzamiento
            
            # Tecla Q para ir a recompensas (para testing)
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_q:
                    self.cambiar_a_recompensas()

        return True

    def correr(self):
        corriendo = True
        while corriendo:
            corriendo = self.manejar_eventos()
            self.actualizar()
            self.dibujar()
            self.reloj.tick(FPS)

        pygame.quit()

if __name__ == "__main__":
    juego = Juego()
    juego.correr()
