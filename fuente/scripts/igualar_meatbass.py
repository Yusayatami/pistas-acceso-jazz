"""Iguala el timbre y el volumen de las muestras de pizzicato de Meatbass.

Algunas muestras del banco (sobre todo La2 y Do2) suenan mucho más apagadas y fuertes que sus vecinas,
así que las notas que salen de ellas destacan. Este script renderiza todas las notas del registro del
walking, ajusta la tendencia natural de brillo y nivel con la altura y corrige cada muestra hacia esa
tendencia (75 % de la desviación) con ecualización y volumen por grupo:
   eq1: realce de medios (700 Hz, zona de armónicos)   eq2: recorte de graves (110 Hz)
   eq3: corte a 3,5 kHz para que el ataque del dedo (clic) no suba respecto a la muestra original
   volume
Parte del programa afinado (afinar_meatbass.py) y escribe:
   Programs/pizz_basic_map_igualado.sfz y Programs/04_pizz_igualado.sfz
Uso: python3 igualar_meatbass.py RUTA_MEATBASS RUTA_SFIZZ_RENDER"""
import os, re, subprocess, sys, tempfile
import numpy as np
import mido

MB, RENDER = sys.argv[1], sys.argv[2]
PROG = os.path.join(MB, "Programs")
SRC = open(os.path.join(PROG, "pizz_basic_map_afinado.sfz")).read()
KEYS = list(range(28, 54))                     # registro del walking (Mi1..Fa3) con margen
AMOUNT = 0.75                                  # parte de la desviación que se corrige
TMP = tempfile.mkdtemp()

# --- grupos del mapa: rango de teclas, capa de velocidad y muestra raíz ---
groups = []
for blk in re.split(r"(?=<group>)", SRC):
    if not blk.startswith("<group>"): continue
    g = dict(re.findall(r"^(lokey|hikey|lovel|hivel)=(\d+)", blk, re.M))
    m = re.search(r"sample=.*?([a-g]b?\d)_vl\d", blk)
    groups.append({"lo": int(g.get("lokey", 0)), "hi": int(g.get("hikey", 127)),
                   "lovel": int(g.get("lovel", 0)), "hivel": int(g.get("hivel", 127)),
                   "root": m.group(1) if m else None})
VEL = 88                                        # pulsación típica de la línea (capa mf)
key_root = {}
for g in groups:
    if g["root"] and g["lovel"] <= VEL <= g["hivel"]:
        for k in range(g["lo"], g["hi"] + 1): key_root[k] = g["root"]
roots = sorted({key_root[k] for k in KEYS if k in key_root}, key=lambda r: min(k for k in KEYS if key_root.get(k) == r))

def write_program(corr, tag):
    out = []
    for blk in re.split(r"(?=<group>)", SRC):
        m = re.search(r"sample=.*?([a-g]b?\d)_vl\d", blk)
        if blk.startswith("<group>") and m and m.group(1) in corr:
            c = corr[m.group(1)]
            extra = (f"eq1_freq=700 eq1_bw=1.5 eq1_gain={c['eq1']:.1f}\n"
                     f"eq2_freq=110 eq2_bw=1.6 eq2_gain={c['eq2']:.1f}\n"
                     f"eq3_freq=3500 eq3_bw=2 eq3_gain={c['eq3']:.1f}\nvolume={c['vol']:.1f}\n")
            blk = blk.replace("<group>\n", "<group>\n" + extra, 1)
        out.append(blk)
    mp = os.path.join(PROG, f"pizz_basic_map_{tag}.sfz")
    open(mp, "w").write("".join(out))
    p = open(os.path.join(PROG, "04_pizz_afinado.sfz")).read().replace(
        "pizz_basic_map_afinado.sfz", f"pizz_basic_map_{tag}.sfz")
    open(os.path.join(PROG, f"04_pizz_{tag}.sfz"), "w").write(p)
    return os.path.join(PROG, f"04_pizz_{tag}.sfz")

