"""Genera las partes MIDI de una pista de acompañamiento (contrabajo + batería, swing).

Uso:  python3 pista.py CONFIG.json TEMPO PREFIJO [SEMILLA]

CONFIG.json (ver ejemplos en la skill):
  {
    "titulo": "A3 · II-V-I mayor corto",
    "tipo": "ejercicio" | "tema",          # ejercicio: acaba en el último acorde; tema: en el primero
    "parrilla": "A3",                       # A1..A6 (anexo del manual)  — o bien —
    "compases": [["Cmaj7"], ["Cm7", "F7"], ...],   # cifrado: 1, 2, 3 (2+1+1) o 4 acordes por compás
    "calidad": "maj7",                      # solo A1/A2: maj7 | 7 | m7 | m6 | 7b9 | m7b5
    "compases_por_acorde": 1,               # solo A1/A2
    "v_alterado": false,                    # A3/A5: tocar el V como 7alt
    "i_menor": "m6",                        # A5/A6: calidad del I menor
    "coros": 1,
    "bateria": ["escobillas"],              # una por coro (se repite cíclicamente): escobillas | baquetas
    "fills": []                             # compases (0 = primero del coro) con pequeño fill
  }

Escribe:
  PREFIJO_bajo.mid
  PREFIJO_stir.mid                         (barrido de escobillas)
  PREFIJO_escobillas_{caja,charles,resto}.mid
  PREFIJO_baquetas_{caja,charles,resto}.mid
  PREFIJO_esperado.json                    (notas del bajo en cada tiempo, para verificar)
Contrabajo: Meatbass (altura real). Batería: Swirly Drums (escobillas) y Virtuosity Drums (baquetas).
"""
import json, random, re, sys
import mido

CFG = json.load(open(sys.argv[1]))
TEMPO, OUT = int(sys.argv[2]), sys.argv[3]
random.seed(int(sys.argv[4]) if len(sys.argv) > 4 else 7)
TPB = 480
ESTILO = CFG.get("estilo", "swing")                    # swing | bossa | vals (3/4) | balada
BPB = int(CFG.get("compas", 4))                        # tiempos por compás (4, o 3 en vals)
SWING = 0.5 if ESTILO == "bossa" else (0.67 if TEMPO <= 90 else (0.65 if TEMPO <= 130 else 0.62))
MS = 60000 / TEMPO / TPB

# ---------- cifrado ----------
PC = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6,
      "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11, "Cb": 11}
NAME = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
# 3ª, 5ª y nota de paso (6ª/7ª) que usa la línea de bajo
Q = {"maj7": (4, 7, 9), "6": (4, 7, 9), "m7": (3, 7, 10), "m6": (3, 7, 9), "mmaj7": (3, 7, 11),
     "7": (4, 7, 10), "7b9": (4, 7, 10), "7alt": (4, 8, 10), "m7b5": (3, 6, 10), "dim7": (3, 6, 9),
     "sus": (5, 7, 10)}
# escala de cada calidad (para las líneas por grados conjuntos) y notas del acorde
SCALE = {"maj7": (0, 2, 4, 5, 7, 9, 11), "6": (0, 2, 4, 5, 7, 9, 11), "m7": (0, 2, 3, 5, 7, 9, 10),
         "m6": (0, 2, 3, 5, 7, 9, 11), "mmaj7": (0, 2, 3, 5, 7, 9, 11), "7": (0, 2, 4, 5, 7, 9, 10),
         "7b9": (0, 1, 4, 5, 7, 8, 10), "7alt": (0, 1, 3, 4, 6, 8, 10), "m7b5": (0, 1, 3, 5, 6, 8, 10),
         "dim7": (0, 2, 3, 5, 6, 8, 9, 11), "sus": (0, 2, 4, 5, 7, 9, 10)}
CT = {"maj7": (0, 4, 7, 9, 11), "6": (0, 4, 7, 9), "m7": (0, 3, 7, 10), "m6": (0, 3, 7, 9),
      "mmaj7": (0, 3, 7, 11), "7": (0, 4, 7, 10), "7b9": (0, 4, 7, 10), "7alt": (0, 4, 8, 10),
      "m7b5": (0, 3, 6, 10), "dim7": (0, 3, 6, 9), "sus": (0, 5, 7, 10)}

