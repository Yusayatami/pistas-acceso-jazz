"""Genera la web de pistas (GitHub Pages) y los QR de cada página.
Uso: python3 generar_web.py CARPETA_SALIDA CARPETA_MP3"""
import os, shutil, sys
import qrcode
import qrcode.image.svg

OUT, MP3 = sys.argv[1], sys.argv[2]
BASE = "https://yusayatami.github.io/pistas-acceso-jazz/"

# página -> (título, subtítulo, [(nombre de la pista, clave del archivo)])
PAGINAS = {
    "a1": ("A1 · Acordes sueltos en modo mayor", "Ciclo de 5ªs · 4 compases por acorde",
           [("Acordes maj7", "A1_maj7"), ("Acordes 7", "A1_7"), ("Acordes m7", "A1_m7")]),
    "a2": ("A2 · Acordes sueltos en modo menor", "Ciclo de 5ªs · 4 compases por acorde",
           [("Acordes m6", "A2_m6"), ("Acordes 7(♭9)", "A2_7b9"), ("Acordes m7(♭5)", "A2_m7b5")]),
    "a3": ("A3 · II-V-I mayor corto", "Dos series descendiendo por tonos",
           [("II-V-I mayor", "A3"), ("II-V-I mayor con V alterado", "A3_V_alterado")]),
    "a4": ("A4 · II-V-I mayor largo", "Dos series descendiendo por tonos",
           [("II-V-I mayor", "A4")]),
    "a5": ("A5 · II-V-I menor corto", "Dos series descendiendo por tonos",
           [("II-V-I menor", "A5"), ("II-V-I menor con V alterado", "A5_V_alterado")]),
    "a6": ("A6 · II-V-I menor largo", "Dos series descendiendo por tonos",
           [("II-V-I menor", "A6")]),
}
TEMPOS = [("Blanca 50", "blanca50"), ("Blanca 70", "blanca70")]
SECCION = {k: "Parrillas de acordes" for k in PAGINAS}
NOTA = {k: ("Contrabajo y batería con escobillas. Dos compases de claqueta antes de empezar. "
            "La pista recorre los 12 tonos en el orden de la parrilla del cuaderno de anexos.") for k in PAGINAS}
# las tarjetas de parrillas pasan a llevar sus archivos
for k, (t, sub, tr) in list(PAGINAS.items()):
    PAGINAS[k] = (t, sub, [(n, [(lab, f"Pista_{key}_{tt}_escobillas.mp3") for lab, tt in TEMPOS]) for n, key in tr])
import json as _j
_L = _j.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "configuraciones", "lecturas.json")))
_T = _j.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "configuraciones", "temas.json")))
def _lect(key):
    t = _L[key][0]
    return [(f"Negra {t} · tempo escrito", f"Pista_Lectura_{key}_negra{t}.mp3"),
            (f"Negra {t - 20} · más lento", f"Pista_Lectura_{key}_negra{t - 20}.mp3")]
LECT_PAG = [("u1-primera-vista", "U1 · Semana 4", [("Lectura", "U1_S4")]),
            ("u2-primera-vista", "U2 · Semanas 3–4", [("Semana 3", "U2_S3"), ("Semana 4", "U2_S4")]),
            ("u3-primera-vista", "U3 · Semanas 3–4", [("Semana 3", "U3_S3"), ("Semana 4", "U3_S4")]),
            ("u4-primera-vista", "U4 · Semana 4", [("Lectura", "U4_S4")]),
            ("u5-primera-vista", "U5 · Semanas 3–4", [("Semana 3", "U5_S3"), ("Semana 4", "U5_S4")]),
            ("u6-primera-vista", "U6 · Semanas 3–4", [("Semana 3", "U6_S3"), ("Semana 4", "U6_S4")]),
            ("u7-primera-vista", "U7 · Semanas 3–4", [("Semana 3", "U7_S3"), ("Semana 4", "U7_S4")]),
            ("u8-primera-vista", "U8 · Semanas 3–4", [("Semana 3", "U8_S3"), ("Semana 4", "U8_S4")]),
            ("u9-semana-1-primera-vista", "U9 · Semana 1", [("Lectura", "U9_S1")]),
            ("u9-semana-2-primera-vista", "U9 · Semana 2", [("Lectura", "U9_S2")]),
            ("u9-simulacro", "U9 · Semana 3 · Simulacro", [("Fragmento de primera vista", "U9_Simulacro")])]
