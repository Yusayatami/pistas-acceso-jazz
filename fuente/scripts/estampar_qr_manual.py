"""Estampa un QR (vectorial) con su rótulo en la esquina superior derecha de páginas de un PDF.
Uso: python3 estampar_qr.py ENTRADA.pdf SALIDA.pdf
Las páginas y direcciones están en PAGINAS (número de página 1-based -> (slug, rótulo))."""
import io, sys
import qrcode
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

BASE = "https://yusayatami.github.io/pistas-acceso-jazz/"
# Cada página se reconoce por su etiqueta de cabecera («U2 · Semana 1 · Comping») y su texto, no por su número:
# así los QR caen en su sitio aunque el manual cambie de paginación.
import re as _re
TEMAS = {"Afternoon in Paris": "afternoon-in-paris", "Satin Doll": "satin-doll", "Four": "four", "Blue Monk": "blue-monk",
         "Impressions": "impressions", "Softly as in a Morning Sunrise": "softly-as-in-a-morning-sunrise",
         "Blue Bossa": "blue-bossa", "Autumn Leaves": "autumn-leaves", "Lullaby of Birdland": "lullaby-of-birdland",
         "In a Sentimental Mood": "in-a-sentimental-mood", "All Blues": "all-blues", "Bessie's Blues": "bessies-blues"}

def destino(texto):
    """Página de la web a la que apunta el QR de una página del manual (None = sin QR)."""
    t = " ".join(texto.split())
    if _re.search(r"Grado Superior de Jazz Introducci[oó]n", t[:120]): return ""      # índice de todas las pistas
    m = _re.search(r"U(\d) · Semanas? ([\d–]+) · (\w+)", t)
    if not m: return None
    u, sem, ap = int(m.group(1)), m.group(2), m.group(3)
    cuerpo = t[m.end():]
    menor = u in (4, 5, 6)
    if ap == "Primera":
        if u == 9: return f"u9-semana-{sem}-primera-vista"
        return f"u{u}-primera-vista"
    if ap == "Simulacro":
        return "u9-simulacro" if "Simulacro · fragmento" in cuerpo else ""
    if ap == "Autoevaluación": return None
    if ap == "Repertorio":
        if u in (8, 9): return ""                                           # aplicación / repertorio de examen
        head = cuerpo[:160]                                              # el título va justo tras la etiqueta
        hits = [(head.find(n), -len(n), s) for n, s in TEMAS.items() if n in head]
        return min(hits)[2] if hits else None
    if ap == "Técnica" and u in (7, 8): return "autumn-leaves" if u == 7 else "four"   # estudios 1 y 2
    p = _re.search(r"parrilla (A[1-6])", cuerpo)
    if p: return p.group(1).lower()
    if ap == "Transcripción" and u in (1, 4):                               # solos de Cedar Walton y Wynton Kelly
        return "afternoon-in-paris" if u == 1 else "softly-as-in-a-morning-sunrise"
    if ap in ("Comping", "Transcripción", "Repaso", "Improvisación"): return "a5" if menor else "a3"
    if ap == "Técnica": return "a2" if menor else "a1"
    return None

def paginas(reader):
    out = {}
    for i, p in enumerate(reader.pages, 1):
        d = destino(p.extract_text() or "")
        if d: out[i] = d                                 # sin QR al índice general de la web (petición de Ramón)
    return out