def quality(s):
    s = s.replace("(", "").replace(")", "").replace("♭", "b").replace("♯", "#").replace(" ", "")
    if s.startswith(("maj", "Maj", "M7", "Δ", "^")) or s in ("", "M", "maj9", "6/9"):
        return "6" if s.startswith("6") else "maj7"
    if s.startswith(("m7b5", "ø", "mi7b5", "-7b5")): return "m7b5"
    if s.startswith(("dim", "o", "°")): return "dim7"
    if s.startswith(("mMaj", "mmaj", "m^", "-^", "mΔ", "-Δ")): return "mmaj7"
    if s.startswith(("m6", "-6", "mi6")): return "m6"
    if s.startswith(("m", "-", "mi")): return "m7"
    if s.startswith("6"): return "6"
    if "sus" in s: return "sus"
    if "alt" in s or "#5" in s or "b13" in s: return "7alt"
    if "b9" in s: return "7b9"
    if s[:1] in ("7", "9", "1"): return "7"
    raise ValueError(f"No entiendo la calidad del acorde: '{s}'")

def ch(sym, beats):
    m = re.match(r"^([A-G](?:#|b|♭|♯)?)(.*)$", sym.strip().strip("()"))   # (G7) = acorde opcional: se toca
    if not m: raise ValueError(f"Acorde no válido: '{sym}'")
    root = m.group(1).replace("♭", "b").replace("♯", "#")
    return (PC[root], quality(m.group(2)), beats)

SERIES = [0, 10, 8, 6, 4, 2, 1, 11, 9, 7, 5, 3]          # anexo: serie 1 + serie 2 (bajando por tonos)
QUINTAS = [0, 5, 10, 3, 8, 1, 6, 11, 4, 9, 2, 7]          # anexo A1/A2: ciclo de 5ªs

def parrilla(cfg):
    p = cfg["parrilla"].upper()
    V = "7alt" if cfg.get("v_alterado") else "7"
    im = cfg.get("i_menor", "m6")
    bars = []
    if p in ("A1", "A2"):
        q = cfg.get("calidad", "maj7" if p == "A1" else "m6")
        n = int(cfg.get("compases_por_acorde", 1))
        for k in QUINTAS:
            bars += [[NAME[k] + q]] * n
        return bars
    for k in SERIES:
        ii, v, i = NAME[(k + 2) % 12], NAME[(k + 7) % 12], NAME[k]
        if p == "A3": bars += [[ii + "m7", v + V], [i + "maj7"]]
        elif p == "A4": bars += [[ii + "m7"], [v + V], [i + "maj7"], [i + "maj7"]]
        elif p == "A5": bars += [[ii + "m7b5", v + ("7alt" if cfg.get("v_alterado") else "7b9")], [i + im]]
        elif p == "A6": bars += [[ii + "m7b5"], [v + "7b9"], [i + im], [i + im]]
        else: raise ValueError(f"Parrilla desconocida: {p}")
    return bars

form = parrilla(CFG) if "parrilla" in CFG else CFG["compases"]
one = []
for bar in form:
    if len(bar) == 1:   one.append(ch(bar[0], BPB))
    elif len(bar) == 2: one += [ch(bar[0], 2), ch(bar[1], BPB - 2)]
    elif len(bar) == 3: one += [ch(bar[0], 2), ch(bar[1], 1), ch(bar[2], 1)]
    elif len(bar) == 4: one += [ch(c, 1) for c in bar]
    else: raise ValueError(f"Compás con demasiados acordes: {bar}")
choruses = int(CFG.get("coros", 1))
chords = one * choruses
kits = [("brush" if k.startswith("esc") else "sticks") for k in CFG.get("bateria", ["escobillas"])]
plan = lambda chorus: kits[chorus % len(kits)]
BAR_FILL = set(CFG.get("fills", []))

