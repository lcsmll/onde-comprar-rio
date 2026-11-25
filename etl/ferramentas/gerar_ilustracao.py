"""
Gera site/img/ilustracao-rio.svg: faixa decorativa em tons pastel (morros, Pao de Acucar,
casinhas e arvores). Desenho proprio, sem imagem de terceiros. Rodar uma vez:
    .venv/bin/python etl/ferramentas/gerar_ilustracao.py
"""
import random
from pathlib import Path

random.seed(7)
L, A = 1200, 230
p = []
# morros do fundo (curvas suaves) e Pao de Acucar a direita
p.append(f'<path fill="#d9e9dc" d="M0 150 C120 95 210 110 300 128 C380 80 470 70 560 118 C640 92 720 96 800 132 '
         f'C860 70 905 40 940 55 C975 70 990 120 1010 128 C1040 96 1075 70 1110 78 C1150 88 1180 120 {L} 125 V{A} H0Z"/>')
p.append(f'<path fill="#c4dfcb" d="M0 175 C90 140 170 150 250 165 C330 135 420 132 500 158 C580 138 660 140 740 162 '
         f'C820 140 900 142 980 160 C1060 142 1140 146 {L} 158 V{A} H0Z"/>')
# casinhas
casas = []
x = 10
while x < L - 30:
    w = random.randint(26, 46); h = random.randint(22, 40); base = 200 + random.randint(-6, 6)
    parede = random.choice(["#f6ead6", "#f3e2c7", "#efe6d8", "#f8efe2"])
    telhado = random.choice(["#e8a07e", "#de8f6d", "#eeb08f", "#d98a6a"])
    casas.append(f'<rect x="{x}" y="{base - h}" width="{w}" height="{h}" rx="2" fill="{parede}"/>'
                 f'<path d="M{x - 3} {base - h} L{x + w / 2} {base - h - 14} L{x + w + 3} {base - h}Z" fill="{telhado}"/>'
                 f'<rect x="{x + w / 2 - 4}" y="{base - 11}" width="8" height="11" rx="1" fill="#c9b59a"/>')
    if random.random() < .55:  # arvore entre as casas
        tx = x + w + random.randint(4, 10); r = random.randint(9, 15)
        casas.append(f'<rect x="{tx - 1.5}" y="{base - r - 4}" width="3" height="{r + 4}" fill="#9c8467"/>'
                     f'<circle cx="{tx}" cy="{base - r - 6}" r="{r}" fill="{random.choice(["#8fc3a2", "#7fb895", "#a3cfb1"])}"/>')
        x = tx + r + random.randint(4, 12)
    else:
        x += w + random.randint(6, 16)
p.extend(casas)
p.append(f'<rect x="0" y="198" width="{L}" height="{A - 198}" fill="#e9e1d1"/>')
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {L} {A}" preserveAspectRatio="xMidYMax slice">'
       + "".join(p) + "</svg>")
out = Path(__file__).resolve().parents[2] / "site" / "img" / "ilustracao-rio.svg"
out.parent.mkdir(exist_ok=True)
out.write_text(svg, encoding="utf-8")
print(f"Gravado {out} ({out.stat().st_size / 1024:.1f} KB)")
