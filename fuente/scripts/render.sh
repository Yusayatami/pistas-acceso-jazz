#!/bin/bash
# Genera una pista completa: MIDI -> render de cada parte con su banco -> mezcla -> MP3.
# Uso: bash render.sh CONFIG.json TEMPO PREFIJO SALIDA.mp3 [opciones de mezcla.py]
set -e
DIR=$(cd "$(dirname "$0")" && pwd)
LIBS=${LIBS:-$HOME/pistas_libs}
R=$LIBS/sfizz/build/library/bin/sfizz_render
BAJO=$LIBS/meatbass/Programs/04_pizz_igualado.sfz
ESC=$LIBS/swirly/Programs/Basic_kit.sfz
BAQ=$LIBS/virtuosity_drums/Programs/02-full-kit.sfz
CFG=$1; TEMPO=$2; P=$3; OUT=$4; shift 4
notes() { python3 -c "import mido;print(sum(1 for m in mido.MidiFile('$1').tracks[0] if m.type=='note_on'))"; }
rend() { if [ "$(notes "$2")" -gt 0 ]; then "$R" --sfz "$1" --midi "$2" --wav "${2%.mid}.wav" -s 44100 -q 3 -p 256 >/dev/null 2>&1; fi; }
rm -f "${P}"_*.wav "${P}"_*.mid
python3 "$DIR/pista.py" "$CFG" "$TEMPO" "$P"
rend "$BAJO" "${P}_bajo.mid"
rend "$ESC" "${P}_stir.mid"
for p in caja charles resto; do rend "$ESC" "${P}_escobillas_$p.mid"; rend "$BAQ" "${P}_baquetas_$p.mid"; done
CURVA=${CURVA:-$DIR/../ejemplos/curva_referencia.json}       # sonido global aprobado por Ramón
if [ -f "$CURVA" ]; then python3 "$DIR/mezcla.py" "$P" "$OUT" --curva "$CURVA" "$@"
else python3 "$DIR/mezcla.py" "$P" "$OUT" "$@"; fi
python3 "$DIR/verificar.py" "$P" "$OUT"