# ---------- contrabajo (walking en negras) ----------
# Para cada acorde de un compás entero se elige una de tres fórmulas:
#   escalar (50 %):          4 pasos de tono/semitono hasta el acorde siguiente   (D E F F# | G, G F E D | C)
#   arpegio + paso (30 %):   salto a nota del acorde y llegada por grado conjunto (D A F F# | G)
#   arpegio (20 %):          fórmulas 1-3-5, 1-5-6, 1-7-5... + aproximación
# En acordes de 2 tiempos: fundamental + aproximación (semitono, paso de escala o 5ª).
from itertools import product
LOW, HIGH = 28, 50                                       # Mi1 .. Re3, altura real
def nearest(pc, ref, lo=LOW, hi=HIGH):
    return min((n for n in range(lo, hi + 1) if n % 12 == pc), key=lambda n: (abs(n - ref), -n))
in_scale = lambda n, r, q: (n - r) % 12 in SCALE[q]
is_ct = lambda n, r, q: (n - r) % 12 in CT[q]
ok_range = lambda ns: min(ns) >= LOW and max(ns) <= HIGH + 3

def targets(pc, ref):                                    # la fundamental siguiente, en las dos octavas útiles
    return [n for n in range(LOW, HIGH + 1) if n % 12 == pc and abs(n - ref) <= 9]

def approach_score(c, T, r, q):                          # nota del tiempo 4 frente a la llegada
    if abs(T - c) == 1: return 1.0                       # semitono
    if abs(T - c) == 2 and in_scale(c, r, q): return 1.0 # paso de escala
    return -2.0

def escalar(R, r, q, nxt):
    cands = []
    for T in targets(nxt, R):
        for st in product((-2, -1, 1, 2), repeat=4):
            if sum(st) != T - R: continue
            changes = sum(1 for x, y in zip(st, st[1:]) if (x > 0) != (y > 0))
            if changes > 1: continue
            ns = [R, R + st[0], R + st[0] + st[1], R + st[0] + st[1] + st[2]]
            if not ok_range(ns + [T]): continue
            if ns[3] == T + 1 and not ns[2] > ns[3]: continue   # semitono superior solo bajando hacia él
            sc = 0.0
            for k in (1, 2):                             # tiempos 2 y 3
                if in_scale(ns[k], r, q): sc += 2
                elif abs((ns[k + 1] if k < 3 else T) - ns[k - 1]) == 2: sc -= 0.5   # cromatismo de paso
                else: sc -= 3
            sc += 1 if is_ct(ns[2], r, q) else 0         # nota del acorde en el tiempo 3
            sc += approach_score(ns[3], T, r, q)
            sc -= 1.5 * changes                          # mejor en una sola dirección
            sc -= 0.15 * abs((ns[2]) - 39)               # sin irse a los extremos del registro
            cands.append((sc, ns, T))
    return cands

def arpegio_paso(R, r, q, nxt):
    cands = []
    for T in targets(nxt, R):
        sgn = 1 if T >= R else -1
        for n2 in range(R - 9, R + 10):
            if n2 == R or not is_ct(n2, r, q): continue
            for d3 in (2, 3):
                for side in (-1, 1):
                    n3 = T + side * d3
                    if n3 in (n2, R) or not in_scale(n3, r, q) or abs(n3 - n2) > 5: continue
                    c = T + side * 1                     # llegada por semitono
                    ns = [R, n2, n3, c]
                    if not ok_range(ns + [T]): continue
                    sc = 2.0 + (1 if is_ct(n3, r, q) else 0)
                    sc -= 0.25 * max(0, abs(n2 - R) - 7)
                    sc -= 0.15 * abs(n3 - 39)
                    cands.append((sc, ns, T))
    return cands

def arpegio(R, r, q, nxt, t3, t5, t6):
    sev = -1 if q in ("maj7", "6", "mmaj7") else -2
    if R <= 41:
        pat = random.choice([[0, t3, t5], [0, 2, t3], [0, t5, t6], [0, t3, t5]])
    else:
        pat = random.choice([[0, sev, -5], [0, -3, -5], [0, -5, -(12 - t3)]])
    body = [R + p for p in pat]
    return body, approach(body[-1], r, q, nxt)

