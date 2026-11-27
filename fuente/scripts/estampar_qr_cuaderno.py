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
SUB = {"a1": "Blanca 50 y 70", "a2": "Blanca 50 y 70", "a3": "Blanca 50 y 70 · También con V alterado",
       "a4": "Blanca 50 y 70", "a5": "Blanca 50 y 70 · También con V alterado", "a6": "Blanca 50 y 70"}
def paginas(reader):                                     # cada parrilla se reconoce por su etiqueta «Anexo · A3», no por su número
    import re
    out = {}
    for i, p in enumerate(reader.pages, 1):
        m = re.search(r"Anexo · (A[1-6])\b", " ".join((p.extract_text() or "").split())[:200])
        if m: out[i] = (m.group(1).lower(), SUB[m.group(1).lower()])
    return out
pdfmetrics.registerFont(TTFont("DMSans-Bold", "/home/claude/DMSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DMSans", "/home/claude/DMSans-Regular.ttf"))
NARANJA, GRIS = HexColor("#C76B1A"), HexColor("#55606D")

SIZE = 50                      # lado del QR en pt (≈ 18 mm)
RIGHT, TOP = 544.05, 55.0      # borde derecho del texto de la cabecera; por debajo de su raya

def overlay(w, h, slug, sub):
    q = qrcode.QRCode(border=0, error_correction=qrcode.constants.ERROR_CORRECT_L)
    q.add_data(BASE + slug + "/"); q.make(fit=True)
    m = q.get_matrix(); n = len(m); cell = SIZE / n
    buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=(w, h))
    x0, ytop = RIGHT - SIZE, h - TOP
    c.setFillColor(HexColor("#000000"))
    for r, row in enumerate(m):
        for k, on in enumerate(row):
            if on: c.rect(x0 + k * cell, ytop - (r + 1) * cell, cell + 0.02, cell + 0.02, stroke=0, fill=1)
    tx = x0 - 9                                             # rótulo en dos líneas, alineado a la derecha
    for y, lab in ((h - 62, "PISTAS"), (h - 71.5, "DE ACOMPAÑAMIENTO")):
        cs = 1.1
        wl = pdfmetrics.stringWidth(lab, "DMSans-Bold", 7.5) + cs * (len(lab) - 1)
        t = c.beginText(tx - wl, y); t.setFont("DMSans-Bold", 7.5); t.setCharSpace(cs)
        t.setFillColor(NARANJA); t.textOut(lab); c.drawText(t)
    c.save(); buf.seek(0)
    return PdfReader(buf).pages[0]

r = PdfReader(sys.argv[1]); wtr = PdfWriter(); PAGINAS = paginas(r)
for i, p in enumerate(r.pages, 1):
    if i in PAGINAS:
        w, h = float(p.mediabox.width), float(p.mediabox.height)
        p.merge_page(overlay(w, h, *PAGINAS[i]))
    wtr.add_page(p)
wtr.write(sys.argv[2])
print("QR estampados en", len(PAGINAS), "páginas ->", sys.argv[2])
