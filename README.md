# Wings & Fish

Juego arcade de pesca con dos aves: el pelícano y el ave pescadora. Vuela sobre el mar, esquiva peces globo, atrapa peces y mejora tus aves.

## Ejecutar

Requiere Python 3 y Pygame. Desde la carpeta del proyecto:

```bash
python3 -m pip install pygame
python3 game.py
```

Pillow es opcional; se usa para reproducir todos los cuadros de los GIF. Sin Pillow, el juego intenta mostrar el primer cuadro.

## Modos

- **Libre:** pesca en oleadas sin una ruta de campaña; los jefes aparecen en las oleadas 10 y 25.
- **Niveles:** completa cinco oleadas para terminar un nivel y desbloquear el siguiente. Los jefes aparecen en los niveles de decena. El progreso se guarda en `~/.wings_and_fish_progress.json`.

Al iniciar una partida puedes ver el tutorial, elegir el modo y abrir el mapa de niveles. El nivel, las monedas, las mejoras y las skins se guardan en `~/.wings_and_fish_progress.json`.

## Controles

- `WASD` o flechas: mover el ave activa.
- `Espacio` o clic izquierdo: zambullirse.
- `1` / `2`: elegir pelícano / ave pescadora.
- `Q`: ráfaga del pelícano.
- `E`: taladro del ave pescadora.
- Clic derecho: disparar con el pelícano o hacer el picotazo con el ave pescadora.

Los camarones aparecen al atrapar cangrejos con el pelícano, flotan a la superficie y se pueden recoger con ambas aves. Cargan la ráfaga del pelícano o curan al ave pescadora. También puedes comprar una carga extra en la tienda. Cada ave tiene nueve skins desbloqueables con monedas.

## Pruebas

```bash
python3 -m unittest discover -s tests
```