def approach(last, r, q, nxt):                           # nota de aproximación (acordes de 2 tiempos)
    target = nearest(nxt, last)
    opts = [o for o in (target - 1, target + 1, target + 7, target - 5, target - 2, target + 2)
            if LOW <= o <= HIGH + 3 and o != last and abs(o - last) <= 9
            and (abs(o - target) != 2 or in_scale(o, r, q))
            and (o != target + 1 or last > o)]                 # semitono superior solo bajando hacia él
    w = [3 if abs(o - target) == 1 else 2 for o in opts]
    return (random.choices(opts, w)[0] if opts else target - 1), target

recent = []                                              # fórmulas usadas en los últimos compases enteros
shape = lambda ns: tuple(b - a for a, b in zip(ns, ns[1:]))

def pick(cands):                                         # elige entre las mejores, con algo de azar
    cands = [(sc - (4.0 if shape(ns) in recent else 0), ns, T) for sc, ns, T in cands]   # no repetir
    best = max(c[0] for c in cands)
    top = [c for c in cands if c[0] >= best - 1.0]
    return random.choice(top)

final_pc = (ch(CFG["final"], 4)[0] if "final" in CFG else          # "final": acorde del golpe final
            chords[0][0] if CFG.get("tipo", "ejercicio") == "tema" else chords[-1][0])
bass, beat = [], 0
root = nearest(chords[0][0], 38)
for i, (r, q, dur) in enumerate(chords):
    t3, t5, t6 = Q[q]
    nxt = chords[i + 1][0] if i + 1 < len(chords) else final_pc   # el último acorde lleva a la nota final
    if dur == 1:
        notes, nroot = [root], nearest(nxt, root)
    elif dur == 2:
        app, nroot = approach(root, r, q, nxt)
        notes = [root, app]
    else:
        fam = random.choices(["escalar", "arpegio_paso", "arpegio"], [0.5, 0.3, 0.2])[0]
        cands = escalar(root, r, q, nxt) if fam == "escalar" else \
                arpegio_paso(root, r, q, nxt) if fam == "arpegio_paso" else []
        if cands:
            sc, notes, nroot = pick(cands)
            recent = (recent + [shape(notes)])[-2:]
        else:
            body, (app, nroot) = arpegio(root, r, q, nxt, t3, t5, t6)
            notes = body + [app]
    for j, n in enumerate(notes[:dur]):
        bass.append((beat + j, n, 92 if j == 0 else random.randint(76, 86)))
    beat += dur
    if nroot is not None:
        root = nroot
END = beat
bass.append((END, root, 96))                             # nota final (la fundamental a la que llega la línea)
ghosts = [(t + SWING, (n2 if random.random() < 0.6 else n), random.randint(55, 70))
          for (t, n, v), (t2, n2, v2) in zip(bass, bass[1:]) if t2 - t == 1 and random.random() < 0.16]

LEN = {}                                                 # duración de cada nota del bajo (si no, 0.93 tiempos)

def bajo_dos(chords, final_pc):
    """Balada (2-feel) y vals: fundamental en blanca y aproximación al acorde siguiente en el resto del compás."""
    out, beat, root = [], 0, nearest(chords[0][0], 38)
    for i, (r, q, dur) in enumerate(chords):
        nxt = chords[i + 1][0] if i + 1 < len(chords) else final_pc
        if dur >= 3:
            app, nroot = approach(root, r, q, nxt)
            out += [(beat, root, 92), (beat + 2, app, 82)]
            LEN[beat], LEN[beat + 2] = 1.92, dur - 2 - 0.08
        else:
            nroot = nearest(nxt, root)
            out.append((beat, root, 92)); LEN[beat] = dur - 0.08
        beat += dur; root = nroot
    out.append((beat, root, 96))
    return out, beat

