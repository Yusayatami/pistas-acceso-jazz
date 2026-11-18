"""Calcula la curva de ecualización que acerca nuestras pistas al sonido de una grabación de referencia.

Uso: python3 curva_referencia.py REFERENCIA.wav PISTA_ACTUAL.mp3 curva.json [CANTIDAD]
  - Compara el espectro medio a largo plazo (tercios de octava, normalizado a 1 kHz) de las dos.
  - Guarda la diferencia suavizada y limitada a ±12 dB, multiplicada por CANTIDAD (por defecto 1.0).
  - Mide también el factor de cresta y la correlación estéreo de los agudos de la referencia,
    que mezcla.py usa como objetivo de compresión y de apertura de la batería.
La curva se aplica en mezcla.py con --curva curva.json."""
import json, subprocess, sys
import numpy as np

REF, OURS, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
AMOUNT = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
SR = 44100
CENTERS = [31.5, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600,
           2000, 2500, 3150, 4000, 5000, 6300, 8000, 10000, 12500, 16000]

def load(f):
    x = np.frombuffer(subprocess.run(["ffmpeg", "-loglevel", "error", "-i", f, "-ac", "2", "-ar", str(SR),
                                      "-f", "f32le", "-"], capture_output=True).stdout, np.float32)
    return x.reshape(-1, 2)

def ltas(x):
    m = x.mean(1); N = 1 << 15; win = np.hanning(N); acc = np.zeros(N // 2 + 1); n = 0
    for i in range(0, len(m) - N, N // 2):
        acc += np.abs(np.fft.rfft(m[i:i + N] * win)) ** 2; n += 1
    fr = np.fft.rfftfreq(N, 1 / SR); acc /= max(n, 1)
    v = np.array([10 * np.log10(acc[(fr >= c / 2 ** (1 / 6)) & (fr < c * 2 ** (1 / 6))].mean() + 1e-20) for c in CENTERS])
    return v - v[CENTERS.index(1000)]

def crest(x):
    m = x.mean(1); return float(20 * np.log10(np.abs(m).max() / np.sqrt(np.mean(m ** 2))))

def hi_corr(x):                                          # correlación L/R entre 2 y 8 kHz (apertura estéreo)
    seg = x[:SR * 30]; out = []
    for ch in (0, 1):
        S = np.fft.rfft(seg[:, ch]); fr = np.fft.rfftfreq(len(seg), 1 / SR); S[(fr < 2000) | (fr > 8000)] = 0
        out.append(np.fft.irfft(S, len(seg)))
    return float(np.corrcoef(out[0], out[1])[0, 1])

R, O = load(REF), load(OURS)
d = ltas(R) - ltas(O)
d = np.convolve(np.pad(d, 1, mode="edge"), [0.25, 0.5, 0.25], mode="valid")     # suavizado
gains = np.clip(d * AMOUNT, -12, 12)
json.dump({"referencia": REF, "frecuencias": CENTERS, "ganancias_db": [round(float(g), 1) for g in gains],
           "cresta_referencia_db": round(crest(R), 1), "correlacion_agudos_referencia": round(hi_corr(R), 2)},
          open(OUT, "w"), indent=1)
print("Curva:", " ".join(f"{c:g}:{g:+.1f}" for c, g in zip(CENTERS, gains)))
print(f"Cresta referencia {crest(R):.1f} dB (nuestra {crest(O):.1f}) · correlación agudos referencia "
      f"{hi_corr(R):.2f} (nuestra {hi_corr(O):.2f}) -> {OUT}")
