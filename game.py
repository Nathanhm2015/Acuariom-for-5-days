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
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-1, 1)
        self.radio = random.randint(8, 15)
        self.color = random.choice([(255, 100, 0), (0, 100, 255), (255, 215, 0)])
        self.vivo = True
    
    def actualizar(self):
        self.x += self.vx
        self.y += self.vy
        
        # Rebotar en bordes del agua
        if self.x - self.radio < 100 or self.x + self.radio > SCREEN_WIDTH - 100:
            self.vx *= -1
        if self.y - self.radio < 350 or self.y + self.radio > SCREEN_HEIGHT - 50:
            self.vy *= -1
        
        # Mantener en límites
        self.x = max(100 + self.radio, min(SCREEN_WIDTH - 100 - self.radio, self.x))
        self.y = max(350 + self.radio, min(SCREEN_HEIGHT - 50 - self.radio, self.y))
    
    def dibujar(self, pantalla):
        if self.vivo:
            pygame.draw.circle(pantalla, self.color, (int(self.x), int(self.y)), self.radio)
            # Ojo
            pygame.draw.circle(pantalla, BLANCO, (int(self.x) + self.radio - 3, int(self.y) - 2), 2)
            pygame.draw.circle(pantalla, NEGRO, (int(self.x) + self.radio - 3, int(self.y) - 2), 1)

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
    
    def dibujar(self, pantalla):
        # Dibujar línea
        pygame.draw.line(pantalla, MARRON, (self.x_inicio, self.y_inicio), 
                        (self.x_final, self.y_final), 2)
        
        # Dibujar anzuelo
        pygame.draw.circle(pantalla, AMARILLO, (int(self.x_final), int(self.y_final)), 4)
        pygame.draw.circle(pantalla, NEGRO, (int(self.x_final), int(self.y_final)), 4, 1)