def bajo_bossa(chords, final_pc):
    """Bossa nova: fundamental (negra con puntillo) y 5ª en corchea; en acordes de 4 tiempos, 5ª en el 3 y fundamental en el 4&."""
    out, beat, root = [], 0, nearest(chords[0][0], 36)
    for i, (r, q, dur) in enumerate(chords):
        nxt = chords[i + 1][0] if i + 1 < len(chords) else final_pc
        t5 = Q[q][1]
        fifth = root + t5 if root + t5 <= HIGH else root - (12 - t5)
        if dur >= 4:
            out += [(beat, root, 90), (beat + 1.5, fifth, 70), (beat + 2, fifth, 84), (beat + 3.5, root, 68)]
            LEN.update({beat: 1.42, beat + 1.5: 0.45, beat + 2: 1.42, beat + 3.5: 0.45})
        elif dur >= 2:
            out += [(beat, root, 90), (beat + 1.5, fifth, 70)]
            LEN.update({beat: 1.42, beat + 1.5: 0.45})
        else:
            out.append((beat, root, 88)); LEN[beat] = 0.9
        beat += dur; root = nearest(nxt, root, 31, 47)
    out.append((beat, root, 96))
    return out, beat

if ESTILO in ("balada", "vals"):
    bass, END = bajo_dos(chords, final_pc); ghosts = []
elif ESTILO == "bossa":
    bass, END = bajo_bossa(chords, final_pc); ghosts = []