# (mapa por número de página de la versión del 23-11-2026, solo como referencia)
PAGINAS_REF = {4: ('', 'Todas las pistas del manual|Parrillas, lecturas y temas'), 5: ('a1', 'Parrilla A1 · Blanca 50 y 70|Contrabajo y batería'), 6: ('a3', 'Parrilla A3 · Blanca 50 y 70|Contrabajo y batería'), 7: ('a1', 'Parrilla A1 · Blanca 50 y 70|Contrabajo y batería'), 8: ('afternoon-in-paris', 'Contrabajo y batería|Pista de Afternoon in Paris'), 9: ('a1', 'Parrilla A1 · Blanca 50 y 70|Contrabajo y batería'), 10: ('a3', 'Parrilla A3 · Blanca 50 y 70|Contrabajo y batería'), 11: ('a1', 'Parrilla A1 · Blanca 50 y 70|Contrabajo y batería'), 12: ('a1', 'Parrilla A1 · Blanca 50 y 70|Contrabajo y batería'), 13: ('a3', 'Parrilla A3 · Blanca 50 y 70|Contrabajo y batería'), 14: ('a1', 'Parrilla A1 · Blanca 50 y 70|Contrabajo y batería'), 15: ('afternoon-in-paris', 'Contrabajo y batería|Pista de Afternoon in Paris'), 16: ('u1-primera-vista', 'Contrabajo y batería|Tempo escrito y más lento'), 17: ('afternoon-in-paris', 'Contrabajo y batería|Tempo de trabajo y de examen'), 19: ('a4', 'Parrilla A4 · Blanca 50 y 70|Contrabajo y batería'), 20: ('a3', 'Parrilla A3 · Blanca 50 y 70|Contrabajo y batería'), 21: ('a3', 'Parrilla A3 · Blanca 50 y 70|Contrabajo y batería'), 22: ('a3', 'Parrilla A3 · Blanca 50 y 70|Contrabajo y batería'), 23: ('a4', 'Parrilla A4 · Blanca 50 y 70|Contrabajo y batería'), 24: ('a3', 'Parrilla A3 · Blanca 50 y 70|Contrabajo y batería'), 25: ('a3', 'Parrilla A3 · Blanca 50 y 70|Contrabajo y batería'), 26: ('a3', 'Parrilla A3 · Blanca 50 y 70|Contrabajo y batería'), 27: ('u2-primera-vista', 'Contrabajo y batería|Tempo escrito y más lento'), 28: ('satin-doll', 'Contrabajo y batería|Tempo de trabajo y de examen'), 29: ('four', 'Contrabajo y batería|Tempo de trabajo y de examen'), 31: ('a4', 'Parrilla A4 · Blanca 50 y 70|Contrabajo y batería'), 32: ('a3', 'Parrilla A3 · Blanca 50 y 70|También con V alterado'), 33: ('a3', 'Parrilla A3 · Blanca 50 y 70|También con V alterado'), 34: ('a3', 'Parrilla A3 · Blanca 50 y 70|También con V alterado'), 35: ('a4', 'Parrilla A4 · Blanca 50 y 70|Contrabajo y batería'), 36: ('a3', 'Parrilla A3 · Blanca 50 y 70|También con V alterado'), 37: ('a3', 'Parrilla A3 · Blanca 50 y 70|También con V alterado'), 38: ('a3', 'Parrilla A3 · Blanca 50 y 70|También con V alterado'), 39: ('u3-primera-vista', 'Contrabajo y batería|Tempo escrito y más lento'), 40: ('blue-monk', 'Contrabajo y batería|Tempo de trabajo y de examen'), 41: ('impressions', 'Contrabajo y batería|Tempo de trabajo y de examen'), 43: ('a2', 'Parrilla A2 · Blanca 50 y 70|Contrabajo y batería'), 44: ('a5', 'Parrilla A5 · Blanca 50 y 70|Contrabajo y batería'), 45: ('a2', 'Parrilla A2 · Blanca 50 y 70|Contrabajo y batería'), 46: ('softly-as-in-a-morning-sunrise', 'Contrabajo y batería|Pista de Softly as in a Morning Sunrise'), 47: ('a2', 'Parrilla A2 · Blanca 50 y 70|Contrabajo y batería'), 48: ('a5', 'Parrilla A5 · Blanca 50 y 70|Contrabajo y batería'), 49: ('a2', 'Parrilla A2 · Blanca 50 y 70|Contrabajo y batería'), 50: ('a2', 'Parrilla A2 · Blanca 50 y 70|Contrabajo y batería'), 51: ('a5', 'Parrilla A5 · Blanca 50 y 70|Contrabajo y batería'), 52: ('a2', 'Parrilla A2 · Blanca 50 y 70|Contrabajo y batería'), 53: ('softly-as-in-a-morning-sunrise', 'Contrabajo y batería|Pista de Softly as in a Morning Sunrise'), 54: ('u4-primera-vista', 'Contrabajo y batería|Tempo escrito y más lento'), 55: ('softly-as-in-a-morning-sunrise', 'Contrabajo y batería|Tempo de trabajo y de examen'), 57: ('a6', 'Parrilla A6 · Blanca 50 y 70|Contrabajo y batería'), 58: ('a5', 'Parrilla A5 · Blanca 50 y 70|Contrabajo y batería'), 59: ('a5', 'Parrilla A5 · Blanca 50 y 70|Contrabajo y batería'), 60: ('a5', 'Parrilla A5 · Blanca 50 y 70|Contrabajo y batería'), 61: ('a6', 'Parrilla A6 · Blanca 50 y 70|Contrabajo y batería'), 62: ('a5', 'Parrilla A5 · Blanca 50 y 70|Contrabajo y batería'), 63: ('a5', 'Parrilla A5 · Blanca 50 y 70|Contrabajo y batería'), 64: ('a5', 'Parrilla A5 · Blanca 50 y 70|Contrabajo y batería'), 65: ('u5-primera-vista', 'Contrabajo y batería|Tempo escrito y más lento'), 66: ('blue-bossa', 'Contrabajo y batería|Tempo de trabajo y de examen'), 67: ('autumn-leaves', 'Contrabajo y batería|Tempo de trabajo y de examen'), 69: ('a6', 'Parrilla A6 · Blanca 50 y 70|Contrabajo y batería'), 70: ('a5', 'Parrilla A5 · Blanca 50 y 70|También con V alterado'), 71: ('a5', 'Parrilla A5 · Blanca 50 y 70|También con V alterado'), 72: ('a5', 'Parrilla A5 · Blanca 50 y 70|También con V alterado'), 73: ('a6', 'Parrilla A6 · Blanca 50 y 70|Contrabajo y batería'), 74: ('a5', 'Parrilla A5 · Blanca 50 y 70|También con V alterado'), 75: ('a5', 'Parrilla A5 · Blanca 50 y 70|También con V alterado'), 76: ('a5', 'Parrilla A5 · Blanca 50 y 70|También con V alterado'), 77: ('u6-primera-vista', 'Contrabajo y batería|Tempo escrito y más lento'), 78: ('lullaby-of-birdland', 'Contrabajo y batería|Tempo de trabajo y de examen'), 79: ('in-a-sentimental-mood', 'Contrabajo y batería|Tempo de trabajo y de examen'), 81: ('autumn-leaves', 'Contrabajo y batería|Pista de Autumn Leaves'), 82: ('a3', 'Parrilla A3 · Blanca 50 y 70|Contrabajo y batería'), 83: ('a3', 'Parrilla A3 · Blanca 50 y 70|Contrabajo y batería'), 84: ('a3', 'Parrilla A3 · Blanca 50 y 70|Contrabajo y batería'), 85: ('a5', 'Parrilla A5 · Blanca 50 y 70|Contrabajo y batería'), 86: ('a5', 'Parrilla A5 · Blanca 50 y 70|Contrabajo y batería'), 87: ('a3', 'Parrilla A3 · Blanca 50 y 70|Contrabajo y batería'), 88: ('u7-primera-vista', 'Contrabajo y batería|Tempo escrito y más lento'), 89: ('all-blues', 'Contrabajo y batería|Tempo de trabajo y de examen'), 90: ('bessies-blues', 'Contrabajo y batería|Tempo de trabajo y de examen'), 91: ('four', 'Contrabajo y batería|Pista de Four'), 92: ('a3', 'Parrilla A3 · Blanca 50 y 70|Contrabajo y batería'), 93: ('a3', 'Parrilla A3 · Blanca 50 y 70|Contrabajo y batería'), 94: ('a5', 'Parrilla A5 · Blanca 50 y 70|Contrabajo y batería'), 95: ('a5', 'Parrilla A5 · Blanca 50 y 70|Contrabajo y batería'), 96: ('a5', 'Parrilla A5 · Blanca 50 y 70|Contrabajo y batería'), 97: ('a5', 'Parrilla A5 · Blanca 50 y 70|Contrabajo y batería'), 98: ('u8-primera-vista', 'Contrabajo y batería|Tempo escrito y más lento'), 99: ('', 'Todas las pistas del manual|Parrillas, lecturas y temas'), 101: ('u9-semana-1-primera-vista', 'Contrabajo y batería|Tempo escrito y más lento'), 102: ('u9-semana-2-primera-vista', 'Contrabajo y batería|Tempo escrito y más lento'), 103: ('', 'Todas las pistas del manual|Parrillas, lecturas y temas'), 104: ('', 'Todas las pistas del manual|Parrillas, lecturas y temas'), 105: ('u9-simulacro', 'Contrabajo y batería|Tempo escrito y más lento')}
pdfmetrics.registerFont(TTFont("DMSans-Bold", "/home/claude/DMSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DMSans", "/home/claude/DMSans-Regular.ttf"))
NARANJA, GRIS = HexColor("#C76B1A"), HexColor("#55606D")

