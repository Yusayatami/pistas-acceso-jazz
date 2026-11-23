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
PAGINAS = {4: ('', 'Todas las pistas del manual|Parrillas, lecturas y temas'), 5: ('a1', 'Parrilla A1 · Blanca 50 y 70|Contrabajo y batería'), 6: ('a3', 'Parrilla A3 · Blanca 50 y 70|Contrabajo y batería'), 7: ('a1', 'Parrilla A1 · Blanca 50 y 70|Contrabajo y batería'), 8: ('afternoon-in-paris', 'Contrabajo y batería|Pista de Afternoon in Paris'), 9: ('a1', 'Parrilla A1 · Blanca 50 y 70|Contrabajo y batería'), 10: ('a3', 'Parrilla A3 · Blanca 50 y 70|Contrabajo y batería'), 11: ('a1', 'Parrilla A1 · Blanca 50 y 70|Contrabajo y batería'), 12: ('a1', 'Parrilla A1 · Blanca 50 y 70|Contrabajo y batería'), 13: ('a3', 'Parrilla A3 · Blanca 50 y 70|Contrabajo y batería'), 14: ('a1', 'Parrilla A1 · Blanca 50 y 70|Contrabajo y batería'), 15: ('afternoon-in-paris', 'Contrabajo y batería|Pista de Afternoon in Paris'), 16: ('u1-primera-vista', 'Contrabajo y batería|Tempo escrito y más lento'), 17: ('afternoon-in-paris', 'Contrabajo y batería|Tempo de trabajo y de examen'), 19: ('a4', 'Parrilla A4 · Blanca 50 y 70|Contrabajo y batería'), 20: ('a3', 'Parrilla A3 · Blanca 50 y 70|Contrabajo y batería'), 21: ('a3', 'Parrilla A3 · Blanca 50 y 70|Contrabajo y batería'), 22: ('a3', 'Parrilla A3 · Blanca 50 y 70|Contrabajo y batería'), 23: ('a4', 'Parrilla A4 · Blanca 50 y 70|Contrabajo y batería'), 24: ('a3', 'Parrilla A3 · Blanca 50 y 70|Contrabajo y batería'), 25: ('a3', 'Parrilla A3 · Blanca 50 y 70|Contrabajo y batería'), 26: ('a3', 'Parrilla A3 · Blanca 50 y 70|Contrabajo y batería'), 27: ('u2-primera-vista', 'Contrabajo y batería|Tempo escrito y más lento'), 28: ('satin-doll', 'Contrabajo y batería|Tempo de trabajo y de examen'), 29: ('four', 'Contrabajo y batería|Tempo de trabajo y de examen'), 31: ('a4', 'Parrilla A4 · Blanca 50 y 70|Contrabajo y batería'), 32: ('a3', 'Parrilla A3 · Blanca 50 y 70|También con V alterado'), 33: ('a3', 'Parrilla A3 · Blanca 50 y 70|También con V alterado'), 34: ('a3', 'Parrilla A3 · Blanca 50 y 70|También con V alterado'), 35: ('a4', 'Parrilla A4 · Blanca 50 y 70|Contrabajo y batería'), 36: ('a3', 'Parrilla A3 · Blanca 50 y 70|También con V alterado'), 37: ('a3', 'Parrilla A3 · Blanca 50 y 70|También con V alterado'), 38: ('a3', 'Parrilla A3 · Blanca 50 y 70|También con V alterado'), 39: ('u3-primera-vista', 'Contrabajo y batería|Tempo escrito y más lento'), 40: ('blue-monk', 'Contrabajo y batería|Tempo de trabajo y de examen'), 41: ('impressions', 'Contrabajo y batería|Tempo de trabajo y de examen'), 43: ('a2', 'Parrilla A2 · Blanca 50 y 70|Contrabajo y batería'), 44: ('a5', 'Parrilla A5 · Blanca 50 y 70|Contrabajo y batería'), 45: ('a2', 'Parrilla A2 · Blanca 50 y 70|Contrabajo y batería'), 46: ('softly-as-in-a-morning-sunrise', 'Contrabajo y batería|Pista de Softly as in a Morning Sunrise'), 47: ('a2', 'Parrilla A2 · Blanca 50 y 70|Contrabajo y batería'), 48: ('a5', 'Parrilla A5 · Blanca 50 y 70|Contrabajo y batería'), 49: ('a2', 'Parrilla A2 · Blanca 50 y 70|Contrabajo y batería'), 50: ('a2', 'Parrilla A2 · Blanca 50 y 70|Contrabajo y batería'), 51: ('a5', 'Parrilla A5 · Blanca 50 y 70|Contrabajo y batería'), 52: ('a2', 'Parrilla A2 · Blanca 50 y 70|Contrabajo y batería'), 53: ('softly-as-in-a-morning-sunrise', 'Contrabajo y batería|Pista de Softly as in a Morning Sunrise'), 54: ('u4-primera-vista', 'Contrabajo y batería|Tempo escrito y más lento'), 55: ('softly-as-in-a-morning-sunrise', 'Contrabajo y batería|Tempo de trabajo y de examen'), 57: ('a6', 'Parrilla A6 · Blanca 50 y 70|Contrabajo y batería'), 58: ('a5', 'Parrilla A5 · Blanca 50 y 70|Contrabajo y batería'), 59: ('a5', 'Parrilla A5 · Blanca 50 y 70|Contrabajo y batería'), 60: ('a5', 'Parrilla A5 · Blanca 50 y 70|Contrabajo y batería'), 61: ('a6', 'Parrilla A6 · Blanca 50 y 70|Contrabajo y batería'), 62: ('a5', 'Parrilla A5 · Blanca 50 y 70|Contrabajo y batería'), 63: ('a5', 'Parrilla A5 · Blanca 50 y 70|Contrabajo y batería'), 64: ('a5', 'Parrilla A5 · Blanca 50 y 70|Contrabajo y batería'), 65: ('u5-primera-vista', 'Contrabajo y batería|Tempo escrito y más lento'), 66: ('blue-bossa', 'Contrabajo y batería|Tempo de trabajo y de examen'), 67: ('autumn-leaves', 'Contrabajo y batería|Tempo de trabajo y de examen'), 69: ('a6', 'Parrilla A6 · Blanca 50 y 70|Contrabajo y batería'), 70: ('a5', 'Parrilla A5 · Blanca 50 y 70|También con V alterado'), 71: ('a5', 'Parrilla A5 · Blanca 50 y 70|También con V alterado'), 72: ('a5', 'Parrilla A5 · Blanca 50 y 70|También con V alterado'), 73: ('a6', 'Parrilla A6 · Blanca 50 y 70|Contrabajo y batería'), 74: ('a5', 'Parrilla A5 · Blanca 50 y 70|También con V alterado'), 75: ('a5', 'Parrilla A5 · Blanca 50 y 70|También con V alterado'), 76: ('a5', 'Parrilla A5 · Blanca 50 y 70|También con V alterado'), 77: ('u6-primera-vista', 'Contrabajo y batería|Tempo escrito y más lento'), 78: ('lullaby-of-birdland', 'Contrabajo y batería|Tempo de trabajo y de examen'), 79: ('in-a-sentimental-mood', 'Contrabajo y batería|Tempo de trabajo y de examen'), 81: ('autumn-leaves', 'Contrabajo y batería|Pista de Autumn Leaves'), 82: ('a3', 'Parrilla A3 · Blanca 50 y 70|Contrabajo y batería'), 83: ('a3', 'Parrilla A3 · Blanca 50 y 70|Contrabajo y batería'), 84: ('a3', 'Parrilla A3 · Blanca 50 y 70|Contrabajo y batería'), 85: ('a5', 'Parrilla A5 · Blanca 50 y 70|Contrabajo y batería'), 86: ('a5', 'Parrilla A5 · Blanca 50 y 70|Contrabajo y batería'), 87: ('a3', 'Parrilla A3 · Blanca 50 y 70|Contrabajo y batería'), 88: ('u7-primera-vista', 'Contrabajo y batería|Tempo escrito y más lento'), 89: ('all-blues', 'Contrabajo y batería|Tempo de trabajo y de examen'), 90: ('bessies-blues', 'Contrabajo y batería|Tempo de trabajo y de examen'), 91: ('four', 'Contrabajo y batería|Pista de Four'), 92: ('a3', 'Parrilla A3 · Blanca 50 y 70|Contrabajo y batería'), 93: ('a3', 'Parrilla A3 · Blanca 50 y 70|Contrabajo y batería'), 94: ('a5', 'Parrilla A5 · Blanca 50 y 70|Contrabajo y batería'), 95: ('a5', 'Parrilla A5 · Blanca 50 y 70|Contrabajo y batería'), 96: ('a5', 'Parrilla A5 · Blanca 50 y 70|Contrabajo y batería'), 97: ('a5', 'Parrilla A5 · Blanca 50 y 70|Contrabajo y batería'), 98: ('u8-primera-vista', 'Contrabajo y batería|Tempo escrito y más lento'), 99: ('', 'Todas las pistas del manual|Parrillas, lecturas y temas'), 101: ('u9-semana-1-primera-vista', 'Contrabajo y batería|Tempo escrito y más lento'), 102: ('u9-semana-2-primera-vista', 'Contrabajo y batería|Tempo escrito y más lento'), 103: ('', 'Todas las pistas del manual|Parrillas, lecturas y temas'), 104: ('', 'Todas las pistas del manual|Parrillas, lecturas y temas'), 105: ('u9-simulacro', 'Contrabajo y batería|Tempo escrito y más lento')}
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

