# Wings & Fish

Juego arcade 2D en Pygame: pilota un pelícano y un águila pescadora, bucea para atrapar peces y enfréntate a jefes submarinos.

## Requisitos

- Python 3.10 o posterior
- Pygame
- Pillow es opcional; se usa para reproducir todos los cuadros de los GIF animados

Instala las dependencias con:

```bash
python3 -m pip install pygame pillow
```

## Ejecutar

```bash
python3 game.py
```

Pulsa **MODOS** y sigue el tutorial. El modo libre conserva las oleadas; el modo niveles ofrece una campaña de 20 niveles, cinco encuentros por nivel y jefes en los niveles 10 y 20. El avance de campaña se guarda en tu carpeta personal.

## Controles

- `WASD` o flechas: mover el ave
- `Espacio` o clic izquierdo: bucear
- `1` / `2`: seleccionar pelícano / ave pescadora
- `Z` / `X`: buceo directo del pelícano / ave pescadora
- `Q`: ráfaga del pelícano
- Clic derecho: picotazo del ave pescadora
- `E`: taladro del ave pescadora
- `Esc`: volver o cerrar una pantalla

Atrapa camarones para cargar la ráfaga del pelícano o recuperar stamina con el ave pescadora. Las monedas permiten comprar mejoras y skins.

## Pruebas

```bash
python3 -m unittest discover -s tests -v
```