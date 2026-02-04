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
    def __init__(self, x_inicio, y_inicio, potencia, angulo):
        self.x_inicio = x_inicio
        self.y_inicio = y_inicio
        self.potencia = potencia  # 0 a 100
        self.angulo = angulo
        
        # Calcular distancia máxima basada en potencia
        self.distancia_max = (potencia / 100) * 400
        
        # Posición actual del anzuelo
        self.x_final = x_inicio + math.cos(angulo) * self.distancia_max
        self.y_final = y_inicio + math.sin(angulo) * self.distancia_max
        
        self.en_agua = self.y_final > 350
        self.pez_enganchado = None
        self.tiempo_linea = 0
    
    def actualizar(self):
        self.tiempo_linea += 1
    
    def dibujar(self, pantalla):
        # Línea de pesca con efecto de ondulación
        puntos = []
        segmentos = 20
        
        for i in range(segmentos + 1):
            t = i / segmentos
            x = self.x_inicio + (self.x_final - self.x_inicio) * t
            y = self.y_inicio + (self.y_final - self.y_inicio) * t
            
            # Agregamos ondulación a la línea
            perpendicular_x = -(self.y_final - self.y_inicio) / (self.distancia_max + 1)
            perpendicular_y = (self.x_final - self.x_inicio) / (self.distancia_max + 1)
            
            ondulacion = math.sin(self.tiempo_linea * 0.1 + i * 0.3) * 2
            x += perpendicular_x * ondulacion
            y += perpendicular_y * ondulacion
            
            puntos.append((int(x), int(y)))
        
        # Dibujar línea con gradiente de espesor
        for i in range(len(puntos) - 1):
            grosor = max(1, int(3 * (1 - i / len(puntos))))
            color_linea = (200 - (i * 2), 200 - (i * 2), 100 + (i // 2))
            pygame.draw.line(pantalla, color_linea, puntos[i], puntos[i + 1], grosor)
        
        # Dibujar anzuelo
        # Cuerpo del anzuelo
        pygame.draw.circle(pantalla, (200, 150, 50), (int(self.x_final), int(self.y_final)), 5)
        # Gancho
        pygame.draw.arc(pantalla, (100, 100, 100), (int(self.x_final - 6), int(self.y_final - 6), 12, 12), 
                       math.pi * 0.3, math.pi * 1.7, 2)
        # Brillo
        pygame.draw.circle(pantalla, (255, 200, 100), (int(self.x_final), int(self.y_final)), 5, 1)

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
        # Sombra del bote en el agua
        pygame.draw.ellipse(pantalla, (0, 0, 0, 80), (self.x - self.ancho // 2 - 10, self.y + self.alto // 2 + 8, 
                                                       self.ancho + 20, 15))
        
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
        
        # Banda de color naranja en el bote (decorativa)
        pygame.draw.line(pantalla, (255, 140, 0), (int(self.x - self.ancho // 2 + 10), int(self.y - self.alto // 2)),
                        (int(self.x + self.ancho // 2 - 10), int(self.y - self.alto // 2)), 8)
        
        # Tablillas del fondo del bote
        for i in range(3):
            y_tablilla = self.y - self.alto + 15 + i * 12
            pygame.draw.line(pantalla, (140, 70, 40), 
                           (int(self.x - self.ancho // 3), int(y_tablilla)),
                           (int(self.x + self.ancho // 3), int(y_tablilla)), 4)
        
        # Jugador sentado en el bote
        jugador_x = self.x - 10
        jugador_y = self.y - self.alto + 25
        
        # Piernas (sentado)
        pygame.draw.line(pantalla, (40, 40, 100), (int(jugador_x - 3), int(jugador_y + 10)), 
                        (int(jugador_x - 5), int(jugador_y + 25)), 4)
        pygame.draw.line(pantalla, (40, 40, 100), (int(jugador_x + 3), int(jugador_y + 10)), 
                        (int(jugador_x + 5), int(jugador_y + 25)), 4)
        
        # Torso (ropa verde)
        pygame.draw.polygon(pantalla, (100, 150, 80), [
            (int(jugador_x - 10), int(jugador_y)),
            (int(jugador_x + 10), int(jugador_y)),
            (int(jugador_x + 8), int(jugador_y + 15)),
            (int(jugador_x - 8), int(jugador_y + 15))
        ])
        
        # Brazos - Brazo izquierdo (hacia atrás, relajado)
        pygame.draw.line(pantalla, (255, 180, 140), (int(jugador_x - 10), int(jugador_y + 2)), 
                        (int(jugador_x - 20), int(jugador_y - 2)), 4)
        
        # Brazo derecho (sujetando caña, animado)
        if self.animando_lanzamiento:
            # Animación de lanzamiento
            progreso = self.tiempo_lanzamiento / 30
            brazo_angulo = -math.pi / 3 - (math.pi / 2) * progreso
        else:
            brazo_angulo = -math.pi / 3
        
        brazo_x = jugador_x + 8 + math.cos(brazo_angulo) * 15
        brazo_y = jugador_y + 2 + math.sin(brazo_angulo) * 15
        pygame.draw.line(pantalla, (255, 180, 140), (int(jugador_x + 8), int(jugador_y + 2)), 
                        (int(brazo_x), int(brazo_y)), 4)
        
        # Mano derecha (círculo pequeño)
        pygame.draw.circle(pantalla, (255, 200, 160), (int(brazo_x), int(brazo_y)), 3)
        
        # Cabeza
        pygame.draw.circle(pantalla, (255, 200, 160), (int(jugador_x), int(jugador_y - 15)), 10)
        
        # Barba marrón oscuro
        pygame.draw.polygon(pantalla, (100, 50, 30), [
            (int(jugador_x - 6), int(jugador_y - 7)),
            (int(jugador_x + 6), int(jugador_y - 7)),
            (int(jugador_x + 5), int(jugador_y - 1)),
            (int(jugador_x - 5), int(jugador_y - 1))
        ])
        
        # Líneas de barba
        pygame.draw.line(pantalla, (80, 40, 20), (int(jugador_x - 4), int(jugador_y - 3)),
                        (int(jugador_x - 3), int(jugador_y + 2)), 1)
        pygame.draw.line(pantalla, (80, 40, 20), (int(jugador_x), int(jugador_y - 3)),
                        (int(jugador_x), int(jugador_y + 2)), 1)
        pygame.draw.line(pantalla, (80, 40, 20), (int(jugador_x + 4), int(jugador_y - 3)),
                        (int(jugador_x + 3), int(jugador_y + 2)), 1)
        
        # Ojos
        pygame.draw.circle(pantalla, (50, 50, 50), (int(jugador_x - 3), int(jugador_y - 18)), 2)
        pygame.draw.circle(pantalla, (50, 50, 50), (int(jugador_x + 3), int(jugador_y - 18)), 2)
        
        # Gorro/Sombrero naranja
        gorro_puntos = [
            (int(jugador_x - 12), int(jugador_y - 26)),
            (int(jugador_x + 12), int(jugador_y - 26)),
            (int(jugador_x + 10), int(jugador_y - 20)),
            (int(jugador_x - 10), int(jugador_y - 20))
        ]
        pygame.draw.polygon(pantalla, (255, 140, 0), gorro_puntos)
        
        # Visera del gorro
        pygame.draw.polygon(pantalla, (255, 150, 20), [
            (int(jugador_x - 10), int(jugador_y - 20)),
            (int(jugador_x + 10), int(jugador_y - 20)),
            (int(jugador_x + 12), int(jugador_y - 18)),
            (int(jugador_x - 12), int(jugador_y - 18))
        ])
        
        # Caña de pescar
        punto_agarre_x = brazo_x
        punto_agarre_y = brazo_y
        
        cana_largo = 90
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
        """Inicia la animación de lanzamiento"""
        self.animando_lanzamiento = True
        self.tiempo_lanzamiento = 0
    
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
        
        self.bote = Bote(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 120)
        self.bote.angulo_cana = self.angulo_cana_reposo  # Posición inicial
        self.linea = None
        self.peces = []
        self.generar_peces(10)
        
        self.pescados = 0
        self.puntos = 0
        self.mensaje = ""
        self.tiempo_mensaje = 0
        
        self.mouse_presionado = False
        self.angulo_lanzamiento = self.angulo_cana_reposo
    
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
                    distancia = math.hypot(pez.x - self.linea.x_final, 
                                         pez.y - self.linea.y_final)
                    if distancia < pez.radio + 5:
                        self.linea.pez_enganchado = pez
                        self.estado = EstadoJuego.PESCANDO
                        break
        
        # Retirar línea si se presiona click
        if self.estado == EstadoJuego.PESCANDO:
            if not self.mouse_presionado:
                pez = self.linea.pez_enganchado
                if pez:
                    pez.vivo = False
                    self.pescados += 1
                    self.puntos += 10
                    self.mensaje = f"+10 puntos! Pescados: {self.pescados}"
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
        
        # Nubes (decorativas)
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
        texto_puntos = self.fuente.render(f"⭐ Puntos: {self.puntos}", True, (255, 200, 0))
        
        self.pantalla.blit(texto_pescados, (stats_x, stats_y))
        self.pantalla.blit(texto_puntos, (stats_x, stats_y + 35))
        
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
    
    def dibujar_ondas(self):
        # Ondas en la superficie del agua
        frame = int(pygame.time.get_ticks() / 50) % 100
        
        for i in range(3):
            fase = (frame + i * 30) / 100
            amplitud = 3 * (1 - abs(fase - 0.5) * 2)
            
            y = 350 + int(amplitud * math.sin(fase * math.pi * 2))
            pygame.draw.line(self.pantalla, (100, 180, 220), (0, y), (SCREEN_WIDTH, y), 1)
    
    def manejar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                return False
            
            if evento.type == pygame.MOUSEBUTTONDOWN:
                self.mouse_presionado = True
                mouse_x, mouse_y = pygame.mouse.get_pos()
                
                if self.estado == EstadoJuego.ESPERANDO:
                    self.estado = EstadoJuego.CARGANDO
                    self.potencia = 0
                    self.incremento_potencia = 1.5
                    
                    # Calcular ángulo hacia el cursor
                    dx = mouse_x - self.bote.x
                    dy = mouse_y - (self.bote.y - 15)
                    self.angulo_lanzamiento = math.atan2(dy, dx)
                    self.bote.angulo_cana = self.angulo_lanzamiento
            
            if evento.type == pygame.MOUSEBUTTONUP:
                self.mouse_presionado = False
                
                if self.estado == EstadoJuego.CARGANDO:
                    # Lanzar línea
                    self.linea = Linea(self.bote.x, self.bote.y - 15, self.potencia, 
                                      self.angulo_lanzamiento)
                    self.bote.iniciar_lanzamiento()
                    self.estado = EstadoJuego.LANZADO
            
            if evento.type == pygame.MOUSEMOTION and self.estado == EstadoJuego.CARGANDO:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                dx = mouse_x - self.bote.x
                dy = mouse_y - (self.bote.y - 15)
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
