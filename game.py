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
    VIENDO_ANUNCIO = 6

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

            # Si alcanza la superficie del agua, entra pero sigue moviéndose
            if self.y_pos >= 350:
                self.en_agua = True
                # Reducir velocidad al entrar al agua pero mantener dirección
                self.vx *= 0.6
                self.vy = abs(self.vy) * 0.3  # Hundir lentamente
        else:
            # En el agua: continuar moviéndose horizontalmente y hundiéndose
            self.x_pos += self.vx
            self.y_pos += self.vy
            
            # Fricción del agua
            self.vx *= 0.95
            self.vy += 0.3  # Gravedad en el agua (más lento)
            
            # Limitar profundidad máxima
            if self.y_pos > SCREEN_HEIGHT - 50:
                self.y_pos = SCREEN_HEIGHT - 50
                self.vy = 0

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
        # Si el bote tiene referencia al juego y hay una línea lanzada, apuntar la caña al anzuelo
        ang_actual = self.angulo_cana
        try:
            # Sólo apuntar al anzuelo cuando la línea está lanzada o pescando
            if hasattr(self, 'game_ref') and self.game_ref and self.game_ref.linea and self.game_ref.estado in (EstadoJuego.LANZADO, EstadoJuego.PESCANDO):
                lx = self.game_ref.linea.x_pos
                ly = self.game_ref.linea.y_pos
                ang_actual = math.atan2(ly - punto_agarre_y, lx - punto_agarre_x)
            else:
                ang_actual = self.angulo_cana
        except Exception:
            ang_actual = self.angulo_cana

        x_cana = punto_agarre_x + math.cos(ang_actual) * cana_largo * (1 - self.flexion_cana * 0.3)
        y_cana = punto_agarre_y + math.sin(ang_actual) * cana_largo * (1 - self.flexion_cana * 0.2)
        # Línea de la caña - dibujamos con contorno para mayor visibilidad
        pygame.draw.line(pantalla, NEGRO, (int(punto_agarre_x), int(punto_agarre_y)),
                        (int(x_cana), int(y_cana)), 5)
        pygame.draw.line(pantalla, (120, 80, 50), (int(punto_agarre_x), int(punto_agarre_y)),
                        (int(x_cana), int(y_cana)), 3)

        # Dibujar línea de pesca conectando al anzuelo si existe
        try:
            if hasattr(self, 'game_ref') and self.game_ref and self.game_ref.linea:
                hook_x = int(self.game_ref.linea.x_pos)
                hook_y = int(self.game_ref.linea.y_pos)
                pygame.draw.line(pantalla, NEGRO, (int(punto_agarre_x), int(punto_agarre_y)), (hook_x, hook_y), 1)
        except Exception:
            pass

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
        
        # Botones de mejora (se crean al inicio)
        self.upgrade_buttons = []
        self.crear_botones_mejoras()
        
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
    
    def crear_botones_mejoras(self):
        """Crear botones de mejora con sus posiciones"""
        self.upgrade_buttons = []
        tienda_x = 15
        tienda_y = 120
        item_h = 65
        
        mejoras = [
            ('strength', 'STRENGTH', '🔧', (180, 80, 80), 'Fisherman is 25% stronger'),
            ('weight', 'WEIGHT', '⚓', (80, 160, 180), 'Hook sinks 15% deeper'),
            ('rebound', 'REBOUND', '↺', (80, 180, 80), 'Hook bounces 5% better'),
            ('resistance', 'RESISTANCE', '🛡', (200, 140, 80), 'Hook up to 1 more fishes'),
        ]
        
        for idx, (key, name, icon, color, desc) in enumerate(mejoras):
            y_pos = tienda_y + idx * item_h
            btn_rect = pygame.Rect(tienda_x, y_pos, 280, 55)
            btn_x3_rect = pygame.Rect(tienda_x + 290, y_pos, 65, 55)
            
            self.upgrade_buttons.append({
                'key': key,
                'name': name,
                'icon': icon,
                'color': color,
                'desc': desc,
                'rect': btn_rect,
                'x3_rect': btn_x3_rect
            })
    
    def comprar_mejora(self, key, multiplicador=1):
        """Comprar una mejora (multiplicador 1 normal, 3 con anuncio)"""
        costo_base = self.upgrade_costs[key]
        costo_total = costo_base * multiplicador
        
        if multiplicador == 1:
            # Compra normal con monedas
            if self.monedas >= costo_total:
                self.monedas -= costo_total
                self.upgrades[key] += 1
                self.upgrade_costs[key] = int(costo_base * 1.5)  # Incrementar costo
                self.mensaje = f"¡Mejora comprada! {self.upgrades[key]}"
                self.tiempo_mensaje = 120
                return True
        else:
            # Compra x3 "viendo anuncio" (simulado - gratis)
            self.upgrades[key] += 3
            self.mensaje = f"¡Mejora x3! Ahora nivel {self.upgrades[key]}"
            self.tiempo_mensaje = 120
            return True
        return False

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

            # Reeling: si el jugador mantiene el click mientras la línea está lanzada, acercar el anzuelo
            if self.mouse_presionado and self.estado in (EstadoJuego.LANZADO, EstadoJuego.PESCANDO):
                # velocidad base de reel (pixeles por update)
                base_reel = 2.0
                fuerza = 1.0 + self.upgrades.get('strength', 0) * 0.25
                velocidad = base_reel * fuerza
                # acercar la posición del anzuelo hacia el bote
                dir_x = (self.bote.x - self.linea.x_pos)
                dir_y = ((self.bote.y - 70) - self.linea.y_pos)
                dist = math.hypot(dir_x, dir_y) + 0.001
                self.linea.x_pos += dir_x / dist * velocidad
                self.linea.y_pos += dir_y / dist * velocidad
                # agregar burbujas mientras reeleando
                if random.random() < 0.08:
                    self.agregar_particula(self.linea.x_pos, self.linea.y_pos, 'burbuja')

                # Si la línea llega cerca del bote, recuperarla automáticamente
                if math.hypot(self.linea.x_pos - self.bote.x, self.linea.y_pos - (self.bote.y - 70)) < 30:
                    # si hay pez enganchado, pasar a PESCANDO para permitir retirar
                    if self.linea.pez_enganchado:
                        self.estado = EstadoJuego.PESCANDO
                    else:
                        self.linea = None
                        self.estado = EstadoJuego.ESPERANDO
                        self.bote.flexion_cana = 0

        # Si no hay línea, suavemente volver el ángulo de la caña a reposo
        if not self.linea:
            diff = self.angulo_cana_reposo - self.bote.angulo_cana
            # normalizar ángulo entre -pi..pi for smooth interpolation
            while diff > math.pi:
                diff -= 2 * math.pi
            while diff < -math.pi:
                diff += 2 * math.pi
            self.bote.angulo_cana += diff * 0.15

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

        # Olas sutiles en la superficie (superposición semi-transparente)
        wave_surf = pygame.Surface((SCREEN_WIDTH, 60), pygame.SRCALPHA)
        ticks = pygame.time.get_ticks() / 500.0
        for x in range(0, SCREEN_WIDTH, 6):
            y_off = math.sin((x / 60.0) + ticks) * 6
            alpha = 40 + int(30 * math.sin((x / 120.0) + ticks * 0.5))
            color = (255, 255, 255, max(10, alpha))
            pygame.draw.circle(wave_surf, color, (x, int(30 + y_off)), 4)
        self.pantalla.blit(wave_surf, (0, 340))

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

        # Línea (dibujamos la línea antes del bote para que la caña esté encima)
        if self.linea:
            self.linea.dibujar(self.pantalla)

        # Bote (dibujar al final para que la caña quede visible encima de la línea)
        self.bote.dibujar(self.pantalla)

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
            
            # Colores según potencia (verde perfecto, amarillo medio, rojo exceso)
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

            # MEDIDOR DE ARCO VISUAL - como en la imagen de referencia
            try:
                # Centro del arco (cerca de la punta de la caña)
                center_x = int(self.bote.x + 50)
                center_y = int(self.bote.y - 80)
                radius_outer = 200
                radius_inner = 140
                
                # Superficie transparente para dibujar el arco
                arc_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                
                # Ángulo base (apuntando hacia donde el jugador señaló)
                base_angle = self.angulo_lanzamiento
                arc_span = 1.0  # Amplitud total del arco en radianes
                
                # Dibujar las 3 zonas del arco: ROJO (izq), AMARILLO, VERDE (centro), AMARILLO, ROJO (der)
                zones = [
                    # (ángulo_inicio_offset, ángulo_fin_offset, color, label)
                    (-arc_span/2, -arc_span/3, (255, 80, 80, 180), ""),  # Rojo izquierda
                    (-arc_span/3, -arc_span/6, (255, 200, 0, 180), ""),  # Amarillo izquierda
                    (-arc_span/6, arc_span/6, (50, 255, 50, 180), "PERFECT"),  # Verde centro
                    (arc_span/6, arc_span/3, (255, 200, 0, 180), ""),  # Amarillo derecha
                    (arc_span/3, arc_span/2, (255, 80, 80, 180), "")   # Rojo derecha
                ]
                
                for a_start, a_end, color, label in zones:
                    # Dibujar segmento del arco
                    points = [(center_x, center_y)]
                    steps = 20
                    
                    # Arco exterior
                    for i in range(steps + 1):
                        t = i / steps
                        angle = base_angle + a_start + (a_end - a_start) * t
                        x = center_x + math.cos(angle) * radius_outer
                        y = center_y + math.sin(angle) * radius_outer
                        points.append((int(x), int(y)))
                    
                    # Arco interior (de vuelta)
                    for i in range(steps, -1, -1):
                        t = i / steps
                        angle = base_angle + a_start + (a_end - a_start) * t
                        x = center_x + math.cos(angle) * radius_inner
                        y = center_y + math.sin(angle) * radius_inner
                        points.append((int(x), int(y)))
                    
                    pygame.draw.polygon(arc_surf, color, points)
                    # Contorno
                    pygame.draw.polygon(arc_surf, (0, 0, 0, 100), points, 2)
                
                self.pantalla.blit(arc_surf, (0, 0))
                
                # Dibujar indicador de potencia actual (aguja/flecha)
                # La potencia mapea a una posición en el arco
                # 0% = extremo izquierdo, 50% = centro, 100% = extremo derecho
                potencia_normalizada = self.potencia / 100.0
                indicator_angle = base_angle + (-arc_span/2) + (arc_span * potencia_normalizada)
                
                # Aguja/indicador
                indicator_length = radius_outer + 20
                ind_x = center_x + math.cos(indicator_angle) * indicator_length
                ind_y = center_y + math.sin(indicator_angle) * indicator_length
                
                # Dibujar línea indicadora gruesa
                pygame.draw.line(self.pantalla, (255, 255, 255), 
                               (center_x, center_y), (int(ind_x), int(ind_y)), 6)
                pygame.draw.line(self.pantalla, (0, 0, 0), 
                               (center_x, center_y), (int(ind_x), int(ind_y)), 4)
                
                # Círculo en el centro
                pygame.draw.circle(self.pantalla, (255, 255, 255), (center_x, center_y), 8)
                pygame.draw.circle(self.pantalla, (0, 0, 0), (center_x, center_y), 6)
                
            except Exception as e:
                pass
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

        # Profundidad grande arriba en el centro (ej. '89 ft')
        profundidad_texto = self.fuente_titulo.render(f"{int(self.profundidad_actual)} ft", True, (30, 140, 200))
        self.pantalla.blit(profundidad_texto, (SCREEN_WIDTH//2 - profundidad_texto.get_width()//2, 10))

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
        """Dibujar panel de tienda con botones de mejoras clicables"""
        # Fondo de la tienda
        tienda_x = 10
        tienda_y = 100
        tienda_w = 370
        tienda_h = 330
        
        # Panel principal con borde celeste
        pygame.draw.rect(self.pantalla, (40, 40, 60), (tienda_x, tienda_y, tienda_w, tienda_h))
        pygame.draw.rect(self.pantalla, (80, 200, 255), (tienda_x, tienda_y, tienda_w, tienda_h), 4)
        
        # Monedas arriba
        monedas_panel = pygame.Rect(tienda_x + 10, tienda_y - 50, 100, 40)
        pygame.draw.rect(self.pantalla, (60, 60, 80), monedas_panel, border_radius=8)
        pygame.draw.rect(self.pantalla, (100, 220, 255), monedas_panel, 3, border_radius=8)
        
        monedas_texto = self.fuente_pequeña.render(f"{self.monedas}", True, (255, 220, 100))
        coin_icon = self.fuente_pequeña.render("💰", True, BLANCO)
        self.pantalla.blit(coin_icon, (monedas_panel.x + 8, monedas_panel.y + 8))
        self.pantalla.blit(monedas_texto, (monedas_panel.x + 40, monedas_panel.y + 10))
        
        # Dibujar cada botón de mejora
        for btn in self.upgrade_buttons:
            key = btn['key']
            rect = btn['rect']
            x3_rect = btn['x3_rect']
            nivel = self.upgrades[key]
            costo = self.upgrade_costs[key]
            tiene_dinero = self.monedas >= costo
            
            # Color del botón principal (gris si no tiene dinero, color normal si sí)
            if tiene_dinero:
                color_fondo = btn['color']
                color_borde = (min(255, btn['color'][0] + 40), min(255, btn['color'][1] + 40), min(255, btn['color'][2] + 40))
            else:
                color_fondo = (100, 120, 130)  # Gris/celeste apagado
                color_borde = (140, 160, 170)
            
            # Botón principal
            pygame.draw.rect(self.pantalla, color_fondo, rect, border_radius=8)
            pygame.draw.rect(self.pantalla, color_borde, rect, 3, border_radius=8)
            
            # Icono/emoji más pequeño
            icono = self.fuente.render(btn['icon'], True, BLANCO)
            self.pantalla.blit(icono, (rect.x + 8, rect.y + 10))
            
            # Nombre de la mejora
            nombre_texto = self.fuente_pequeña.render(btn['name'], True, BLANCO)
            self.pantalla.blit(nombre_texto, (rect.x + 55, rect.y + 8))
            
            # Costo con moneda
            costo_texto = pygame.font.Font(None, 20).render(f"💰 {costo}", True, (255, 220, 100))
            self.pantalla.blit(costo_texto, (rect.x + 200, rect.y + 8))
            
            # Descripción más pequeña
            desc_font = pygame.font.Font(None, 18)
            desc_texto = desc_font.render(btn['desc'], True, (200, 200, 200) if tiene_dinero else (140, 140, 140))
            self.pantalla.blit(desc_texto, (rect.x + 55, rect.y + 32))
            
            # Botón x3 (con anuncio) más pequeño
            if tiene_dinero:
                x3_color = (100, 200, 100)  # Verde
                x3_borde = (150, 255, 150)
            else:
                x3_color = (100, 120, 130)
                x3_borde = (140, 160, 170)
            
            pygame.draw.rect(self.pantalla, x3_color, x3_rect, border_radius=8)
            pygame.draw.rect(self.pantalla, x3_borde, x3_rect, 3, border_radius=8)
            
            # Icono de video/anuncio
            video_icon = self.fuente_pequeña.render("📺", True, BLANCO)
            self.pantalla.blit(video_icon, (x3_rect.x + 8, x3_rect.y + 5))
            
            x3_texto = pygame.font.Font(None, 20).render("x3", True, BLANCO)
            self.pantalla.blit(x3_texto, (x3_rect.x + 20, x3_rect.y + 28))
            
            upgrade_label = pygame.font.Font(None, 16).render("Upgrade", True, BLANCO)
            self.pantalla.blit(upgrade_label, (x3_rect.x + 4, x3_rect.y + 42))
    
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
                
                # Detectar clicks en botones de mejoras
                for btn in self.upgrade_buttons:
                    if btn['rect'].collidepoint(mx, my):
                        # Click en botón principal (compra normal)
                        self.comprar_mejora(btn['key'], multiplicador=1)
                        return True
                    elif btn['x3_rect'].collidepoint(mx, my):
                        # Click en botón x3 (ver anuncio - gratis)
                        self.comprar_mejora(btn['key'], multiplicador=3)
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