def overlay(w, h, slug, sub, page):
    q = qrcode.QRCode(border=0, error_correction=qrcode.constants.ERROR_CORRECT_L)
    q.add_data(BASE + (slug + "/" if slug else "")); q.make(fit=True)
    m = q.get_matrix(); n = len(m)
    buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=(w, h))
    if page == 53:                                       # página llena: el QR va en el recuadro «Cómo estudiarlo», sin rótulo
        size, x0, ytop = 44, 540.0 - 44, h - 683
        c.setFillColor(HexColor("#FFFFFF")); c.rect(x0 - 3, ytop - size - 3, size + 6, size + 6, stroke=0, fill=1)
    else:
        size, x0, ytop = SIZE, RIGHT - SIZE, h - TOP
    cell = size / n
    c.setFillColor(HexColor("#000000"))
    for r, row in enumerate(m):
        for k, on in enumerate(row):
            if on: c.rect(x0 + k * cell, ytop - (r + 1) * cell, cell + 0.02, cell + 0.02, stroke=0, fill=1)
    if page != 53:
        tx = x0 - 9                                      # rótulo en dos líneas, espaciado, alineado a la derecha
        for y, lab in ((h - 62, "PISTAS"), (h - 71.5, "DE AUDIO")):
            cs = 1.1
            wl = pdfmetrics.stringWidth(lab, "DMSans-Bold", 7.5) + cs * (len(lab) - 1)
            t = c.beginText(tx - wl, y); t.setFont("DMSans-Bold", 7.5); t.setCharSpace(cs)
            t.setFillColor(NARANJA); t.textOut(lab); c.drawText(t)
    c.save(); buf.seek(0)
    return PdfReader(buf).pages[0]

r = PdfReader(sys.argv[1]); wtr = PdfWriter()
for i, p in enumerate(r.pages, 1):
    if i in PAGINAS:
        w, h = float(p.mediabox.width), float(p.mediabox.height)
        p.merge_page(overlay(w, h, *PAGINAS[i], i))
    wtr.add_page(p)
wtr.write(sys.argv[2])
print("QR estampados en", len(PAGINAS), "páginas ->", sys.argv[2])
