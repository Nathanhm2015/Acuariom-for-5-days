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

# Colores
AGUA_CLARO = (135, 206, 235)
AGUA_OSCURO = (30, 144, 255)
CIELO = (135, 206, 250)
BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)
AMARILLO = (255, 255, 0)
NARANJA = (255, 165, 0)
ROJO = (255, 0, 0)
VERDE = (0, 255, 0)
GRIS = (128, 128, 128)
MARRON = (139, 69, 19)

class EstadoJuego(Enum):
    ESPERANDO = 1
    CARGANDO = 2
    LANZADO = 3
    PESCANDO = 4

class Pez:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-1.5, 1.5)
        self.vy = random.uniform(-0.5, 0.5)
        self.radio = random.randint(10, 20)
        self.tipo = random.choice(['dorado', 'azul', 'rojo', 'naranja', 'verde'])
        self.colores = {
            'dorado': (255, 215, 0),
            'azul': (30, 144, 255),
            'rojo': (220, 50, 50),
            'naranja': (255, 140, 0),
            'verde': (60, 180, 75)
        }
        self.color_primario = self.colores[self.tipo]
        self.vivo = True
        self.frame = 0
        self.rotacion = 0
    
    def actualizar(self):
        self.x += self.vx
        self.y += self.vy
        self.frame += 1
        
        # Cambiar rotación basada en dirección
        if self.vx < 0:
            self.rotacion = math.pi  # Voltear hacia la izquierda
        else:
            self.rotacion = 0  # Voltear hacia la derecha
        
        # Rebotar en bordes con más espacio
        if self.x - self.radio < 100 or self.x + self.radio > SCREEN_WIDTH - 100:
            self.vx *= -1
        if self.y - self.radio < 400 or self.y + self.radio > SCREEN_HEIGHT - 40:
            self.vy *= -1
        
        # Mantener en límites
        self.x = max(100 + self.radio, min(SCREEN_WIDTH - 100 - self.radio, self.x))
        self.y = max(400 + self.radio, min(SCREEN_HEIGHT - 40 - self.radio, self.y))
    
    def dibujar(self, pantalla):
        if self.vivo:
            # Aplicar rotación
            if self.rotacion != 0:
                cos_r = math.cos(self.rotacion)
                sin_r = math.sin(self.rotacion)
            else:
                cos_r = 1
                sin_r = 0
            
            # Sombra
            pygame.draw.ellipse(pantalla, (0, 0, 0, 40), (int(self.x - self.radio - 2), 
                                                          int(self.y + self.radio + 2), 
                                                          (self.radio + 2) * 2, 5))
            
            # Cuerpo principal del pez (elipse)
            cuerpo_ancho = int(self.radio * 2.5)
            cuerpo_alto = int(self.radio * 1.5)
            
            # Dibujar cuerpo con brillo
            pygame.draw.ellipse(pantalla, self.color_primario, 
                               (int(self.x - cuerpo_ancho // 2), int(self.y - cuerpo_alto // 2),
                                cuerpo_ancho, cuerpo_alto))
            
            # Escamas (patrón de líneas)
            for i in range(3):
                pygame.draw.line(pantalla, tuple(max(0, c - 40) for c in self.color_primario),
                               (int(self.x - cuerpo_ancho // 2 + 5), int(self.y - cuerpo_alto // 2 + i * 8)),
                               (int(self.x - cuerpo_ancho // 2 + 5), int(self.y + cuerpo_alto // 2 - i * 8)), 1)
            
            # Brillo en el cuerpo
            pygame.draw.ellipse(pantalla, tuple(min(255, c + 80) for c in self.color_primario),
                               (int(self.x - cuerpo_ancho // 2 + 2), int(self.y - cuerpo_alto // 3),
                                int(cuerpo_ancho * 0.4), int(cuerpo_alto * 0.4)), 2)
            
            # Aleta dorsal
            aleta_altura = self.radio // 2
            aleta_x1 = int(self.x - cuerpo_ancho // 4)
            aleta_y1 = int(self.y - cuerpo_alto // 2)
            aleta_x2 = int(self.x - cuerpo_ancho // 6)
            aleta_y2 = int(self.y - cuerpo_alto // 2 - aleta_altura)
            aleta_x3 = int(self.x)
            aleta_y3 = int(self.y - cuerpo_alto // 2)
            
            pygame.draw.polygon(pantalla, tuple(max(0, c - 60) for c in self.color_primario),
                               [(aleta_x1, aleta_y1), (aleta_x2, aleta_y2), (aleta_x3, aleta_y3)])
            
            # Cola ondulante
            ondulacion = math.sin(self.frame * 0.15) * 4
            cola_x1 = int(self.x + cuerpo_ancho // 2)
            cola_y1 = int(self.y - cuerpo_alto // 3 + ondulacion)
            cola_x2 = int(self.x + cuerpo_ancho // 2 + self.radio)
            cola_y2 = int(self.y + ondulacion * 1.5)
            cola_x3 = int(self.x + cuerpo_ancho // 2)
            cola_y3 = int(self.y + cuerpo_alto // 3 + ondulacion)
            
            pygame.draw.polygon(pantalla, self.color_primario,
                               [(cola_x1, cola_y1), (cola_x2, cola_y2), (cola_x3, cola_y3)])
            
            # Aleta ventral
            pygame.draw.polygon(pantalla, tuple(max(0, c - 60) for c in self.color_primario),
                               [(int(self.x - cuerpo_ancho // 4), int(self.y + cuerpo_alto // 2)),
                                (int(self.x - cuerpo_ancho // 6), int(self.y + cuerpo_alto // 2 + self.radio // 3)),
                                (int(self.x), int(self.y + cuerpo_alto // 2))])
            
            # Ojo
            ojo_x = int(self.x - cuerpo_ancho // 3)
            ojo_y = int(self.y - cuerpo_alto // 4)
            pygame.draw.circle(pantalla, BLANCO, (ojo_x, ojo_y), 3)
            pygame.draw.circle(pantalla, (50, 50, 50), (ojo_x, ojo_y), 2)

class Linea:
    def __init__(self, x_inicio, y_inicio, potencia, angulo, distancia_base=400):
        self.x_inicio = x_inicio
        self.y_inicio = y_inicio
        self.potencia = potencia  # 0 a 100
        self.angulo = angulo

        # Distancia máxima calculada según potencia y base (puede crecer con mejoras)
        self.distancia_max = (potencia / 100) * distancia_base

        # Posición dinámica del anzuelo (inicia en la punta de la caña)
        self.x_pos = x_inicio
        self.y_pos = y_inicio

        # Velocidad inicial basada en potencia (permite arco alto cuando potencia es alta)
        max_speed = 40.0
        speed = (potencia / 100) * max_speed
        self.vx = math.cos(angulo) * speed
        self.vy = math.sin(angulo) * speed

        # En nuestro sistema Y crece hacia abajo; la gravedad la empuja hacia abajo
        self.gravity = 0.9

        self.en_agua = False
        self.pez_enganchado = None
        self.tiempo_linea = 0

    def actualizar(self):
        # Si el anzuelo no ha llegado al agua, actualizar física tipo proyectil
        if not self.en_agua:
            self.x_pos += self.vx
            self.y_pos += self.vy
            self.vy += self.gravity

            # Distancia recorrida desde el inicio
            distancia_recorrida = math.hypot(self.x_pos - self.x_inicio, self.y_pos - self.y_inicio)

            # Si alcanza la distancia máxima forzamos que caiga al agua
            if distancia_recorrida >= self.distancia_max or self.y_pos >= 350:
                self.y_pos = min(self.y_pos, 350)
                self.en_agua = True

        # aumentar contador para ondulación cuando esté en agua o volando
        self.tiempo_linea += 1

    def dibujar(self, pantalla):
        # Dibujar la línea desde el inicio hasta la posición actual del anzuelo
        puntos = []
        segmentos = 22

        x_final = int(self.x_pos)
        y_final = int(self.y_pos)

        for i in range(segmentos + 1):
            t = i / segmentos
            x = self.x_inicio + (x_final - self.x_inicio) * t
            y = self.y_inicio + (y_final - self.y_inicio) * t

            # Ondulación pequeña, independiente de la distancia cuando está en el aire
            perpendicular_x = -(y_final - self.y_inicio) / (self.distancia_max + 1)
            perpendicular_y = (x_final - self.x_inicio) / (self.distancia_max + 1)
            ondulacion = math.sin(self.tiempo_linea * 0.12 + i * 0.35) * (2 if self.en_agua else 4 * (self.potencia/100))
            x += perpendicular_x * ondulacion
            y += perpendicular_y * ondulacion

            puntos.append((int(x), int(y)))

        # Dibujar segmento de la línea
        for i in range(len(puntos) - 1):
            grosor = max(1, int(3 * (1 - i / len(puntos))))
            color_linea = (200 - (i * 2), 200 - (i * 2), 100 + (i // 2))
            pygame.draw.line(pantalla, color_linea, puntos[i], puntos[i + 1], grosor)

        # Dibujar anzuelo en la posición actual
        pygame.draw.circle(pantalla, (200, 150, 50), (x_final, y_final), 6)
        pygame.draw.arc(pantalla, (100, 100, 100), (x_final - 7, y_final - 7, 14, 14), math.pi * 0.3, math.pi * 1.7, 2)
        pygame.draw.circle(pantalla, (255, 200, 100), (x_final, y_final), 6, 1)

class Bote:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.ancho = 140
        self.alto = 70
        self.angulo_cana = -math.pi / 4  # Ángulo inicial de la caña
        self.flexion_cana = 0
        self.tiempo_lanzamiento = 0
        self.animando_lanzamiento = False
    
    def dibujar_textura_madera(self, pantalla, x, y, ancho, alto):
        """Dibuja textura de madera con líneas verticales"""
        colores_madera = [(139, 69, 19), (160, 82, 45), (185, 110, 50), (150, 75, 20)]
        
        for i in range(0, ancho, 5):
            color = colores_madera[(x + i) % len(colores_madera)]
            pygame.draw.line(pantalla, color, (int(x + i), int(y)), 
                           (int(x + i), int(y + alto)), 2)
    
    def dibujar(self, pantalla):
        # Sombra del bote en el agua (más suave)
        sombra_surf = pygame.Surface((self.ancho + 30, 20), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra_surf, (0, 0, 0, 90), (0, 0, self.ancho + 30, 20))
        pantalla.blit(sombra_surf, (self.x - (self.ancho + 30) // 2 - 5, self.y + self.alto // 2 + 6))
        
        # Casco principal del bote (forma de bote real)
        casco_puntos = [
            (int(self.x - self.ancho // 2), int(self.y)),  # Esquina inferior izquierda
            (int(self.x - self.ancho // 2 + 10), int(self.y - self.alto // 3)),  # Lado izquierdo
            (int(self.x - self.ancho // 4), int(self.y - self.alto)),  # Arriba izquierda
            (int(self.x + self.ancho // 4), int(self.y - self.alto)),  # Arriba derecha
            (int(self.x + self.ancho // 2 - 10), int(self.y - self.alto // 3)),  # Lado derecho
            (int(self.x + self.ancho // 2), int(self.y)),  # Esquina inferior derecha
        ]
        
        # Dibujar casco relleno
        pygame.draw.polygon(pantalla, (160, 82, 45), casco_puntos)
        
        # Textura de madera en el casco
        self.dibujar_textura_madera(pantalla, self.x - self.ancho // 2, self.y - self.alto, 
                                     self.ancho, self.alto)
        
        # Borde del casco (3D)
        pygame.draw.polygon(pantalla, (120, 60, 30), casco_puntos, 3)
        
        # Interior del bote (más claro)
        interior_puntos = [
            (int(self.x - self.ancho // 2 + 15), int(self.y - 10)),
            (int(self.x - self.ancho // 4), int(self.y - self.alto + 10)),
            (int(self.x + self.ancho // 4), int(self.y - self.alto + 10)),
            (int(self.x + self.ancho // 2 - 15), int(self.y - 10)),
        ]
        pygame.draw.polygon(pantalla, (185, 110, 50), interior_puntos)
        
        # Banda de color naranja en el bote (decorativa) con brillo
        banda_rect = (int(self.x - self.ancho // 2 + 10), int(self.y - self.alto // 2 - 4), int(self.ancho - 20), 12)
        pygame.draw.rect(pantalla, (255, 140, 0), banda_rect, border_radius=6)
        pygame.draw.rect(pantalla, (255, 200, 80), (banda_rect[0]+2, banda_rect[1]+1, banda_rect[2]-4, banda_rect[3]-4), border_radius=5)
        
        # Tablillas del fondo del bote
        for i in range(3):
            y_tablilla = self.y - self.alto + 15 + i * 12
            pygame.draw.line(pantalla, (140, 70, 40), 
                           (int(self.x - self.ancho // 3), int(y_tablilla)),
                           (int(self.x + self.ancho // 3), int(y_tablilla)), 4)
        
        # Jugador sentado en el bote (mejorado - como la imagen)
        jugador_x = self.x - 20
        jugador_y = self.y - self.alto + 30

        # Piernas y botas
        pygame.draw.polygon(pantalla, (30, 60, 110), [(int(jugador_x - 8), int(jugador_y + 10)), (int(jugador_x - 2), int(jugador_y + 10)), (int(jugador_x - 4), int(jugador_y + 28)), (int(jugador_x - 10), int(jugador_y + 28))])
        pygame.draw.polygon(pantalla, (30, 60, 110), [(int(jugador_x + 2), int(jugador_y + 10)), (int(jugador_x + 8), int(jugador_y + 10)), (int(jugador_x + 10), int(jugador_y + 28)), (int(jugador_x + 4), int(jugador_y + 28))])
        pygame.draw.rect(pantalla, (80, 180, 100), (int(jugador_x - 10), int(jugador_y + 26), 10, 6), border_radius=2)
        pygame.draw.rect(pantalla, (80, 180, 100), (int(jugador_x + 2), int(jugador_y + 26), 10, 6), border_radius=2)

        # Torso con capucha
        hood_rect = (int(jugador_x - 14), int(jugador_y - 6), 28, 22)
        pygame.draw.ellipse(pantalla, (95, 145, 75), hood_rect)
        pygame.draw.rect(pantalla, (90, 140, 70), (int(jugador_x - 12), int(jugador_y+2), 24, 16), border_radius=4)
        pygame.draw.line(pantalla, (70, 110, 60), (int(jugador_x - 6), int(jugador_y+6)), (int(jugador_x + 6), int(jugador_y+6)), 2)

        # Brazo izquierdo relajado
        pygame.draw.line(pantalla, (255, 200, 160), (int(jugador_x - 8), int(jugador_y + 6)), (int(jugador_x - 20), int(jugador_y + 2)), 5)

        # Brazo derecho (sujetando caña)
        if self.animando_lanzamiento:
            progreso = self.tiempo_lanzamiento / 30
            brazo_angulo = -math.pi / 2.5 - (math.pi / 2.2) * progreso
        else:
            brazo_angulo = -math.pi / 2.5

        brazo_x = jugador_x + 8 + math.cos(brazo_angulo) * 18
        brazo_y = jugador_y + 2 + math.sin(brazo_angulo) * 18
        pygame.draw.line(pantalla, (255, 200, 160), (int(jugador_x + 8), int(jugador_y + 2)), (int(brazo_x), int(brazo_y)), 4)
        pygame.draw.circle(pantalla, (255, 200, 160), (int(brazo_x), int(brazo_y)), 3)

        # Cabeza, barba y gorro
        pygame.draw.circle(pantalla, (255, 205, 170), (int(jugador_x), int(jugador_y - 18)), 10)
        pygame.draw.ellipse(pantalla, (110, 60, 30), (int(jugador_x - 8), int(jugador_y - 8), 16, 12))
        pygame.draw.polygon(pantalla, (95, 50, 25), [(int(jugador_x - 8), int(jugador_y - 2)), (int(jugador_x + 8), int(jugador_y - 2)), (int(jugador_x + 4), int(jugador_y + 4)), (int(jugador_x - 4), int(jugador_y + 4))])
        pygame.draw.circle(pantalla, (50, 50, 50), (int(jugador_x - 3), int(jugador_y - 20)), 2)
        pygame.draw.circle(pantalla, (50, 50, 50), (int(jugador_x + 3), int(jugador_y - 20)), 2)
        pygame.draw.ellipse(pantalla, (245, 200, 80), (int(jugador_x - 14), int(jugador_y - 30), 28, 14))
        pygame.draw.polygon(pantalla, (245, 195, 70), [(int(jugador_x - 16), int(jugador_y - 24)), (int(jugador_x + 16), int(jugador_y - 24)), (int(jugador_x + 12), int(jugador_y - 18)), (int(jugador_x - 12), int(jugador_y - 18))])
        
        # Caña de pescar
        punto_agarre_x = brazo_x
        punto_agarre_y = brazo_y
        
        cana_largo = 95
        # Calcular punto final con flexión
        x_cana = punto_agarre_x + math.cos(self.angulo_cana) * cana_largo * (1 - self.flexion_cana * 0.3)
        y_cana = punto_agarre_y + math.sin(self.angulo_cana) * cana_largo * (1 - self.flexion_cana * 0.2)
        
        # Dibujar caña gradualmente más delgada
        for i in range(10):
            t = i / 10
            x_seg = punto_agarre_x + (x_cana - punto_agarre_x) * t
            y_seg = punto_agarre_y + (y_cana - punto_agarre_y) * t
            x_seg2 = punto_agarre_x + (x_cana - punto_agarre_x) * (t + 0.1)
            y_seg2 = punto_agarre_y + (y_cana - punto_agarre_y) * (t + 0.1)
            
            grosor = max(1, int(5 * (1 - t)))
            pygame.draw.line(pantalla, (120, 60, 30), (int(x_seg), int(y_seg)), 
                           (int(x_seg2), int(y_seg2)), grosor)
        
        # Brillo en la caña
        pygame.draw.line(pantalla, (200, 150, 100), (int(punto_agarre_x), int(punto_agarre_y)), 
                        (int(x_cana), int(y_cana)), 1)
        
        # Carrete (reel)
        pygame.draw.circle(pantalla, (60, 60, 60), (int(punto_agarre_x - 12), int(punto_agarre_y)), 10)
        pygame.draw.circle(pantalla, (100, 100, 100), (int(punto_agarre_x - 12), int(punto_agarre_y)), 10, 2)
        # Líneas del carrete
        for i in range(0, 360, 45):
            x_end = punto_agarre_x - 12 + 8 * math.cos(math.radians(i))
            y_end = punto_agarre_y + 8 * math.sin(math.radians(i))
            pygame.draw.line(pantalla, (80, 80, 80), (int(punto_agarre_x - 12), int(punto_agarre_y)),
                           (int(x_end), int(y_end)), 1)
    
    def iniciar_lanzamiento(self):
        """Inicia la animación de lanzamiento; potencia influye en la flexión."""
        self.animando_lanzamiento = True
        self.tiempo_lanzamiento = 0
        # la flexión inicial depende de la potencia (si se pasa en el atributo antes de llamar)
        try:
            potencia = getattr(self, 'potencia_lanzamiento', 50)
            self.flexion_cana = min(1.0, potencia / 100)
        except Exception:
            self.flexion_cana = 0.5
    
    def actualizar_lanzamiento(self):
        """Actualiza la animación de lanzamiento"""
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
        
        self.estado = EstadoJuego.ESPERANDO
        self.potencia = 0
        self.incremento_potencia = 1.5
        self.angulo_cana_reposo = -math.pi / 2.5  # Ángulo de reposo de la caña
        
        # posicionar el bote a la izquierda como en la referencia
        self.bote = Bote(140, SCREEN_HEIGHT - 120)
        self.bote.angulo_cana = self.angulo_cana_reposo  # Posición inicial
        # Referencia al juego para que el bote pueda saber si hay línea lanzada
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
        # Shop / upgrades
        self.shop_open = False
        self.tienda_rect = pygame.Rect(SCREEN_WIDTH - 90, 20, 70, 60)
        self.upgrades = {'distancia': 0, 'fuerza': 0, 'peso': 0}
        self.upgrade_costs = {'distancia': 25, 'fuerza': 30, 'peso': 15}
        self.base_distance = 400
    
    def generar_peces(self, cantidad):
        self.peces = []
        for _ in range(cantidad):
            x = random.randint(150, SCREEN_WIDTH - 150)
            y = random.randint(420, SCREEN_HEIGHT - 80)
            self.peces.append(Pez(x, y))
    
    def actualizar(self):
        # Actualizar animación de lanzamiento del bote
        self.bote.actualizar_lanzamiento()
        
        # Actualizar peces
        for pez in self.peces:
            if pez.vivo:
                pez.actualizar()
        
        # Actualizar línea si existe
        if self.linea:
            self.linea.actualizar()
        
        # Actualizar potencia si está cargando
        if self.estado == EstadoJuego.CARGANDO:
            self.potencia = min(100, self.potencia + self.incremento_potencia)
            self.bote.flexion_cana = self.potencia / 100
            
            # Invertir dirección al llegar a 100
            if self.potencia >= 100:
                self.incremento_potencia = -1.5
            elif self.potencia <= 0:
                self.incremento_potencia = 1.5
        
        # Actualizar línea si está lanzada
        if self.estado == EstadoJuego.LANZADO:
            self.linea.pez_enganchado = None
            
            # Verificar colisión con peces
            for pez in self.peces:
                if pez.vivo:
                    # usar posición dinámica del anzuelo (x_pos, y_pos)
                    distancia = math.hypot(pez.x - getattr(self.linea, 'x_pos', getattr(self.linea, 'x_final', 0)), 
                                         pez.y - getattr(self.linea, 'y_pos', getattr(self.linea, 'y_final', 0)))
                    extra_hook = 5 + self.upgrades.get('peso', 0) * 3
                    if distancia < pez.radio + extra_hook:
                        self.linea.pez_enganchado = pez
                        self.estado = EstadoJuego.PESCANDO
                        break
        
        # Retirar línea si se presiona click
        if self.estado == EstadoJuego.PESCANDO:
            if not self.mouse_presionado:
                pez = None
                if self.linea:
                    pez = self.linea.pez_enganchado
                if pez:
                    pez.vivo = False
                    self.pescados += 1
                    self.monedas += self.moneda_por_pez
                    self.mensaje = f"+{self.moneda_por_pez} monedas! Pescados: {self.pescados}"
                    self.tiempo_mensaje = 120

                    # Generar nuevo pez
                    self.peces.append(Pez(random.randint(150, SCREEN_WIDTH - 150),
                                         random.randint(420, SCREEN_HEIGHT - 80)))

                self.estado = EstadoJuego.ESPERANDO
                self.bote.flexion_cana = 0
                self.linea = None
        
        # Actualizar tiempo de mensaje
        if self.tiempo_mensaje > 0:
            self.tiempo_mensaje -= 1
    
    def dibujar(self):
        # Fondo - Cielo degradado
        for y in range(0, 350):
            color_cielo = (
                int(135 + (120 - 135) * (y / 350)),
                int(206 + (170 - 206) * (y / 350)),
                int(250 + (220 - 250) * (y / 350))
            )
            pygame.draw.line(self.pantalla, color_cielo, (0, y), (SCREEN_WIDTH, y))
        
        # Escala superior y temporizador
        self.dibujar_escala_timer()

        # UI de costos (burbujas izquierda)
        self.dibujar_ui_burbujas()

        # Sol grande en el horizonte (semi-sumergido)
        sol_x = SCREEN_WIDTH // 2 + 150
        sol_y = 350 + 60
        sol_radio = 180
        sol_surf = pygame.Surface((sol_radio*2, sol_radio*2), pygame.SRCALPHA)
        pygame.draw.circle(sol_surf, (250, 250, 70, 230), (sol_radio, sol_radio), sol_radio)
        # recortar la parte superior para simular sol detrás del horizonte
        self.pantalla.blit(sol_surf, (sol_x - sol_radio, sol_y - sol_radio + 20))

        # Boya cerca del sol (posicionada como en la referencia)
        try:
            self.dibujar_boya(sol_x - 80, sol_y)
        except Exception:
            pass

        # Icono de tienda (simple)
        # Icono de tienda (estilizado como en la referencia)
        tienda_w, tienda_h = 70, 60
        tienda_x = SCREEN_WIDTH - tienda_w - 20
        tienda_y = 20
        # Fondo azul con borde negro grueso
        pygame.draw.rect(self.pantalla, (30, 140, 240), (tienda_x, tienda_y, tienda_w, tienda_h), border_radius=8)
        pygame.draw.rect(self.pantalla, (0,0,0), (tienda_x, tienda_y, tienda_w, tienda_h), 4, border_radius=8)
        # Tejadillo rojo/white
        roof = [(tienda_x + 8, tienda_y + 14), (tienda_x + tienda_w//2, tienda_y - 8), (tienda_x + tienda_w - 8, tienda_y + 14)]
        pygame.draw.polygon(self.pantalla, (220,30,30), roof)
        # Rayas blancas en el tejado
        pygame.draw.line(self.pantalla, (255,255,255), (tienda_x + 14, tienda_y + 8), (tienda_x + tienda_w//2, tienda_y + 2), 3)
        pygame.draw.line(self.pantalla, (255,255,255), (tienda_x + tienda_w - 14, tienda_y + 8), (tienda_x + tienda_w//2, tienda_y + 2), 3)
        texto_shop = self.fuente_pequeña.render("shop", True, BLANCO)
        self.pantalla.blit(texto_shop, (tienda_x+12, tienda_y + tienda_h - 26))

        # Si la tienda está abierta, dibujar overlay con botones de compra
        if self.shop_open:
            shop_w, shop_h = 260, 240
            shop_x = SCREEN_WIDTH // 2 - shop_w // 2
            shop_y = SCREEN_HEIGHT // 2 - shop_h // 2
            pygame.draw.rect(self.pantalla, (30, 30, 40), (shop_x, shop_y, shop_w, shop_h), border_radius=8)
            pygame.draw.rect(self.pantalla, (200, 200, 200), (shop_x+4, shop_y+4, shop_w-8, shop_h-8), 2, border_radius=6)

            title = self.fuente.render("Tienda de mejoras", True, (240, 240, 240))
            self.pantalla.blit(title, (shop_x + 18, shop_y + 10))

            # Botones de compra
            btn_w, btn_h = 220, 40
            padding = 12
            bx = shop_x + 20
            by = shop_y + 50
            keys = list(self.upgrades.keys())
            for i, key in enumerate(keys):
                rect = pygame.Rect(bx, by + i * (btn_h + padding), btn_w, btn_h)
                pygame.draw.rect(self.pantalla, (50, 80, 120), rect, border_radius=6)
                cost = self.upgrade_costs.get(key, 0)
                lvl = self.upgrades.get(key, 0)
                texto = self.fuente_pequeña.render(f"{key.capitalize()} Lv{lvl} - {cost} monedas", True, BLANCO)
                self.pantalla.blit(texto, (rect.x + 12, rect.y + 8))

        self.dibujar_nubes()
        
        # Línea del horizonte (agua)
        pygame.draw.line(self.pantalla, (100, 150, 180), (0, 350), (SCREEN_WIDTH, 350), 2)
        
        # Fondo - Agua degradada
        for y in range(350, SCREEN_HEIGHT):
            intensidad = (y - 350) / (SCREEN_HEIGHT - 350)
            color_agua = (
                int(30 + intensidad * 20),
                int(144 - intensidad * 50),
                int(255 - intensidad * 80)
            )
            pygame.draw.line(self.pantalla, color_agua, (0, y), (SCREEN_WIDTH, y))
        
        # Animación del agua (ondas)
        self.dibujar_ondas()
        
        # Dibujar peces
        for pez in self.peces:
            pez.dibujar(self.pantalla)
        
        # Dibujar bote
        self.bote.dibujar(self.pantalla)
        
        # Dibujar línea si existe
        if self.linea:
            self.linea.dibujar(self.pantalla)
        else:
            # Si no hay línea lanzada, dibujar una línea vertical fina desde la punta de la caña al agua
            # (esto hace que la escena se parezca a la imagen con la línea colgando)
            try:
                # Intentar obtener la punta de la caña desde el bote
                punto_agarre_x = None
                punto_agarre_y = None
                # calculamos punto final de caña según bote
                punto_agarre_x = self.bote.x + 8 + math.cos(self.bote.angulo_cana) * 18
                punto_agarre_y = (self.bote.y - self.bote.alto + 30) + math.sin(self.bote.angulo_cana) * 18
                y_superficie = 350
                pygame.draw.line(self.pantalla, (170, 170, 180), (int(punto_agarre_x), int(punto_agarre_y)), (int(punto_agarre_x), y_superficie), 2)
                pygame.draw.circle(self.pantalla, (200,160,80), (int(punto_agarre_x), y_superficie), 3)
            except Exception:
                pass
        
        # Panel de interfaz (semi-transparente)
        panel_surf = pygame.Surface((SCREEN_WIDTH, 100))
        panel_surf.set_alpha(200)
        panel_surf.fill((20, 20, 40))
        self.pantalla.blit(panel_surf, (0, 0))
        
        # Barra de potencia mejorada
        barra_x = 20
        barra_y = 15
        barra_ancho = 250
        barra_alto = 25
        
        # Fondo de la barra
        pygame.draw.rect(self.pantalla, (50, 50, 80), (barra_x, barra_y, barra_ancho, barra_alto))
        pygame.draw.rect(self.pantalla, (150, 150, 200), (barra_x, barra_y, barra_ancho, barra_alto), 2)
        
        if self.estado == EstadoJuego.CARGANDO:
            relleno_ancho = (self.potencia / 100) * barra_ancho
            # Gradiente de color según potencia
            if self.potencia < 33:
                color_relleno = (0, 200, 100)  # Verde
            elif self.potencia < 66:
                color_relleno = (255, 200, 0)  # Amarillo
            else:
                color_relleno = (255, 0, 0)  # Rojo
            
            pygame.draw.rect(self.pantalla, color_relleno, (barra_x, barra_y, relleno_ancho, barra_alto))
            
            # Texto de potencia
            texto_potencia = self.fuente.render(f"{int(self.potencia)}%", True, BLANCO)
            self.pantalla.blit(texto_potencia, (barra_x + barra_ancho + 10, barra_y))
        else:
            texto_estado = self.fuente_pequeña.render("Haz CLICK y mantén para cargar potencia", True, BLANCO)
            self.pantalla.blit(texto_estado, (barra_x, barra_y + 5))
        
        # Estadísticas en la esquina superior derecha
        stats_x = SCREEN_WIDTH - 280
        stats_y = 15
        
        texto_pescados = self.fuente.render(f"🎣 Pescados: {self.pescados}", True, (255, 200, 0))
        texto_monedas = self.fuente.render(f"🪙 Monedas: {self.monedas}", True, (255, 200, 0))

        self.pantalla.blit(texto_pescados, (stats_x, stats_y))
        self.pantalla.blit(texto_monedas, (stats_x, stats_y + 35))
        
        # Dibujar mensaje de logro
        if self.tiempo_mensaje > 0:
            alpha = int(255 * (self.tiempo_mensaje / 120))
            texto_mensaje = self.fuente.render(self.mensaje, True, (100, 255, 100))
            self.pantalla.blit(texto_mensaje, (SCREEN_WIDTH // 2 - 150, 120))
        
        # Estado de pescando
        if self.estado == EstadoJuego.PESCANDO:
            texto_pescando = self.fuente_grande.render("¡PESCADO!", True, (255, 100, 0))
            self.pantalla.blit(texto_pescando, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 50))
            
            instruccion = self.fuente_pequeña.render("Haz CLICK para retirar", True, BLANCO)
            self.pantalla.blit(instruccion, (SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 + 20))
        
        pygame.display.flip()
    
    def dibujar_nubes(self):
        # Nubes decorativas estáticas
        nubes = [
            (150, 80, 40),
            (500, 100, 35),
            (800, 70, 45),
        ]
        
        for x, y, size in nubes:
            # Círculos que forman la nube
            pygame.draw.circle(self.pantalla, (255, 255, 255), (x, y), size)
            pygame.draw.circle(self.pantalla, (255, 255, 255), (x + size // 2, y - 10), size - 5)
            pygame.draw.circle(self.pantalla, (255, 255, 255), (x + size, y), size)

    def dibujar_ui_burbujas(self):
        # Burbujas de UI a la izquierda con costos
        x = 30
        y = 60
        w = 220
        h = 56
        shadow_off = 6

        # Distancia - azul (blob con sombra)
        pygame.draw.ellipse(self.pantalla, (20, 20, 60), (x - 6 + shadow_off, y - 6 + shadow_off, w + 12, h + 12))
        pygame.draw.ellipse(self.pantalla, (30, 170, 240), (x - 6, y - 6, w + 12, h + 12))
        pygame.draw.ellipse(self.pantalla, (10, 10, 30), (x - 6, y - 6, w + 12, h + 12), 2)
        t = self.fuente_pequeña.render("distancia = 25 monedas", True, (10,10,30))
        self.pantalla.blit(t, (x + 10, y + 12))

        # Fuerza - rojo
        y += 80
        pygame.draw.ellipse(self.pantalla, (20, 20, 60), (x - 6 + shadow_off, y - 6 + shadow_off, w + 12, h + 12))
        pygame.draw.ellipse(self.pantalla, (220, 40, 40), (x - 6, y - 6, w + 12, h + 12))
        pygame.draw.ellipse(self.pantalla, (255,255,255), (x - 6, y - 6, w + 12, h + 12), 2)
        t2 = self.fuente_pequeña.render("fuerza = 30 monedas", True, (255,255,255))
        self.pantalla.blit(t2, (x + 10, y + 12))

        # Peso - naranja
        y += 80
        pygame.draw.ellipse(self.pantalla, (20, 20, 60), (x - 6 + shadow_off, y - 6 + shadow_off, w + 12, h + 12))
        pygame.draw.ellipse(self.pantalla, (255, 140, 0), (x - 6, y - 6, w + 12, h + 12))
        pygame.draw.ellipse(self.pantalla, (10,10,30), (x - 6, y - 6, w + 12, h + 12), 2)
        t3 = self.fuente_pequeña.render("peso = 15 monedas", True, (10,10,30))
        self.pantalla.blit(t3, (x + 10, y + 12))

    def dibujar_escala_timer(self):
        # Barra superior gruesa estilo dibujo (negra) con marcas y un marcador amarillo
        y = 24
        left = 80
        right = SCREEN_WIDTH - 80
        pygame.draw.line(self.pantalla, (10,10,10), (left, y), (right, y), 10)

        # Marcas verticales negras (estilo hecho a mano)
        pasos = 6
        for i in range(pasos + 1):
            x = int(left + (right - left) * i / pasos)
            pygame.draw.line(self.pantalla, (10,10,10), (x, y - 28), (x, y + 28), 6)

        # Marcador amarillo dinámico que indica qué tan profundo/alejado se lanzará
        # Mientras cargas, se basa en la potencia; si ya lanzaste, refleja la distancia objetivo
        if self.estado == EstadoJuego.CARGANDO:
            frac = self.potencia / 100
        elif self.linea:
            # línea puede no haber llegado al agua aún, usamos distancia_max relativa a base
            frac = min(1.0, max(0.0, self.linea.distancia_max / max(1, self.base_distance)))
        else:
            frac = 0.05

        marker_x = int(left +  (right - left) * frac)
        pygame.draw.circle(self.pantalla, (250, 230, 80), (marker_x, y), 18)
        pygame.draw.circle(self.pantalla, (10,10,10), (marker_x, y), 18, 3)

    def dibujar_boya(self, cx, cy):
        # Boya colorida (estimación de la imagen) - bandas y rotación
        boya_surf = pygame.Surface((120, 80), pygame.SRCALPHA)
        # Dibujar bandas
        pygame.draw.ellipse(boya_surf, (200,20,20), (6, 6, 108, 68))
        pygame.draw.ellipse(boya_surf, (20,20,200), (18, 16, 84, 48))
        pygame.draw.ellipse(boya_surf, (60,200,80), (32, 24, 56, 32))
        # borde
        pygame.draw.ellipse(boya_surf, (10,10,10), (6,6,108,68), 3)
        rot = pygame.transform.rotate(boya_surf, -25)
        self.pantalla.blit(rot, (cx - rot.get_width()//2, cy - rot.get_height()//2))
    
    def dibujar_ondas(self):
        # Ondas en la superficie del agua con reflejos
        frame = int(pygame.time.get_ticks() / 50) % 100

        for i in range(4):
            fase = (frame + i * 30) / 100
            amplitud = 3 + i
            y = 350 + int(amplitud * math.sin(fase * math.pi * 2))
            color = (90 + i*10, 170 + i*10, 210 + i*5)
            pygame.draw.line(self.pantalla, color, (0, y), (SCREEN_WIDTH, y), 1)

        # Reflejos suaves del sol en el agua (si el sol está presente)
        try:
            sol_x = SCREEN_WIDTH // 2 + 150
            for r in range(3):
                alpha = max(20, 120 - r * 30)
                width = 380 - r * 80
                refl = pygame.Surface((width, 24), pygame.SRCALPHA)
                pygame.draw.ellipse(refl, (250, 250, 120, alpha), (0, 0, width, 20))
                self.pantalla.blit(refl, (sol_x - width//2 + r*6, 360 + r*6))
        except Exception:
            pass

        # Pequeños destellos móviles
        ticks = int(pygame.time.get_ticks() / 120)
        for i in range(0, SCREEN_WIDTH, 140):
            x = (i + ticks) % SCREEN_WIDTH
            y = 362 + int(math.sin((i + ticks) * 0.02) * 3)
            pygame.draw.aaline(self.pantalla, (200, 230, 255), (x, y), (x + 20, y))
    
    def manejar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return False
            
            if evento.type == pygame.MOUSEBUTTONDOWN:
                self.mouse_presionado = True
                mx, my = pygame.mouse.get_pos()

                # Priorizar interacción con la tienda
                if self.tienda_rect.collidepoint(mx, my):
                    self.shop_open = not self.shop_open
                    continue

                if self.shop_open:
                    # manejar clicks dentro de la UI de la tienda
                    shop_w, shop_h = 260, 240
                    shop_x = SCREEN_WIDTH // 2 - shop_w // 2
                    shop_y = SCREEN_HEIGHT // 2 - shop_h // 2
                    btn_w, btn_h = 220, 40
                    padding = 12
                    bx = shop_x + 20
                    by = shop_y + 50
                    keys = list(self.upgrades.keys())
                    for i, key in enumerate(keys):
                        rect = pygame.Rect(bx, by + i * (btn_h + padding), btn_w, btn_h)
                        if rect.collidepoint(mx, my):
                            cost = self.upgrade_costs.get(key, 0)
                            if self.monedas >= cost:
                                self.monedas -= cost
                                self.upgrades[key] += 1
                                # aplicar efecto inmediato
                                if key == 'distancia':
                                    self.base_distance += 100
                                if key == 'fuerza':
                                    self.moneda_por_pez += 5
                                # peso ya afecta el radio de anzuelo en actualizar
                                self.mensaje = f"Compraste {key}!"
                                self.tiempo_mensaje = 90
                            else:
                                self.mensaje = "Monedas insuficientes"
                                self.tiempo_mensaje = 90
                            self.shop_open = False
                            break
                    continue

                # Si no se interactuó con la tienda, proceder con el juego
                if self.estado == EstadoJuego.ESPERANDO:
                    self.estado = EstadoJuego.CARGANDO
                    self.potencia = 0
                    self.incremento_potencia = 1.5
                    
                    # Calcular ángulo hacia el cursor
                    dx = mx - self.bote.x
                    dy = my - (self.bote.y - 70)
                    self.angulo_lanzamiento = math.atan2(dy, dx)
                    self.bote.angulo_cana = self.angulo_lanzamiento
                
                # Si está en estado LANZADO y presiona de nuevo, devuelve la caña
                elif self.estado == EstadoJuego.LANZADO:
                    self.estado = EstadoJuego.ESPERANDO
                    self.linea = None
                    self.bote.angulo_cana = self.angulo_cana_reposo
                    self.bote.flexion_cana = 0
                    self.bote.animando_lanzamiento = False
            
            if evento.type == pygame.MOUSEBUTTONUP:
                self.mouse_presionado = False
                
                if self.estado == EstadoJuego.CARGANDO:
                    # Lanzar línea
                    # Ajustar distancia base según mejoras
                    distancia_base = self.base_distance + self.upgrades['distancia'] * 100
                    self.linea = Linea(self.bote.x, self.bote.y - 70, self.potencia, self.angulo_lanzamiento, distancia_base)
                    self.bote.iniciar_lanzamiento()
                    self.estado = EstadoJuego.LANZADO
            
            if evento.type == pygame.MOUSEMOTION and self.estado == EstadoJuego.CARGANDO:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                dx = mouse_x - self.bote.x
                dy = mouse_y - (self.bote.y - 70)
                self.angulo_lanzamiento = math.atan2(dy, dx)
                self.bote.angulo_cana = self.angulo_lanzamiento
        
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
