#!/bin/bash
# Prepara el entorno: herramientas, bancos de muestras libres (CC0) y el renderizador sfizz.
# Uso: bash setup.sh   (idempotente; LIBS=/ruta para cambiar dónde se instalan los bancos)
set -e
LIBS=${LIBS:-$HOME/pistas_libs}
mkdir -p "$LIBS"
command -v ffmpeg >/dev/null || (apt-get update -q && apt-get install -y -q ffmpeg)
command -v cmake >/dev/null && command -v g++ >/dev/null || apt-get install -y -q cmake g++
command -v lilypond >/dev/null || apt-get install -y -q lilypond >/dev/null    # partitura de la línea de bajo
python3 -c "import mido, numpy" 2>/dev/null || pip install -q --break-system-packages mido numpy
clone() { [ -d "$LIBS/$2/.git" ] || git clone -q --depth 1 "https://github.com/$1" "$LIBS/$2"; }
clone sfzinstruments/karoryfer.meatbass meatbass             # contrabajo (Otto Rubner 1958), ~530 MB
clone sfzinstruments/virtuosity_drums virtuosity_drums       # batería de jazz con baquetas, ~760 MB
clone sfzinstruments/karoryfer.swirly-drums swirly           # batería con escobillas, ~2,6 GB
if [ ! -x "$LIBS/sfizz/build/library/bin/sfizz_render" ]; then
  [ -d "$LIBS/sfizz/.git" ] || git clone -q --depth 1 --recursive --shallow-submodules \
      https://github.com/sfztools/sfizz "$LIBS/sfizz"
  mkdir -p "$LIBS/sfizz/build" && cd "$LIBS/sfizz/build"
  cmake .. -DCMAKE_BUILD_TYPE=Release -DSFIZZ_JACK=OFF -DSFIZZ_RENDER=ON -DSFIZZ_SHARED=OFF >/dev/null
  make -j"$(nproc)" sfizz_render >/dev/null
fi
DIR=$(cd "$(dirname "$0")" && pwd)
[ -f "$LIBS/meatbass/Programs/04_pizz_afinado.sfz" ] || python3 "$DIR/afinar_meatbass.py" "$LIBS/meatbass"
[ -f "$LIBS/meatbass/Programs/04_pizz_igualado.sfz" ] || \
  python3 "$DIR/igualar_meatbass.py" "$LIBS/meatbass" "$LIBS/sfizz/build/library/bin/sfizz_render"
echo "Listo. Bancos y sfizz_render en $LIBS"
