"""Escribe en pentagrama (LilyPond -> PDF/PNG) la línea de contrabajo de una pista, con su cifrado.
Uso: python3 partitura_bajo.py CONFIG.json PREFIJO SALIDA_SIN_EXTENSION [COMPASES] [TITULO]
Usa PREFIJO_esperado.json (lo escribe pista.py). Las ghost notes no se escriben.
El contrabajo se escribe una octava por encima de lo que suena, como es habitual."""
import json, re, subprocess, sys

CFG = json.load(open(sys.argv[1])); P = sys.argv[2]; OUT = sys.argv[3]
NBARS = int(sys.argv[4]) if len(sys.argv) > 4 else 32
TITLE = sys.argv[5] if len(sys.argv) > 5 else CFG.get("titulo", "")
E = json.load(open(P + "_esperado.json"))
d = {t: n for t, n in E["bajo"]}

sys.argv = [sys.argv[0], sys.argv[1], "120", "/tmp/_dummy"]      # reutiliza la forma de pista.py
src = open(__file__.replace("partitura_bajo.py", "pista.py")).read()
ns = {}
exec(src.split("# ---------- contrabajo")[0], ns)                 # solo la parte del cifrado
form = ns["form"]
LET = "cdefgab"; NAT = [0, 2, 4, 5, 7, 9, 11]
ACC = {-2: "eses", -1: "es", 0: "", 1: "is", 2: "isis"}

def names(pc):                                   # grafías posibles de una clase de altura: (letra, alteración)
    out = []
    for li, npc in enumerate(NAT):
        a = (pc - npc + 6) % 12 - 6
        if abs(a) <= 1: out.append((li, a))
    return out

def chord_info(sym):
    m = re.match(r"^([A-G])(#|b)?", sym.strip("()"))
    li = "CDEFGAB".index(m.group(1)); pc, q, _ = ns["ch"](sym, 4)
    return li, pc, q

def diatonic(m, sym):                            # grafía por la escala del acorde (letras consecutivas)
    li, pc, q = chord_info(sym)
    sc = ns["SCALE"][q]
    iv = (m - pc) % 12
    if len(sc) != 7 or iv not in sc: return None
    L = (li + sc.index(iv)) % 7
    return (L, (m % 12 - NAT[L] + 6) % 12 - 6)

def spell(m, prev, nxt, sym, sym_prev, sym_next):
    d = diatonic(m, sym)
    if d and abs(d[1]) <= 1: return d
    up = nxt is not None and nxt > m or (nxt is None and prev is not None and m > prev)
    dp = diatonic(prev, sym_prev) if prev is not None else None
    prev_letter = dp[0] if dp else None
    best = None
    for L, a in names(m % 12):
        sc = 2 if a == 0 else 0
        sc -= 3 if (L, a) in ((0, -1), (3, -1), (2, 1), (6, 1)) else 0      # Do♭, Fa♭, Mi♯, Si♯
        sc += 1 if (a == 1 and up) or (a == -1 and not up) else 0
        sc += 1.5 if L == prev_letter and ((a == -1 and not up) or (a == 1 and up)) else 0   # La–La♭–Sol, Do–Do♯–Re
        if best is None or sc > best[0]: best = (sc, (L, a))
    return best[1]

def lily_pitch(m, L, a):
    written = m + 12                                                   # escrito una octava arriba
    octv = (written - a) // 12 - 1                                     # octava de la letra (Do♭ pertenece a la de Do)
    return LET[L] + ACC[a] + ("'" * (octv - 3) if octv > 3 else "," * (3 - octv))

def cif(sym):                                    # cifrado como en el manual (Caveat, b/# como alteraciones)
    m = re.match(r"^\(?([A-G])(#|b)?(.*?)\)?$", sym)
    parts = [f'"{m.group(1)}"'] + ([r"\fl" if m.group(2) == "b" else r"\sh"] if m.group(2) else [])
    q = m.group(3).replace("b", "♭").replace("#", "♯")
    for chunk in re.split(r"([♭♯])", q):
        if chunk == "♭": parts.append(r"\fl")
        elif chunk == "♯": parts.append(r"\sh")
        elif chunk: parts.append(f'"{chunk}"')
    return "^\\markup \\override #'(font-name . \"Caveat Bold\") \\fontsize #4 \\concat { " + " ".join(parts) + " }"

notes = []
nbars = min(NBARS, len(form) * CFG.get("coros", 1))
beats = []
for bar in range(nbars):
    fbar = form[bar % len(form)]
    split = {1: [4], 2: [2, 2], 3: [2, 1, 1], 4: [1, 1, 1, 1]}[len(fbar)]
    beats += [c for c, du in zip(fbar, split) for _ in range(du)]
last = None
for t in range(nbars * 4):
    m = d[t]; prev = d.get(t - 1); nxt = d.get(t + 1)
    L, a = spell(m, prev, nxt, beats[t], beats[t - 1] if t else beats[t], beats[t + 1] if t + 1 < len(beats) else beats[t])
    txt = lily_pitch(m, L, a) + "4"
    if beats[t] != last: txt += cif(beats[t])
    last = beats[t]
    notes.append(txt)

ly = r"""\version "2.24.0"
\paper { #(set-paper-size "a4") indent = 0 system-system-spacing.basic-distance = #13 ragged-last = ##f }
\header { title = "%s" subtitle = "Línea de contrabajo (suena una octava más grave)" tagline = ##f }
fl = \markup \concat { \hspace #0.35 \raise #0.9 \fontsize #-2.5 \flat \hspace #0.2 }
sh = \markup \concat { \hspace #0.35 \raise #1.0 \fontsize #-3 \sharp \hspace #0.2 }
\layout { \context { \Staff \override TextScript.staff-padding = #3 } }
<<
  \new Staff { \clef bass \time 4/4 \override Score.BarNumber.break-visibility = ##(#f #t #t)
    %s \bar "|." }
>>
""" % (TITLE, " ".join(n + ((" | \\break" if (i + 1) % 16 == 0 else " |") if (i + 1) % 4 == 0 else "") for i, n in enumerate(notes)))
open(OUT + ".ly", "w").write(ly)
subprocess.run(["lilypond", "-dno-point-and-click", "-o", OUT, OUT + ".ly"], check=True,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(["lilypond", "-dno-point-and-click", "-dresolution=110", "--png", "-o", OUT, OUT + ".ly"],
               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("Partitura:", OUT + ".pdf")