def measure(program):
    mid = mido.MidiFile(ticks_per_beat=480); tr = mido.MidiTrack(); mid.tracks.append(tr)
    tr.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(120)))
    for cc, v in ((104, 4), (107, 0)): tr.append(mido.Message("control_change", control=cc, value=v))
    for rep in range(4):                                       # 4 vueltas: promedia las tomas (rr)
        for k in KEYS:
            tr.append(mido.Message("note_on", note=k, velocity=VEL, time=0 if (rep == 0 and k == KEYS[0]) else 120))
            tr.append(mido.Message("note_off", note=k, velocity=0, time=360))
    mf, wf = os.path.join(TMP, "s.mid"), os.path.join(TMP, "s.wav")
    mid.save(mf)
    subprocess.run([RENDER, "--sfz", program, "--midi", mf, "--wav", wf, "-s", "44100"],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    x = np.frombuffer(subprocess.run(["ffmpeg", "-loglevel", "error", "-i", wf, "-ac", "1", "-f", "f32le", "-"],
                                     capture_output=True).stdout, np.float32)
    sr, step = 44100, 0.5
    lv, br, ck = {k: [] for k in KEYS}, {k: [] for k in KEYS}, {k: [] for k in KEYS}
    def band(sig, lo, hi):
        sp = np.abs(np.fft.rfft(sig * np.hanning(len(sig)), 8192)) ** 2; fr = np.fft.rfftfreq(8192, 1 / sr)
        return sp[(fr > lo) & (fr < hi)].sum() / len(sig)
    for rep in range(4):
        for i, k in enumerate(KEYS):
            a = int(((rep * len(KEYS) + i) * step + 0.005) * sr); seg = x[a:a + int(0.12 * sr)]
            sp = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))) ** 2; fr = np.fft.rfftfreq(len(seg), 1 / sr)
            lv[k].append(20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9))
            br[k].append(10 * np.log10(sp[(fr > 400) & (fr < 2500)].sum() / sp[(fr > 30) & (fr < 400)].sum()))
            a0 = int(((rep * len(KEYS) + i) * step) * sr)        # clic: 2-6 kHz en los primeros 25 ms
            ck[k].append(10 * np.log10(band(x[a0:a0 + int(0.025 * sr)], 2000, 6000) /
                                       band(x[a0 + int(0.05 * sr):a0 + int(0.20 * sr)], 30, 1000)))
    return ({k: np.mean(lv[k]) for k in KEYS}, {k: np.mean(br[k]) for k in KEYS},
            {k: np.mean(ck[k]) for k in KEYS})

def deviations(vals):
    """Desviación de cada muestra respecto a la tendencia lineal (ajuste robusto)."""
    ks = np.array(KEYS, float); v = np.array([vals[k] for k in KEYS])
    use = np.ones(len(ks), bool)
    for _ in range(3):
        a, b = np.polyfit(ks[use], v[use], 1)
        res = v - (a * ks + b)
        use = np.abs(res) < max(3.0, 1.5 * np.std(res[use]))
    return {r: float(np.median([res[i] for i, k in enumerate(KEYS) if key_root.get(k) == r])) for r in roots}, res

lv0, br0, ck0 = measure(os.path.join(PROG, "04_pizz_afinado.sfz"))
dev_b, res_b0 = deviations(br0)
corr = {r: {"eq1": 0.0, "eq2": 0.0, "eq3": 0.0, "vol": 0.0} for r in roots}
per_root = lambda d, r: float(np.median([d[k] for k in KEYS if key_root.get(k) == r]))
need = {r: -AMOUNT * dev_b[r] for r in roots}                  # dB de brillo que hay que ganar (o perder)
for it in range(2):                                            # dos pasadas para afinar la respuesta del eq
    for r in roots:
        A = need[r] if it == 0 else need[r] * corr[r]["scale"]
        corr[r]["eq1"] = float(np.clip(A * 0.7, -6, 9))
        corr[r]["eq2"] = float(np.clip(-A * 0.8, -9, 0)) if A > 0 else 0.0
        corr[r]["A"] = A
    lv1, br1, ck1 = measure(write_program(corr, "igualado"))
    for r in roots:
        got = np.median([br1[k] - br0[k] for k in KEYS if key_root.get(k) == r])
        corr[r]["scale"] = (corr[r]["A"] / got) if abs(got) > 0.5 and abs(need[r]) > 1 else 1.0
# clic: que el ataque no suba respecto a la muestra original (dos pasadas)
for it in range(2):
    for r in roots:
        rise = per_root(ck1, r) - per_root(ck0, r)
        corr[r]["eq3"] = float(np.clip(corr[r]["eq3"] - max(0.0, rise) * 1.3, -12, 0))
    lv1, br1, ck1 = measure(write_program(corr, "igualado"))
# volumen: después del eq, cada muestra hacia la tendencia de nivel
dev_l, _ = deviations(lv1)
for r in roots:
    corr[r]["vol"] = float(np.clip(-AMOUNT * dev_l[r], -8, 8))
lv2, br2, ck2 = measure(write_program(corr, "igualado"))
_, res_b2 = deviations(br2); _, res_l0 = deviations(lv0); _, res_l2 = deviations(lv2)
for r in roots:
    print(f"  {r:4s} brillo {dev_b[r]:+6.1f} dB -> medios {corr[r]['eq1']:+5.1f}, graves {corr[r]['eq2']:+5.1f}, "
          f"3,5 kHz {corr[r]['eq3']:+5.1f}, volumen {corr[r]['vol']:+5.1f} · clic {per_root(ck2, r) - per_root(ck0, r):+4.1f} dB")
print(f"Meatbass igualado: dispersión de brillo {np.std(res_b0):.1f} -> {np.std(res_b2):.1f} dB · "
      f"de nivel {np.std(res_l0):.1f} -> {np.std(res_l2):.1f} dB -> Programs/04_pizz_igualado.sfz")