SIZE = 50                      # lado del QR en pt (≈ 18 mm)
RIGHT, TOP = 544.05, 55.0      # borde derecho del texto de la cabecera; por debajo de su raya

def caption(sub):                                        # una sola línea, sobre el título: «PISTAS  Parrilla A3 · Blanca 50 y 70»
    l1, l2 = sub.split("|")
    if l1.startswith("Parrilla"): return l1 + (" · también con V alterado" if l2.startswith("También") else "")
    if l1.startswith("Todas"): return "Todas las pistas: parrillas, lecturas y temas"
    return l2

def overlay(w, h, slug, page, especial=False):
    q = qrcode.QRCode(border=0, error_correction=qrcode.constants.ERROR_CORRECT_L)
    q.add_data(BASE + (slug + "/" if slug else "")); q.make(fit=True)
    m = q.get_matrix(); n = len(m)
    buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=(w, h))
    if especial:                                         # página llena: el QR va en el recuadro «Cómo estudiarlo», sin rótulo
        size, x0, ytop = 44, 540.0 - 44, h - 683
        c.setFillColor(HexColor("#FFFFFF")); c.rect(x0 - 3, ytop - size - 3, size + 6, size + 6, stroke=0, fill=1)
    else:
        size, x0, ytop = SIZE, RIGHT - SIZE, h - TOP
    cell = size / n
    c.setFillColor(HexColor("#000000"))
    for r, row in enumerate(m):
        for k, on in enumerate(row):
            if on: c.rect(x0 + k * cell, ytop - (r + 1) * cell, cell + 0.02, cell + 0.02, stroke=0, fill=1)
    if not especial:
        tx = x0 - 9                                      # rótulo en dos líneas, espaciado, alineado a la derecha
        for y, lab in ((h - 62, "PISTAS"), (h - 71.5, "DE AUDIO")):
            cs = 1.1
            wl = pdfmetrics.stringWidth(lab, "DMSans-Bold", 7.5) + cs * (len(lab) - 1)
            t = c.beginText(tx - wl, y); t.setFont("DMSans-Bold", 7.5); t.setCharSpace(cs)
            t.setFillColor(NARANJA); t.textOut(lab); c.drawText(t)
    c.save(); buf.seek(0)
    return PdfReader(buf).pages[0]

