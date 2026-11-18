"""Mezcla de una pista de acompañamiento (sin reverb) y exportación a MP3.

python3 mezcla.py PREFIJO SALIDA.mp3 [--bajo-sobre-bateria 9] [--caja-sobre-charles -4]
                  [--barrido-sobre-charles -10] [--escobillas-sobre-baquetas -3] [--curva curva.json]

Con --curva (de curva_referencia.py) se acerca el sonido global a una grabación de referencia:
  - apertura estéreo de la batería hasta la correlación de agudos de la referencia
  - ecualización del total con la curva
  - compresión de bus suave hasta el factor de cresta de la referencia

Partes que usa (las que existan):
  PREFIJO_bajo.wav
  PREFIJO_escobillas_{caja,charles,resto}.wav + PREFIJO_stir.wav
  PREFIJO_baquetas_{caja,charles,resto}.wav

Equilibrios por defecto (sonoridad integrada, LUFS) — los que Ramón aprobó:
  - escobillas: golpes de caja 4 LU por debajo del charles; barrido (stir) 10 LU por debajo
  - escobillas 3 LU por debajo de las baquetas, si hay de las dos
  - contrabajo 9 LU por encima de la batería de referencia (la más fuerte)
  - contrabajo: paso alto 38 Hz, -3 dB en 250 Hz, +2 dB en 900 Hz, compresión suave (ataque 5 ms); sin reverb
"""
import argparse, json, os, re, subprocess
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("prefijo"); ap.add_argument("salida")
ap.add_argument("--bajo-sobre-bateria", type=float, default=9.0)
ap.add_argument("--caja-sobre-charles", type=float, default=-4.0)
ap.add_argument("--barrido-sobre-charles", type=float, default=-10.0)
ap.add_argument("--escobillas-sobre-baquetas", type=float, default=-3.0)
ap.add_argument("--curva", default=None)
A = ap.parse_args()
P, OUT = A.prefijo, A.salida
TMP_D, TMP_B = f"{P}__d.wav", f"{P}__b.wav"

def ff(*a): subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *a], check=True)
def lufs(f):
    r = subprocess.run(["ffmpeg", "-i", f, "-af", "ebur128", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1])
def mix(files_gains, out):
    ins, fc = [], ""
    for i, (f, g) in enumerate(files_gains):
        ins += ["-i", f]; fc += f"[{i}]volume={g:.2f}dB[p{i}];"
    fc += "".join(f"[p{i}]" for i in range(len(files_gains))) + \
          f"amix=inputs={len(files_gains)}:normalize=0"
    ff(*ins, "-filter_complex", fc, out)
ex = os.path.exists

info = {}
has_brush = ex(f"{P}_escobillas_caja.wav")
if has_brush:
    k = lambda p: f"{P}_escobillas_{p}.wav"
    hh = lufs(k("charles"))
    g_taps = min(0.0, (hh + A.caja_sobre_charles) - lufs(k("caja")))
    g_stir = (hh + A.barrido_sobre_charles) - lufs(f"{P}_stir.wav")
    mix([(k("caja"), g_taps), (f"{P}_stir.wav", g_stir), (k("charles"), 0), (k("resto"), 0)],
        f"{P}_escobillas.wav")
    brush = lufs(f"{P}_escobillas.wav")
    info["golpes caja"] = round(g_taps, 1); info["barrido"] = round(g_stir, 1)
has_sticks = ex(f"{P}_baquetas_caja.wav") or ex(f"{P}_baquetas_resto.wav")
if has_sticks:
    k = lambda p: f"{P}_baquetas_{p}.wav"
    mix([(k(p), 0) for p in ("caja", "charles", "resto") if ex(k(p))], f"{P}_baquetas.wav")
    sticks = lufs(f"{P}_baquetas.wav")

drums = []
if has_sticks:
    ref = sticks
    drums.append((f"{P}_baquetas.wav", 0.0))
    if has_brush:
        drums.append((f"{P}_escobillas.wav", (sticks + A.escobillas_sobre_baquetas) - brush))
        info["escobillas"] = round(drums[-1][1], 1)
else:
    ref = brush
    drums.append((f"{P}_escobillas.wav", 0.0))
