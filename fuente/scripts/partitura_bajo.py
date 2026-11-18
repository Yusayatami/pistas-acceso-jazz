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
FL = ["c", "des", "d", "ees", "e", "f", "ges", "g", "aes", "a", "bes", "b"]
SH = ["c", "cis", "d", "dis", "e", "f", "fis", "g", "gis", "a", "ais", "b"]

def prefer_sharp(sym):                       # grafía según la tonalidad a la que pertenece el acorde
    root = re.match(r"^[A-G](#|b)?", sym).group(0)
    if "#" in root: return True
    if "b" in root: return False
    pc, q, _ = ns["ch"](sym, 4)
    key = {"m7": pc - 2, "m6": pc + 3, "mmaj7": pc + 3, "m7b5": pc + 1, "dim7": pc + 1,
           "7": pc + 5, "7b9": pc + 5, "7alt": pc + 5, "sus": pc + 5}.get(q, pc) % 12
    return key in (7, 2, 9, 4, 11)                                  # Sol, Re, La, Mi, Si

def lily_pitch(m, nxt, sharp):
    pc = m % 12
    if nxt is not None and nxt - m == 1: name = SH[pc]               # sube por semitono: sostenido
    elif nxt is not None and nxt - m == -1: name = FL[pc]            # baja por semitono: bemol
    else: name = SH[pc] if sharp else FL[pc]
    o = (m + 12) // 12 - 1                                            # escrito una octava arriba
    return name + ("'" * (o - 3) if o > 3 else "," * (3 - o))

def lily_chord(sym, dur):
    m = re.match(r"^([A-G])(#|b)?(.*)$", sym)
    root = m.group(1).lower() + {"#": "is", "b": "es", None: ""}[m.group(2)]
    q = m.group(3).replace("(", "").replace(")", "")
    tab = {"maj7": "maj7", "m7": "m7", "7": "7", "7b9": "7.9-", "m7b5": "m7.5-", "m6": "m6", "6": "6",
           "7alt": "7.5+.9-", "dim7": "dim7", "mMaj7": "m7+", "7sus": "7sus4"}
    return f"{root}{dur}:{tab.get(q, q or 'maj7')}"

notes, chords_ly = [], []
seq = sorted(d)
for bar in range(min(NBARS, len(form) * CFG.get("coros", 1))):
    fbar = form[bar % len(form)]
    durs = {1: ["1"], 2: ["2", "2"], 3: ["2", "4", "4"], 4: ["4"] * 4}[len(fbar)]
    per_beat = [c for c, du in zip(fbar, durs) for _ in range(4 // int(du))]
    for k in range(4):
        t = bar * 4 + k
        nxt = d.get(t + 1)
        notes.append(lily_pitch(d[t], nxt, prefer_sharp(per_beat[k])) + "4")
    chords_ly += [lily_chord(c, du) for c, du in zip(fbar, durs)]

ly = r"""\version "2.24.0"
\paper { #(set-paper-size "a4") indent = 0 system-system-spacing.basic-distance = #13 ragged-last = ##f }
\header { title = "%s" subtitle = "Línea de contrabajo (suena una octava más grave)" tagline = ##f }
\layout { \context { \ChordNames \override ChordName.font-size = #2 } }
<<
  \new ChordNames { \chordmode { %s } }
  \new Staff { \clef bass \time 4/4 \override Score.BarNumber.break-visibility = ##(#f #t #t)
    %s \bar "|." }
>>
""" % (TITLE, " ".join(chords_ly), " ".join(n + ((" | \\break" if (i + 1) % 16 == 0 else " |") if (i + 1) % 4 == 0 else "") for i, n in enumerate(notes)))
open(OUT + ".ly", "w").write(ly)
subprocess.run(["lilypond", "-dno-point-and-click", "-o", OUT, OUT + ".ly"], check=True,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(["lilypond", "-dno-point-and-click", "-dresolution=110", "--png", "-o", OUT, OUT + ".ly"],
               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("Partitura:", OUT + ".pdf")
