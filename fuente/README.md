# Fuente de las pistas de acompañamiento

Todo lo necesario para regenerar las pistas, la web y los QR del manual de preparación de la prueba de acceso a Grado Superior de Jazz (piano). La web publicada (carpetas `a1`…`a6`, lecturas, temas, `audio` y `qr`) se genera a partir de aquí: no se edita a mano.

## Contenido

- `configuraciones/parrillas/`: las 12 pistas de las parrillas A1–A6 del cuaderno de anexos (A3 y A5 también con V alterado). Tempos: blanca 50 y 70, con escobillas.
- `configuraciones/lecturas/`: las 17 lecturas a primera vista, con su cifrado tal como está en el manual y las repeticiones desplegadas. La pista toca la forma tres veces (melodía, chorus de improvisación, melodía), al tempo escrito y 20 puntos más lenta. Los tempos están en `lecturas.json`.
- `configuraciones/temas/`: los 12 temas (2 libres y 10 obligados), a tempo de trabajo y de examen (`temas.json`). Los temas suenan 4 vueltas y los blues de 12 compases 8. La clave `estilo` puede ser `swing`, `bossa` (*Blue Bossa*), `vals` (*All Blues*, con `"compas": 3`) o `balada` (*In a Sentimental Mood*). La clave `final` fija el acorde del golpe final cuando el tema no empieza en el I (*Autumn Leaves*).
- `scripts/`: los scripts de la skill «pistas-acompanamiento-jazz» (`setup.sh`, `pista.py`, `mezcla.py`, `render.sh`…), además de:
  - `generar_web.py`: monta la web y los QR a partir de una carpeta con todos los MP3.
  - `estampar_qr_cuaderno.py` y `estampar_qr_manual.py`: ponen los QR en los PDF del cuaderno de anexos y del manual, sin rehacerlos. Usan las fuentes DM Sans (`DMSans-Regular.ttf` y `DMSans-Bold.ttf` en `/home/claude/`).
- `ejemplos/curva_referencia.json`: el sonido global aprobado por Ramón (ecualización, compresión y apertura estéreo).

## Cambiar una pista

1. `bash scripts/setup.sh` (la primera vez en cada sesión: bancos de muestras y renderizador).
2. Edita la configuración y genera de nuevo: `bash scripts/render.sh CONFIG.json TEMPO PREFIJO SALIDA.mp3`.
3. Usa **exactamente el mismo nombre de archivo** que tiene en `audio/`: así los QR impresos siguen funcionando.
4. Regenera la web con `python3 scripts/generar_web.py CARPETA_SALIDA CARPETA_CON_TODOS_LOS_MP3` y sube los cambios.

Nombres de archivo:
- `Pista_<parrilla>_blanca<50|70>_escobillas.mp3`
- `Pista_Lectura_<U?_S?>_negra<tempo>.mp3`
- `Pista_Tema_<Tema>_negra<tempo>_<trabajo|examen>.mp3`