mix(drums, TMP_D)
ff("-i", f"{P}_bajo.wav", "-af",
   "highpass=f=38,equalizer=f=250:t=q:w=1.2:g=-3,equalizer=f=900:t=q:w=1:g=2,"
   "acompressor=threshold=-36dB:ratio=4:attack=5:release=120:makeup=4,alimiter=limit=0.7",
   "-ac", "2", TMP_B)
g_bass = (ref + A.bajo_sobre_bateria) - lufs(TMP_B)
info["bajo"] = round(g_bass, 1)
CURVA = json.load(open(A.curva)) if A.curva else None   # --curva "" desactiva el sonido de referencia

def load(f, ss=0, t=30):
    x = np.frombuffer(subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", str(ss), "-t", str(t), "-i", f,
                                      "-ac", "2", "-ar", "44100", "-f", "f32le", "-"], capture_output=True).stdout, np.float32)
    return x.reshape(-1, 2)
def hi_corr(x):
    out = []
    for ch in (0, 1):
        S = np.fft.rfft(x[:, ch]); fr = np.fft.rfftfreq(len(x), 1 / 44100); S[(fr < 2000) | (fr > 8000)] = 0
        out.append(np.fft.irfft(S, len(x)))
    return float(np.corrcoef(out[0], out[1])[0, 1])

WIDE = 1.0
if CURVA:                                  # apertura estéreo de la batería (el contrabajo sigue centrado)
    target = CURVA["correlacion_agudos_referencia"]; best = (9, 1.0)
    for w in (1.0, 1.5, 2.0, 2.5, 3.0, 4.0):           # medida sobre la mezcla con el contrabajo
        ff("-i", TMP_B, "-i", TMP_D, "-t", "30", "-filter_complex",
           f"[0]volume={g_bass:.2f}dB[b];[1]stereotools=mlev=1:slev={w}[d];[b][d]amix=inputs=2:normalize=0",
           f"{P}__w.wav")
        c = hi_corr(load(f"{P}__w.wav")); best = min(best, (abs(c - target), w))
    WIDE = best[1]; os.remove(f"{P}__w.wav")
    info["apertura batería"] = WIDE



base = (f"[0]volume={g_bass:.2f}dB,pan=stereo|c0=0.55*c0|c1=0.45*c1[b];"
        f"[1]highpass=f=30,equalizer=f=8000:t=q:w=1:g=-2,stereotools=mlev=1:slev={WIDE}[d];"
        "[b][d]amix=inputs=2:normalize=0")
master = ""
if CURVA:                                  # ecualización del total y compresión de bus hasta la cresta de la referencia
    eq = ";".join(f"entry({f},{g})" for f, g in zip(CURVA["frecuencias"], CURVA["ganancias_db"]))
    master = f",firequalizer=gain_entry='{eq}'"
    TMP_M = f"{P}__m.wav"
    ff("-i", TMP_B, "-i", TMP_D, "-filter_complex", base + master, TMP_M)
    def crest(f):
        x = load(f, 0, 600).mean(1); return 20 * np.log10(np.abs(x).max() / np.sqrt(np.mean(x ** 2)))
    goal, comp = CURVA["cresta_referencia_db"], ""
    for thr in (-14, -18, -22, -26, -30, -34, -38):
        ff("-i", TMP_M, "-af", f"acompressor=threshold={thr}dB:ratio=2.5:attack=20:release=200:makeup=1", f"{P}__c.wav")
        cr = crest(f"{P}__c.wav")
        comp = f",acompressor=threshold={thr}dB:ratio=2.5:attack=20:release=200:makeup=1"
        if cr <= goal + 0.3: break
    master += comp; info["cresta"] = round(cr, 1)
    for f in (TMP_M, f"{P}__c.wav"):
        if ex(f): os.remove(f)
TMP_F = f"{P}__f.wav"                     # normalización lineal a -16 LUFS + limitador (no altera la dinámica)
ff("-i", TMP_B, "-i", TMP_D, "-filter_complex", base + master, TMP_F)
g_out = -16.0 - lufs(TMP_F)
ff("-i", TMP_F, "-af", f"volume={g_out:.2f}dB,alimiter=limit=0.84:level=0,"
   "silenceremove=stop_periods=-1:stop_duration=1.5:stop_threshold=-60dB",
   "-codec:a", "libmp3lame", "-b:a", "192k", OUT)
os.remove(TMP_F)
for f in (TMP_D, TMP_B):
    if ex(f): os.remove(f)
print(OUT, info)
