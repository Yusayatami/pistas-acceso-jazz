"""Mide la afinación de cada muestra de pizzicato de Meatbass y crea un programa corregido:
   Programs/pizz_basic_map_afinado.sfz y Programs/04_pizz_afinado.sfz
Uso: python3 afinar_meatbass.py RUTA_MEATBASS"""
import glob, os, re, subprocess, sys
import numpy as np

MB = sys.argv[1]
NAMES = {"c": 0, "db": 1, "d": 2, "eb": 3, "e": 4, "f": 5, "gb": 6, "g": 7, "ab": 8, "a": 9, "bb": 10, "b": 11}

def cents(path):
    m = re.match(r"([a-g]b?)(\d)_", os.path.basename(path))
    if not m:
        return None                                   # ruidos percusivos: sin altura
    midi = 12 * (int(m.group(2)) + 1) + NAMES[m.group(1)]
    fn = 440 * 2 ** ((midi - 69) / 12)
    x = np.frombuffer(subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-ac", "1", "-f", "f32le", "-"],
                                     capture_output=True).stdout, np.float32)
    sr = 44100; i = int(np.argmax(np.abs(x)))
    seg = x[i + int(0.05 * sr): i + int(0.65 * sr)]
    seg = seg * np.hanning(len(seg)); N = 1 << 19
    sp = np.abs(np.fft.rfft(seg, N)); fr = np.fft.rfftfreq(N, 1 / sr)
    est = []
    for h in (1, 2, 3, 4):
        mm = (fr > fn * h * 0.94) & (fr < fn * h * 1.06)
        if sp[mm].max() > sp.max() * 0.05:
            est.append(fr[mm][np.argmax(sp[mm])] / h)
    return 1200 * np.log2(np.median(est) / fn) if est else 0.0

prog = os.path.join(MB, "Programs")
src = open(os.path.join(prog, "pizz_basic_map.sfz")).read()
out, n = [], 0
for line in src.splitlines():
    out.append(line)
    m = re.match(r"\s*sample=(.+\.wav)\s*$", line)
    if m and "pizz" in m.group(1):
        wav = os.path.join(prog, m.group(1).replace("\\", "/"))
        c = cents(wav)
        if c is not None:
            out.append(f"tune={-round(c)}"); n += 1
open(os.path.join(prog, "pizz_basic_map_afinado.sfz"), "w").write("\n".join(out) + "\n")
p = open(os.path.join(prog, "04_pizz.sfz")).read().replace(
    '#include "pizz_basic_map.sfz"', '#include "pizz_basic_map_afinado.sfz"')
open(os.path.join(prog, "04_pizz_afinado.sfz"), "w").write(p)
print(f"Meatbass afinado: {n} muestras corregidas -> Programs/04_pizz_afinado.sfz")