# ---------- batería ----------
COUNT_IN = 8                                             # 2 compases de claqueta
n_bars = END // 4
bars_per_chorus = n_bars // choruses
style_of = lambda bar: plan(bar // bars_per_chorus)
sticks, brush = [], []

first = style_of(0)
for b, v in [(0, 80), (2, 80), (4, 85), (5, 85), (6, 85), (7, 85)]:
    (brush if first == "brush" else sticks).append(
        (b, 38 if first == "brush" else 37, v - (25 if first == "brush" else 0)))

def sw(b):
    return b + SWING

for bar in range(n_bars):
    b0 = COUNT_IN + bar * 4
    st = style_of(bar)
    in_chorus = bar % bars_per_chorus
    last_of_chorus = (bar + 1) % bars_per_chorus == 0 and bar != n_bars - 1
    switching = last_of_chorus and style_of(bar + 1) != st
    first_of_chorus = in_chorus == 0
    tgt = brush if st == "brush" else sticks
    tgt += [(b0 + 1, 44, 70), (b0 + 3, 44, 72)]                       # charles con el pie en 2 y 4
    if switching:                    # cambio escobillas <-> baquetas: 2 tiempos tocando y luego solo charles
        if st == "brush":
            tgt += [(b0, 38, 52), (b0 + 1, 38, 70), (sw(b0 + 1), 38, 45), (b0, 60, 70)]
            # pequeño break con baquetas en el tiempo 4: tresillo negra + corchea, ambos en el timbal
            if style_of(bar + 1) == "sticks":
                sticks.extend([(b0 + 3, 41, 68), (b0 + 3 + 2/3, 41, 76)])
        else:
            tgt += [(b0, 51, 80), (b0 + 1, 51, 92), (sw(b0 + 1), 51, 62), (b0 + 1, 38, 60)]
        continue
    if st == "sticks":
        tgt += [(b0, 51, 78), (b0 + 1, 51, 92), (sw(b0 + 1), 51, 62),       # ride: din, din-ga, din, din-ga
                (b0 + 2, 51, 80), (b0 + 3, 51, 94), (sw(b0 + 3), 51, 64)]
        tgt += [(b0 + q, 36, random.randint(30, 38)) for q in range(4)]    # bombo "feathering"
        if first_of_chorus:
            tgt += [(b0, 49, 52), (b0, 36, 58)]                            # crash suave al entrar
        elif last_of_chorus or in_chorus in BAR_FILL:
            tgt += [(b0 + 2 + k / 3, 38, 48 + k * 8) for k in range(6)] + [(sw(b0 + 3), 36, 70)]
        elif random.random() < 0.45:                                        # comping suave de caja
            tgt.append((random.choice([sw(b0 + 1), sw(b0 + 3), sw(b0 + 2)]), 38, random.randint(34, 48)))
    else:
        # mano izquierda: barrido (stir) cada 2 tiempos; mano derecha: patrón de ride en la caja
        tgt += [(b0, 60, random.randint(66, 76)), (b0 + 2, 60, random.randint(66, 76))]
        tgt += [(b0, 38, 44), (b0 + 1, 38, 72), (sw(b0 + 1), 38, 40),
                (b0 + 2, 38, 46), (b0 + 3, 38, 74), (sw(b0 + 3), 38, 42)]
        tgt += [(b0 + q, 36, random.randint(26, 34)) for q in range(4)]
        if first_of_chorus and bar > 0:
            tgt += [(b0, 49, 60), (b0, 36, 60)]
        if last_of_chorus or in_chorus in BAR_FILL:
            random.random()                     # mantiene la secuencia aleatoria de las pistas aprobadas
            tgt.append((b0 + 3, 64, 80))                                    # barrido corto de acento
            tgt.append((sw(b0 + 3), 38, 66))
fin = COUNT_IN + END                                                        # golpe final
last_kit = brush if style_of(n_bars - 1) == "brush" else sticks
last_kit += [(fin, 49, 95 if last_kit is sticks else 75), (fin, 36, 85 if last_kit is sticks else 60),
             (fin, 62, 1) if last_kit is brush else (fin, 51, 70)]

# ---------- batería de bossa, vals y balada ----------
if ESTILO != "swing":
    COUNT_IN = 2 * BPB
    n_bars = END // BPB
    bars_per_chorus = n_bars // choruses
    if ESTILO == "bossa":
        style_of = lambda bar: "sticks"                      # bossa: aro (cross-stick), charles y bombo
    elif ESTILO == "balada":
        style_of = lambda bar: "brush"                       # balada: escobillas todo el tema
    else:
        style_of = lambda bar: plan(bar // bars_per_chorus)
    sticks, brush = [], []
    first = style_of(0)
    cnt = [0, 2, 4, 5, 6, 7] if BPB == 4 else [0, 3, 4, 5]
    for b in cnt:                                            # claqueta
        if first == "brush": brush.append((b, 38, 55 if b < BPB else 60))
        else: sticks.append((b, 37, 75 if b < BPB else 85))
    for bar in range(n_bars):
        b0 = COUNT_IN + bar * BPB
        st = style_of(bar)
        in_chorus = bar % bars_per_chorus
        last_of_chorus = (bar + 1) % bars_per_chorus == 0 and bar != n_bars - 1
        switching = last_of_chorus and style_of(bar + 1) != st
        tgt = brush if st == "brush" else sticks
        if ESTILO == "bossa":
            for e in range(8):                                # charles cerrado en corcheas rectas
                tgt.append((b0 + e / 2, 42, 52 if e % 2 == 0 else 38))
            rim = [0, 1.5, 3] if bar % 2 == 0 else [1, 2.5]   # aro en clave de dos compases
            tgt += [(b0 + x, 37, random.randint(62, 70)) for x in rim]
            tgt += [(b0, 36, 62), (b0 + 1.5, 36, 40), (b0 + 2, 36, 58), (b0 + 3.5, 36, 40)]
        elif ESTILO == "balada":
            tgt += [(b0 + q, 60, random.randint(60, 68)) for q in range(4)]          # barrido en cada tiempo
            tgt += [(b0 + 1, 38, 58), (b0 + 3, 38, 60), (sw(b0 + 3), 38, 34)]          # golpes suaves en 2 y 4
            tgt += [(b0 + 1, 44, 66), (b0 + 3, 44, 68), (b0, 36, 28), (b0 + 2, 36, 26)]
        else:                                                 # vals de jazz (3/4)
            tgt += [(b0 + 1, 44, 66), (b0 + 2, 44, 68), (b0, 36, random.randint(28, 34))]
            if st == "sticks":
                tgt += [(b0, 51, 84), (b0 + 1, 51, 90), (sw(b0 + 1), 51, 60), (b0 + 2, 51, 80)]
                if in_chorus == 0:
                    tgt += [(b0, 49, 52), (b0, 36, 58)]
                elif random.random() < 0.3:
                    tgt.append((sw(b0 + 2), 38, random.randint(34, 46)))
            else:
                tgt += [(b0, 60, random.randint(66, 76))]
                tgt += [(b0, 38, 46), (b0 + 1, 38, 72), (sw(b0 + 1), 38, 40), (b0 + 2, 38, 70)]
                if in_chorus == 0 and bar > 0:
                    tgt += [(b0, 49, 60), (b0, 36, 60)]
            if switching and st == "brush":                  # break con baquetas: tresillo de negra + corchea
                sticks.extend([(b0 + 2, 41, 68), (b0 + 2 + 2/3, 41, 76)])
    fin = COUNT_IN + END
    last_kit = brush if style_of(n_bars - 1) == "brush" else sticks
    last_kit += [(fin, 49, 75 if last_kit is brush else 85), (fin, 36, 60 if last_kit is brush else 75)]

# ---------- MIDI ----------
def write(path, events, lengths, jitter_ms, ch=0, ccs=()):
    m = mido.MidiFile(ticks_per_beat=TPB); tr = mido.MidiTrack(); m.tracks.append(tr)
    tr.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(TEMPO), time=0))
    for cc, val in ccs:
        tr.append(mido.Message("control_change", control=cc, value=val, channel=ch, time=0))
    msgs = []
    for ev in events:
        t, n, v = ev[:3]; kind = ev[3] if len(ev) > 3 else None
        on = max(8, int(round(t * TPB + random.uniform(-jitter_ms, jitter_ms) / MS)))
        msgs += [(on, 1, n, v), (on + int(lengths(t, n, kind) * TPB), 0, n, 0)]
    msgs.sort(key=lambda x: (x[0], x[1]))
    last = 0
    for tick, k, n, v in msgs:
        tr.append(mido.Message("note_on" if k else "note_off", note=n, velocity=v, channel=ch, time=tick - last))
        last = tick
    m.save(path)

