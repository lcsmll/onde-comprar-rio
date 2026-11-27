"""
12 - Paginas por bairro com previa para WhatsApp/redes (Open Graph).

Para cada bairro exibido gera:
  site/bairro/<slug>/index.html   pagina leve com titulo, descricao e imagem de previa;
                                  quem abre e levado ao bairro dentro do app (#bairro/COD)
  site/bairro/<slug>/previa.png   imagem 1200x630 com a nota (pesos iguais) e as 6 notas
E tambem site/img/previa.png (previa da pagina inicial).

Por que assim: o WhatsApp nao executa JavaScript e nao aceita SVG na previa; ele le as
etiquetas <meta property="og:..."> do HTML e baixa uma imagem PNG/JPG.
A imagem e desenhada em HTML com o visual do app e fotografada pelo Chrome (Playwright).

Rode depois do 99 (precisa de site/data/bairros.json).
"""
import html
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from comum import PROC, SITE_DATA, config

SITE = SITE_DATA.parent
FONTES = SITE / "fonts"
ILUSTRA = SITE / "img" / "ilustracao-rio.svg"

ROTULOS = {"violencia": "Segurança", "alagamento": "Menos alagamento", "escolas": "Escolas",
           "transporte": "Transporte", "emprego": "Emprego", "barulho": "Menos barulho"}
TXT_FORTE = {"violencia": "segurança", "alagamento": "pouco alagamento", "escolas": "escolas",
             "transporte": "transporte", "emprego": "acesso ao emprego", "barulho": "pouco barulho"}
ZONAS = {"zona-norte": "Zona Norte", "zona-oeste": "Zona Oeste", "zona-sul": "Zona Sul", "centro": "Centro"}

fmt = lambda v: f"{v:.1f}".replace(".", ",")
reais = lambda v: "R$ " + f"{v:,.0f}".replace(",", ".")


def juntar(xs):
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " e " + xs[-1]


