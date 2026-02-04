# Acuariom - Juego de Pesca

Un juego interactivo de pesca desarrollado en Python con Pygame.

## Mecánicas del Juego

- **Bote Estático**: Estás dentro de un bote que no se mueve
- **Caña de Pescar**: Lanza tu caña hacia donde apuntes con el cursor
- **Sistema de Potencia**: Presiona el botón del mouse y mantén presionado para cargar la potencia (0-100%). A mayor potencia, más lejos se lanza la línea
- **Pesca**: Cuando la línea toque a un pez, se enganchará. Suelta el botón del mouse para retirar y pescar el pez
- **Sistema de Puntos**: Cada pez pescado suma 10 puntos

## Controles

- **Mouse Click**: Presionar y mantener para cargar potencia
- **Mover Mouse**: Cambiar ángulo de lanzamiento
- **Soltar Click**: Lanzar la caña de pescar

## Instalación

### Requisitos
- Python 3.7+
- Pygame

### Instalar Pygame

```bash
pip install pygame
```

## Cómo Ejecutar

```bash
python game.py
```

## Gameplay

1. Hace click en cualquier parte de la pantalla para comenzar a cargar
2. Mueve el mouse para ajustar el ángulo de la caña
3. Mantén presionado para cargar la potencia (verás la barra cambiar de color)
4. Suelta para lanzar la línea
5. Cuando la línea toque un pez, se enganchará (verás el mensaje "¡PESCADO!")
6. Hace click para retirar la caña y pescar el pez

## Características

- Peces con IA que nadan aleatoriamente
- Barra de potencia dinámica con cambio de color
- Sistema de puntuación y contador de pescados
- Interfaz gráfica intuitiva
- Física realista de lanzamiento basada en potencia

Autor: Acuariom Team