vel = lambda v: min(127, v + 4)                         # pulsación media (capas mf/f de Meatbass)
bev = [(COUNT_IN + t, n, vel(v)) for t, n, v in bass] + [(COUNT_IN + t, n, 34, "g") for t, n, v in ghosts]
write(OUT + "_bajo.mid", bev,
      lambda t, n, k: 2.5 if t >= COUNT_IN + END else (0.2 if k == "g" else LEN.get(t - COUNT_IN, 0.93)), 5,
      ccs=[(104, 4), (107, 0), (106, 64), (100, 10)])   # Meatbass: caída corta, una voz, «Tame» ~10 ms
                                                        # (ataque menos agresivo) y arranque de ~5 ms

beat_s = 60 / TEMPO                                     # barrido: ataque = 1 tiempo, cola larga
cc55 = max(8, min(127, round(beat_s / 2 * 127)))
write(OUT + "_stir.mid", [e for e in brush if e[1] in (60, 62, 64)],
      lambda t, n, k: 2.0 if n == 60 else 0.5, 4, ccs=[(55, cc55), (56, 127), (57, 127)])
PARTS = {"caja": (38, 40), "charles": (42, 44, 46)}
for kit, evs, chn in (("escobillas", [e for e in brush if e[1] not in (60, 62, 64)], 0), ("baquetas", sticks, 9)):
    resto = [e for e in evs if not any(e[1] in v for v in PARTS.values())]
    for part, notes in list(PARTS.items()) + [("resto", None)]:
        sel = resto if notes is None else [e for e in evs if e[1] in notes]
        write(f"{OUT}_{kit}_{part}.mid", sel, lambda t, n, k: 0.5, 6, ch=chn)

json.dump({"tempo": TEMPO, "count_in_beats": COUNT_IN,
           "bajo": [[t, n] for t, n, v in bass if t < END]}, open(OUT + "_esperado.json", "w"))
print(f"{OUT}: {CFG.get('titulo', '')} · {TEMPO} bpm · {n_bars} compases · {choruses} coro(s) · "
      f"batería {'/'.join(CFG.get('bateria', ['escobillas']))}")