def cartao_html(titulo, sobretitulo, nota, criterios, rodape,
                legenda_sem_nota="Compare bairros com dados oficiais e simule o financiamento."):
    """HTML 1200x630 da imagem de previa (usa as fontes e a ilustracao do site)."""
    barras = "".join(
        f'<div class="b"><span class="r">{ROTULOS[c]}</span><span class="f"><span style="width:{0 if v is None else v * 10:.0f}%"></span></span>'
        f'<span class="v">{"–" if v is None else fmt(v)}</span></div>' for c, v in criterios)
    anel = ""
    if nota is not None:
        r = 70
        c = 2 * 3.14159 * r
        anel = (f'<div class="anel"><svg viewBox="0 0 170 170"><circle cx="85" cy="85" r="{r}" class="fu"/>'
                f'<circle cx="85" cy="85" r="{r}" class="ch" stroke-dasharray="{c * nota / 10:.1f} {c:.1f}" '
                f'transform="rotate(-90 85 85)"/></svg><span>{fmt(nota)}</span></div>')
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face {{ font-family: Nunito; src: url("{(FONTES / 'Nunito-Variable.woff2').as_uri()}"); font-weight: 200 1000; }}
@font-face {{ font-family: Quicksand; src: url("{(FONTES / 'Quicksand-Variable.woff2').as_uri()}"); font-weight: 300 700; }}
* {{ box-sizing: border-box; margin: 0; }}
body {{ width: 1200px; height: 630px; background: #f6f3ec; font-family: Nunito; color: #18211e; position: relative; overflow: hidden; }}
.ilu {{ position: absolute; left: 0; right: 0; bottom: 0; height: 150px; background: url("{ILUSTRA.as_uri()}") center bottom / auto 150px repeat-x; }}
.marca {{ position: absolute; left: 64px; top: 48px; font: 700 26px Quicksand; color: #0f6b5c; display: flex; gap: 12px; align-items: center; }}
.marca svg {{ width: 34px; height: 34px; fill: #0f6b5c; }}
.esq {{ position: absolute; left: 64px; top: 128px; width: 560px; }}
.sob {{ font: 800 20px Nunito; letter-spacing: .08em; text-transform: uppercase; color: #0f6b5c; display: flex; gap: 10px; align-items: center; }}
.sob:before {{ content: ""; width: 12px; height: 12px; border-radius: 50%; background: #0f6b5c; box-shadow: 0 0 0 5px #e3f1ec; }}
h1 {{ font: 700 82px/1.02 Quicksand; letter-spacing: -.02em; margin: 14px 0 18px; }}
h1.longo {{ font-size: 60px; }}
.leg-inicio {{ width: 520px; font-size: 25px; }}
.linha {{ display: flex; align-items: center; gap: 26px; }}
.anel {{ position: relative; width: 150px; height: 150px; }}
.anel svg {{ width: 150px; height: 150px; }}
.anel circle {{ fill: none; stroke-width: 15; }} .fu {{ stroke: #e6dfd0; }} .ch {{ stroke: #0f6b5c; stroke-linecap: round; }}
.anel span {{ position: absolute; inset: 0; display: grid; place-items: center; font: 700 50px Quicksand; }}
.leg {{ font-size: 22px; color: #545c58; width: 340px; line-height: 1.3; }}
.dir {{ position: absolute; right: 64px; top: 120px; width: 470px; background: #fffdf8; border: 2px solid #e6dfd0;
        border-radius: 28px; padding: 26px 30px; box-shadow: 0 18px 40px -24px rgba(60,45,20,.45); }}
.b {{ display: grid; grid-template-columns: 215px 1fr 50px; align-items: center; gap: 14px; height: 50px; font-size: 22px; white-space: nowrap; }}
.f {{ height: 12px; background: #e6dfd0; border-radius: 99px; overflow: hidden; }}
.f span {{ display: block; height: 100%; background: #0f6b5c; border-radius: 99px; }}
.v {{ text-align: right; font: 700 24px Quicksand; }}
.rod {{ margin-top: 18px; font-size: 21px; color: #545c58; }}
.esq.longo h1 {{ font-size: 56px; }}
.esq.longo .anel, .esq.longo .anel svg {{ width: 118px; height: 118px; }}
.esq.longo .anel span {{ font-size: 40px; }}
</style></head><body>
<div class="marca"><svg viewBox="0 0 24 24"><path d="M3 21V10l9-7 9 7v11h-6v-6H9v6z"/></svg>Onde Comprar no Rio</div>
<div class="esq{' longo' if nota is not None and len(titulo) > 16 else ''}"><p class="sob">{html.escape(sobretitulo)}</p><h1 class="{'longo' if len(titulo) > 24 else ''}">{html.escape(titulo)}</h1>
  {f'<div class="linha">{anel}<p class="leg">Nota de 0 a 10 com os 6 critérios com o mesmo peso</p></div>' if nota is not None else f'<p class="leg leg-inicio">{html.escape(legenda_sem_nota)}</p>'}<p class="rod">{html.escape(rodape)}</p></div>
<div class="dir">{barras}</div>
<div class="ilu"></div>
</body></html>"""


def pagina_html(titulo, descricao, url, imagem, destino, nome):
    e = html.escape
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light only">
  <title>{e(titulo)} · Onde Comprar no Rio</title>
  <meta name="description" content="{e(descricao)}">
  <link rel="canonical" href="{e(url)}">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="Onde Comprar no Rio">
  <meta property="og:locale" content="pt_BR">
  <meta property="og:title" content="{e(titulo)}">
  <meta property="og:description" content="{e(descricao)}">
  <meta property="og:url" content="{e(url)}">
  <meta property="og:image" content="{e(imagem)}">
  <meta property="og:image:type" content="image/jpeg">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="{e(titulo)}">
  <meta name="twitter:card" content="summary_large_image">
  <meta http-equiv="refresh" content="0; url={e(destino)}">
  <style>body{{font-family:system-ui,sans-serif;background:#f6f3ec;color:#18211e;display:grid;place-items:center;min-height:90vh}}a{{color:#0f6b5c}}</style>
</head>
<body>
  <p>Abrindo <a href="{e(destino)}">{e(nome)} no Onde Comprar no Rio</a>...</p>
  <script>location.replace({json.dumps(destino)});</script>
</body>
</html>
"""


def main():
    d = json.loads((SITE_DATA / "bairros.json").read_text(encoding="utf-8"))
    zonas = json.loads((SITE_DATA / "links_portais.json").read_text(encoding="utf-8"))["zona_por_regiao"]
    base = config.SITE_URL.rstrip("/") + "/"
    N = len(d["referencia_codigos"])
    with sync_playwright() as p:
        nav = p.chromium.launch(channel="chrome", headless=True)
        pg = nav.new_page(viewport={"width": 1200, "height": 630})

        tmp = PROC / "_previa.html"   # arquivo local: so assim o Chrome carrega fontes e ilustracao (file://)

        def foto(html_cartao, destino: Path):
            destino.parent.mkdir(parents=True, exist_ok=True)
            tmp.write_text(html_cartao, encoding="utf-8")
            pg.goto(tmp.as_uri(), wait_until="load")
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(150)
            if destino.suffix == ".jpg":
                pg.screenshot(path=str(destino), type="jpeg", quality=86)
            else:
                pg.screenshot(path=str(destino), type="png")

        feitas = []
        for b in d["bairros"]:
            if not b["tem_nota"]:
                continue
            notas = {c: b["criterios"][c]["nota"] for c in d["criterios"]}
            final = None if b.get("sem_nota_final") else sum(notas.values()) / len(notas)
            sem_nota = [ROTULOS[c] for c, v in notas.items() if v is None]
            zona = ZONAS.get(zonas.get(b["regiao"], ""), "Rio de Janeiro")
            fortes = [c for c, v in sorted(((c, v) for c, v in notas.items() if v is not None), key=lambda x: -x[1]) if v >= 6.5][:3]
            desc = (f"{zona}. " + (f"Entre os {N} bairros do Rio, se destaca em {juntar([TXT_FORTE[c] for c in fortes])}. " if fortes else "")
                    + (f"m² médio vendido {reais(b['preco_itbi']['rs_m2'])} (ITBI). " if b.get("preco_itbi") else "")
                    + "Veja os números com fonte oficial, compare e simule o financiamento.")
            titulo = f"{b['nome']}: nota {fmt(final)} de 10" if final is not None else f"{b['nome']}: notas, preço e simulação"
            pasta = SITE / "bairro" / b["slug"]
            url = f"{base}bairro/{b['slug']}/"
            rodape = (f"m² médio vendido {reais(b['preco_itbi']['rs_m2'])} (ITBI) · dados oficiais" if b.get("preco_itbi")
                      else "Dados oficiais")
            img = pasta / "previa.jpg"
            (pasta / "previa.png").unlink(missing_ok=True)          # versao antiga (PNG)
            foto(cartao_html(b["nome"], f"Bairro · {zona}", final, list(notas.items()), rodape,
                             f"Sem nota final: {juntar(sem_nota)} com dados insuficientes. Veja o motivo no app."
                             if sem_nota else ""), img)
            (pasta / "index.html").write_text(
                pagina_html(titulo, desc, url, url + "previa.jpg", f"../../#bairro/{b['codbairro']}", b["nome"]), encoding="utf-8")
            feitas.append((b["nome"], "-" if final is None else fmt(final), img.stat().st_size // 1024))

        # previa da pagina inicial: media das notas dos bairros por criterio nao faz sentido;
        # mostra os criterios com a barra cheia so como ilustracao? Nao: usa o bairro de maior nota como exemplo real.
        topo = max((b for b in d["bairros"] if b["tem_nota"] and not b.get("sem_nota_final")),
                   key=lambda b: sum(b["criterios"][c]["nota"] for c in d["criterios"]))
        foto(cartao_html("Qual bairro do Rio combina com você?", "Dados oficiais · grátis · sem cadastro", None,
                         [(c, topo["criterios"][c]["nota"]) for c in d["criterios"]],
                         f"Exemplo real: {topo['nome']} · notas de 0 a 10 entre {N} bairros do Rio"),
             SITE / "img" / "previa.png")
        nav.close()
    tmp.unlink(missing_ok=True)

    for nome, nota, kb in (feitas if len(feitas) <= 20 else feitas[:5]):
        print(f"  {nome:26} nota {nota}  previa {kb} KB")
    if len(feitas) > 20:
        print(f"  ... ({len(feitas)} no total; tamanho medio {sum(k for *_, k in feitas) / len(feitas):.0f} KB)")
    print(f"Paginas geradas: {len(feitas)} em site/bairro/ | previa da inicial: site/img/previa.png")


if __name__ == "__main__":
    main()