def sin_hueco(pdf):                                      # páginas con texto donde iría el QR (esquina superior derecha)
    import subprocess
    out = subprocess.run(["pdftotext", "-bbox", pdf, "-"], capture_output=True, text=True).stdout
    llenas = set()
    for n, pag in enumerate(out.split("<page ")[1:], 1):
        for m in _re.finditer(r'xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)"', pag):
            x0, y0, x1, y1 = map(float, m.groups())
            if x1 > 488 and y1 > 53 and y0 < 107: llenas.add(n)
    return llenas

r = PdfReader(sys.argv[1]); wtr = PdfWriter()
MAPA = paginas(r); LLENAS = sin_hueco(sys.argv[1])
for i, p in enumerate(r.pages, 1):
    if i in MAPA:
        w, h = float(p.mediabox.width), float(p.mediabox.height)
        p.merge_page(overlay(w, h, MAPA[i], i, especial=i in LLENAS))
    wtr.add_page(p)
wtr.write(sys.argv[2])
print("QR estampados en", len(MAPA), "páginas ->", sys.argv[2])
if LLENAS & set(MAPA):
    print("Revisar a ojo: sin hueco arriba, el QR va abajo a la derecha (recuadro «Cómo estudiarlo») en las páginas",
          sorted(LLENAS & set(MAPA)))
