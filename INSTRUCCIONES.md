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

🎮 VISIÓN GENERAL DEL JUEGO

Es un juego de pesca 2D, estilo casual / arcade, con gráficos planos (flat design), colores vivos y mecánicas simples pero adictivas.

La cámara es 2D lateral:

Arriba: cielo + superficie del agua

Abajo: mundo submarino en capas

🌊 ESTILO DEL FONDO MARINO

No es realista, es caricaturesco y minimalista.

Superficie

Cielo amarillo brillante

Sol grande y difuminado

Montañas triangulares simples

Árboles verdes con formas básicas

Todo con colores pastel y suaves

Sin texturas realistas, todo es vectorial

Bajo el agua

El color cambia según la profundidad:

Verde claro cerca de la superficie

Verde/azulado más oscuro al bajar

Rocas grandes a los lados con huecos

Plantas marinas simples (formas negras o verde oscuro)

Pequeñas burbujas circulares flotando

👉 El fondo no distrae, solo ambienta.

💧 COLOR DEL AGUA

Superficie: verde turquesa brillante

Profundidad media: verde agua

Profundo: verde oscuro con toques azulados

No hay transparencia realista, es un color sólido con degradado

🐟 LOS PECES
Estilo

Caricaturescos

Formas simples

Ojos grandes y expresivos

Algunos sonríen 😄

Sin detalles realistas (escamas mínimas)

Tamaños

Peces pequeños (comunes)

Peces medianos

Peces grandes (más valor / más peso)

Movimiento

Nadan de lado a lado

Velocidad constante

Algunos en grupos

🎣 LA CAÑA DE PESCAR

Estilo simple y limpio

Línea negra delgada

Anzuelo pequeño con:

Bolita naranja

Detalle azul

La línea se inclina según el movimiento

El anzuelo:

Baja

Se mueve horizontalmente

Rebota en paredes según mejoras

✨ EFECTOS ESPECIALES

Muy sutiles, nada exagerado:

Burbujas circulares

Brillos al atrapar peces

Chispas doradas al ganar monedas

Barra de “Jackpot” que se llena

Animaciones suaves (ease in / ease out)

🧠 INTERFAZ DE USUARIO (UI)
Medidor de profundidad

Texto grande: 125 ft, 153 ft, etc.

Barra vertical u horizontal marcando profundidad

Muy clara y legible

Lanzamiento

Medidor en forma de arco

Colores:

Rojo (malo)

Amarillo (medio)

Verde (perfecto)

Texto tipo: “Great!”

Tienda / mejoras

Panel a la izquierda:

Strength

Weight

Rebound

Resistance

Cada mejora:

Ícono

Descripción corta

Botón “Upgrade x3” (con video)

🧍 PERSONAJE

Pescador caricaturesco

Barba grande

Gorra

Sentado en un bote pequeño

Caja con peces detrás

No se mueve mucho, solo animación ligera

💰 RECOMPENSAS

Pantalla final con:

Monedas

Peces atrapados

Barra de progreso tipo jackpot

Botones:

Collect

Collect x3 (ver anuncio)

🎨 ESTILO ARTÍSTICO RESUMIDO

2D

Flat design

Colores vivos

Sin realismo

Bordes suaves

Ideal para móviles

🛠️ SI QUIERES RECREARLO

Puedo ayudarte a:

Diseñar el escenario en Blender

Crear los peces y el anzuelo

Programar la lógica de pesca

Hacer el medidor de lanzamiento

Montar un prototipo jugable
