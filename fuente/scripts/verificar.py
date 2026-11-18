"""Comprueba una pista: que el contrabajo da las notas previstas, su afinación y la duración.
Uso: python3 verificar.py PREFIJO SALIDA.mp3"""
import json, subprocess, sys
import numpy as np

P, OUT = sys.argv[1], sys.argv[2]
E = json.load(open(f"{P}_esperado.json"))
spb = 60 / E["tempo"]; sr = 44100
x = np.frombuffer(subprocess.run(["ffmpeg", "-loglevel", "error", "-i", f"{P}_bajo.wav", "-ac", "1",
                                  "-f", "f32le", "-"], capture_output=True).stdout, np.float32)
notes = [(t, n) for t, n in E["bajo"] if float(t).is_integer()]
step = max(1, len(notes) // 60)                       # hasta ~60 notas repartidas por la pista
ok = tot = 0; fallos = []; desv = []
for t, n in notes[::step]:
    a = int(((E["count_in_beats"] + t) * spb + 0.05) * sr); L = int(min(0.5, 0.8 * spb) * sr)
    seg = x[a:a + L]
    if len(seg) < L: continue
    seg = seg * np.hanning(L); N = 1 << 19
    sp = np.abs(np.fft.rfft(seg, N)); fr = np.fft.rfftfreq(N, 1 / sr)
    score = []                                        # clase de altura dominante (suma de armónicos)
    for pc in range(12):
        f0 = 440 * 2 ** ((pc + 36 - 69) / 12); s = 0
        for h in range(1, 6):
            for o in (0.5, 1, 2):
                fq = f0 * o * h
                if fq < 1500:
                    m = (fr > fq * 0.97) & (fr < fq * 1.03); s += sp[m].max()
        score.append(s)
    tot += 1
    if int(np.argmax(score)) != n % 12:
        fallos.append(t); continue
    ok += 1
    fn = 440 * 2 ** ((n - 69) / 12); est = []         # afinación fina con los armónicos 1-4
    for h in (1, 2, 3, 4):
        m = (fr > fn * h * 0.97) & (fr < fn * h * 1.03)
        if sp[m].max() > sp.max() * 0.05: est.append(fr[m][np.argmax(sp[m])] / h)
    if est: desv.append(1200 * np.log2(np.median(est) / fn))
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", OUT],
                           capture_output=True, text=True).stdout)
musica = (E["count_in_beats"] + E["bajo"][-1][0] + 1) * spb
print(f"Verificación {OUT}: notas del contrabajo {ok}/{tot} correctas"
      + (f" (revisar tiempos {fallos[:8]})" if fallos else "")
      + (f" · afinación: desviación típica {np.median(np.abs(desv)):.0f} cents, máxima {np.max(np.abs(desv)):.0f}" if desv else "")
      + f" · duración {dur:.1f} s (música {musica:.1f} s + final)")