class Bote:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.ancho = 100
        self.alto = 50
        self.angulo_cana = -math.pi / 4  # Ángulo inicial de la caña
        self.flexion_cana = 0
    
    def dibujar(self, pantalla):
        # Sombra del bote
        pygame.draw.ellipse(pantalla, (0, 0, 0, 50), (self.x - self.ancho // 2 - 5, self.y + self.alto // 2 + 5, 
                                                       self.ancho + 10, 10))
        
        # Casco del bote (gradiente simulado)
        pygame.draw.ellipse(pantalla, (200, 100, 50), (self.x - self.ancho // 2, self.y - self.alto // 2, 
                                                        self.ancho, self.alto))
        pygame.draw.ellipse(pantalla, (180, 80, 40), (self.x - self.ancho // 2, self.y - self.alto // 2 + 5, 
                                                       self.ancho, self.alto - 10))
        
        # Borde del bote (3D)
        pygame.draw.arc(pantalla, (150, 50, 30), (self.x - self.ancho // 2, self.y - self.alto // 2, 
                                                   self.ancho, self.alto), 0, math.pi, 3)
        
        # Detalles del bote
        pygame.draw.line(pantalla, (100, 50, 20), (self.x - self.ancho // 4, self.y - 5), 
                        (self.x - self.ancho // 4, self.y + 10), 2)
        pygame.draw.line(pantalla, (100, 50, 20), (self.x + self.ancho // 4, self.y - 5), 
                        (self.x + self.ancho // 4, self.y + 10), 2)
        
        # Jugador (cuerpo completo)
        # Torso
        pygame.draw.rect(pantalla, (255, 150, 100), (int(self.x - 8), int(self.y - 35), 16, 20), 
                        border_radius=3)
        # Cabeza
        pygame.draw.circle(pantalla, (255, 180, 140), (int(self.x), int(self.y - 42)), 7)
        # Brazos
        pygame.draw.line(pantalla, (255, 180, 140), (int(self.x - 8), int(self.y - 30)), 
                        (int(self.x - 15), int(self.y - 25)), 3)
        pygame.draw.line(pantalla, (255, 180, 140), (int(self.x + 8), int(self.y - 30)), 
                        (int(self.x + 15), int(self.y - 25)), 3)
        # Piernas
        pygame.draw.line(pantalla, (50, 50, 150), (int(self.x - 4), int(self.y - 15)), 
                        (int(self.x - 4), int(self.y)), 3)
        pygame.draw.line(pantalla, (50, 50, 150), (int(self.x + 4), int(self.y - 15)), 
                        (int(self.x + 4), int(self.y)), 3)
        
        # Caña de pescar con flexión
        cana_largo = 80
        # Punto de agarre
        punto_agarre_x = self.x + 10
        punto_agarre_y = self.y - 25
        
        # Calcular punto final con flexión
        x_cana = punto_agarre_x + math.cos(self.angulo_cana) * cana_largo * (1 - self.flexion_cana * 0.3)
        y_cana = punto_agarre_y + math.sin(self.angulo_cana) * cana_largo * (1 - self.flexion_cana * 0.2)
        
        # Dibujar caña con grosor que disminuye
        pygame.draw.line(pantalla, (139, 69, 19), (int(punto_agarre_x), int(punto_agarre_y)), 
                        (int(x_cana), int(y_cana)), 6)
        # Brillo en la caña
        pygame.draw.line(pantalla, (200, 150, 100), (int(punto_agarre_x), int(punto_agarre_y)), 
                        (int(x_cana), int(y_cana)), 2)
        
        # Carrete (reel)
        pygame.draw.circle(pantalla, (50, 50, 50), (int(punto_agarre_x - 5), int(punto_agarre_y)), 8)
        pygame.draw.circle(pantalla, (100, 100, 100), (int(punto_agarre_x - 5), int(punto_agarre_y)), 8, 2)

class Juego:
    def __init__(self):
        self.pantalla = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Acuariom - Juego de Pesca")
        self.reloj = pygame.time.Clock()
        self.fuente = pygame.font.Font(None, 36)
        self.fuente_pequeña = pygame.font.Font(None, 24)
        
        self.estado = EstadoJuego.ESPERANDO
        self.potencia = 0
        self.incremento_potencia = 1.5
        
        self.bote = Bote(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)
        self.linea = None
        self.peces = []
        self.generar_peces(8)
        
        self.pescados = 0
        self.puntos = 0
        self.mensaje = ""
        self.tiempo_mensaje = 0
        
        self.mouse_presionado = False
        self.angulo_lanzamiento = -math.pi / 4
    
    def generar_peces(self, cantidad):
        self.peces = []
        for _ in range(cantidad):
            x = random.randint(150, SCREEN_WIDTH - 150)
            y = random.randint(400, SCREEN_HEIGHT - 100)
            self.peces.append(Pez(x, y))
    
    def actualizar(self):
        # Actualizar peces
        for pez in self.peces:
            if pez.vivo:
                pez.actualizar()
        
        # Actualizar potencia si está cargando
        if self.estado == EstadoJuego.CARGANDO:
            self.potencia = min(100, self.potencia + self.incremento_potencia)
            
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
                                         random.randint(400, SCREEN_HEIGHT - 100)))
                
                self.estado = EstadoJuego.ESPERANDO
                self.linea = None
        
        # Actualizar tiempo de mensaje
        if self.tiempo_mensaje > 0:
            self.tiempo_mensaje -= 1
    
    def dibujar(self):
        # Fondo - Cielo
        self.pantalla.fill(CIELO, (0, 0, SCREEN_WIDTH, 350))
        
        # Fondo - Agua
        pygame.draw.rect(self.pantalla, AGUA_OSCURO, (0, 350, SCREEN_WIDTH, SCREEN_HEIGHT - 350))
        
        # Dibujar peces
        for pez in self.peces:
            pez.dibujar(self.pantalla)
        
        # Dibujar bote
        self.bote.dibujar(self.pantalla)
        
        # Dibujar línea si existe
        if self.linea:
            self.linea.dibujar(self.pantalla)
        
        # Dibujar barra de potencia
        barra_y = 20
        barra_ancho = 200
        barra_alto = 20
        
        pygame.draw.rect(self.pantalla, GRIS, (20, barra_y, barra_ancho, barra_alto))
        
        if self.estado == EstadoJuego.CARGANDO:
            relleno_ancho = (self.potencia / 100) * barra_ancho
            color_relleno = (255 - (self.potencia * 2.55), self.potencia * 2.55, 0)
            pygame.draw.rect(self.pantalla, color_relleno, (20, barra_y, relleno_ancho, barra_alto))
        
        pygame.draw.rect(self.pantalla, BLANCO, (20, barra_y, barra_ancho, barra_alto), 2)
        
        # Dibujar texto de estado
        if self.estado == EstadoJuego.ESPERANDO:
            texto_estado = self.fuente_pequeña.render("CLICK para lanzar", True, NEGRO)
            self.pantalla.blit(texto_estado, (20, barra_y + 30))
        elif self.estado == EstadoJuego.CARGANDO:
            texto_potencia = self.fuente.render(f"Potencia: {int(self.potencia)}%", True, BLANCO)
            self.pantalla.blit(texto_potencia, (20, barra_y + 30))
        elif self.estado == EstadoJuego.PESCANDO:
            texto_pescando = self.fuente.render("¡PESCADO! CLICK para retirar", True, VERDE)
            self.pantalla.blit(texto_pescando, (SCREEN_WIDTH // 2 - 200, 50))
        
        # Dibujar estadísticas
        texto_pescados = self.fuente.render(f"Pescados: {self.pescados}", True, BLANCO)
        texto_puntos = self.fuente.render(f"Puntos: {self.puntos}", True, BLANCO)
        self.pantalla.blit(texto_pescados, (SCREEN_WIDTH - 300, 20))
        self.pantalla.blit(texto_puntos, (SCREEN_WIDTH - 300, 60))
        
        # Dibujar mensaje
        if self.tiempo_mensaje > 0:
            texto_mensaje = self.fuente_pequeña.render(self.mensaje, True, VERDE)
            self.pantalla.blit(texto_mensaje, (SCREEN_WIDTH // 2 - 100, 100))
        
        pygame.display.flip()
    
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