for slug, tit, cards in LECT_PAG:
    PAGINAS[slug] = (f"{tit} · Primera vista", "Lectura a primera vista sobre cifrado",
                     [(n, _lect(k)) for n, k in cards])
    SECCION[slug] = "Lecturas a primera vista"
    NOTA[slug] = ("Contrabajo y batería con escobillas, dos compases de claqueta. La pista toca la forma tres veces: "
                  "melodía, un chorus de improvisación y otra vez la melodía.")
TEMA_SLUG = {}
for key, v in _T.items():
    slug = key.lower().replace("_", "-"); TEMA_SLUG[key] = slug
    PAGINAS[slug] = (v["titulo"], "Tema libre" if key in ("Afternoon_in_Paris", "Softly_as_in_a_Morning_Sunrise") else "Tema obligado",
                     [("Pista", [(f"Trabajo · negra {v['trabajo']}", f"Pista_Tema_{key}_negra{v['trabajo']}_trabajo.mp3"),
                                 (f"Examen · negra {v['examen']}", f"Pista_Tema_{key}_negra{v['examen']}_examen.mp3")])])
    SECCION[slug] = "Temas"
    NOTA[slug] = {"bossa": "Contrabajo y batería en bossa nova. ", "vals": "Contrabajo y batería en vals de jazz (3/4). ",
                  "balada": "Contrabajo y batería con escobillas, en balada. "}.get(
        v["estilo"], "Contrabajo y batería: escobillas en la primera y la última vuelta, baquetas en las de en medio. ") + (
        "Dos compases de claqueta; la forma suena " + ("ocho veces (tema dos veces, improvisación y tema dos veces)."
        if v["compases"] == 12 else "cuatro veces: tema, dos chorus de improvisación y tema."))

CSS = """
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap');
*{box-sizing:border-box}
body{margin:0;font-family:'DM Sans',system-ui,sans-serif;color:#1d2733;background:#f6f7f9}
header{background:#1A4A7A;color:#fff;padding:22px 20px 18px}
header a{color:#cfe0f2;text-decoration:none;font-size:14px}
h1{margin:6px 0 4px;font-size:22px;font-weight:700}
.sub{margin:0;color:#cfe0f2;font-size:15px}
main{max-width:640px;margin:0 auto;padding:18px 16px 40px}
.card{background:#fff;border-radius:12px;padding:16px;margin-bottom:14px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.card h2{margin:0 0 12px;font-size:17px;color:#1A4A7A}
.tempos{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap}
.tempos button{flex:1;min-width:110px;border:2px solid #C76B1A;background:#fff;color:#C76B1A;border-radius:8px;
  padding:10px 8px;font:500 15px 'DM Sans',sans-serif;cursor:pointer}
.tempos button.on{background:#C76B1A;color:#fff}
audio{width:100%}
label{display:flex;align-items:center;gap:8px;margin-top:10px;font-size:14px;color:#55606d}
.nota{font-size:14px;color:#55606d;line-height:1.5}
ul.idx{list-style:none;padding:0;margin:0}
ul.idx li a{display:block;background:#fff;border-radius:10px;padding:14px 16px;margin-bottom:10px;color:#1A4A7A;
  text-decoration:none;font-weight:500;box-shadow:0 1px 3px rgba(0,0,0,.08)}
ul.idx li a span{display:block;font-weight:400;font-size:14px;color:#55606d;margin-top:2px}
h3{color:#C76B1A;font-size:13px;letter-spacing:.08em;text-transform:uppercase;margin:22px 0 10px}
"""

JS = """
document.querySelectorAll('.card').forEach(c=>{
  const a=c.querySelector('audio'), bs=c.querySelectorAll('.tempos button'), l=c.querySelector('input');
  bs.forEach(b=>b.onclick=()=>{const play=!a.paused; a.src=b.dataset.src; bs.forEach(x=>x.classList.remove('on'));
    b.classList.add('on'); if(play) a.play();});
  l.onchange=()=>a.loop=l.checked;
});
"""

def page(title, body, back=True):
    nav = '<a href="../">← Todas las pistas</a>' if back else '<a>Manual de preparación de la prueba de acceso · Piano jazz</a>'
    return f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title>
<link rel="stylesheet" href="{'../' if back else ''}estilo.css"></head><body>
<header>{nav}{body[0]}</header><main>{body[1]}</main>
<script src="{'../' if back else ''}pistas.js"></script></body></html>"""

os.makedirs(os.path.join(OUT, "audio"), exist_ok=True)
os.makedirs(os.path.join(OUT, "qr"), exist_ok=True)
open(os.path.join(OUT, "estilo.css"), "w").write(CSS)
open(os.path.join(OUT, "pistas.js"), "w").write(JS)
open(os.path.join(OUT, ".nojekyll"), "w").write("")

def qr(slug):
    url = BASE + (slug + "/" if slug else "")
    for kind, fac in (("svg", qrcode.image.svg.SvgPathImage), ("png", None)):
        q = qrcode.QRCode(border=2, box_size=20, error_correction=qrcode.constants.ERROR_CORRECT_M)
        q.add_data(url); q.make(fit=True)
        img = q.make_image(image_factory=fac) if fac else q.make_image(fill_color="black", back_color="white")
        img.save(os.path.join(OUT, "qr", f"QR_{slug or 'indice'}.{kind}"))

for slug, (title, sub, tracks) in PAGINAS.items():
    cards = ""
    for name, files in tracks:
        files = [(lab, f) for lab, f in files if os.path.exists(os.path.join(MP3, f))]   # solo las pistas que ya existen
        for _, f in files:
            shutil.copy(os.path.join(MP3, f), os.path.join(OUT, "audio", f))
        btns = "".join(f'<button class="{"on" if i == 0 else ""}" data-src="../audio/{f}">{lab}</button>'
                       for i, (lab, f) in enumerate(files))
        cards += (f'<div class="card">' + ("" if name == "Pista" else f'<h2>{name}</h2>') + f'<div class="tempos">{btns}</div>'
                  f'<audio controls preload="none" src="../audio/{files[0][1]}"></audio>'
                  f'<label><input type="checkbox"> Repetir en bucle</label></div>')
    cards += f'<p class="nota">{NOTA[slug]}</p>'
    os.makedirs(os.path.join(OUT, slug), exist_ok=True)
    open(os.path.join(OUT, slug, "index.html"), "w").write(
        page(title, (f"<h1>{title}</h1><p class='sub'>{sub}</p>", cards)))
    qr(slug)

idx = ""
for sec in ("Parrillas de acordes", "Lecturas a primera vista", "Temas"):
    items = "".join(f'<li><a href="{s}/">{t}<span>{sub}</span></a></li>' for s, (t, sub, _) in PAGINAS.items() if SECCION[s] == sec)
    idx += f"<h3>{sec}</h3><ul class='idx'>{items}</ul>"
open(os.path.join(OUT, "index.html"), "w").write(
    page("Pistas de acompañamiento", ("<h1>Pistas de acompañamiento</h1><p class='sub'>Parrillas, lecturas y temas</p>", idx), back=False))
qr("")
print("Web lista en", OUT)
