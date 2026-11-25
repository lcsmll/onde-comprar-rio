"""
11 - Mapa dos bairros em SVG -> site/data/mapa.json

Por que SVG e nao Leaflet com mapa de fundo: o fundo de ruas viria de servidores externos
(cada visitante enviaria o IP para eles). Aqui o desenho e gerado a partir da malha oficial
de bairros e fica todo dentro do site.

- Contornos simplificados sem abrir buracos entre vizinhos (shapely.coverage_simplify).
- Coordenadas em metros (SIRGAS 2000 / UTM 23S) convertidas para "unidades de tela"
  (1 unidade = ESCALA metros), com o eixo Y invertido (no SVG, Y cresce para baixo).
- O site pinta os bairros exibidos pela nota; os demais aparecem em cinza, como contexto.
"""
import json

import shapely
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import polylabel

from comum import SITE_DATA, carregar_bairros, codigos_mvp, config

TOLERANCIA_M = 40   # quanto simplificar os contornos (metros)
ESCALA = 20         # metros por unidade do SVG
MARGEM_M = 1500     # folga em volta dos bairros exibidos no enquadramento inicial


def caminho(geom, minx, maxy) -> str:
    """Poligono -> atributo 'd' do SVG (M x y L ... Z), com coordenadas inteiras."""
    partes = []
    polys = geom.geoms if isinstance(geom, MultiPolygon) else [geom]
    for p in polys:
        for anel in [p.exterior, *p.interiors]:
            pts = [(round((x - minx) / ESCALA), round((maxy - y) / ESCALA)) for x, y in anel.coords]
            # remove pontos repetidos depois do arredondamento
            limpos = [pts[0]] + [q for a, q in zip(pts, pts[1:]) if q != a]
            if len(limpos) >= 4:
                partes.append("M" + "L".join(f"{x} {y}" for x, y in limpos[:-1]) + "Z")
    return "".join(partes)


def main():
    b = carregar_bairros()
    geoms = shapely.coverage_simplify(b.geometry.to_numpy(), TOLERANCIA_M)
    b = b.set_geometry(list(geoms), crs=config.CRS_METROS)
    minx, miny, maxx, maxy = b.total_bounds
    mvp = codigos_mvp() if not config.EXIBIR_TODOS else list(b["codbairro"])
    ex = b[b["codbairro"].isin(mvp)].total_bounds
    vb = [round((ex[0] - MARGEM_M - minx) / ESCALA), round((maxy - ex[3] - MARGEM_M) / ESCALA),
          round((ex[2] - ex[0] + 2 * MARGEM_M) / ESCALA), round((ex[3] - ex[1] + 2 * MARGEM_M) / ESCALA)]

    if config.EXIBIR_TODOS:   # cidade inteira exibida: o enquadramento inicial e a propria cidade
        vb = [0, 0, round((maxx - minx) / ESCALA), round((maxy - miny) / ESCALA)]

    bairros = {}
    for _, r in b.iterrows():
        # rotulo no ponto mais "interno" do maior pedaco do bairro (longe das divisas)
        g = max(r.geometry.geoms, key=lambda x: x.area) if isinstance(r.geometry, MultiPolygon) else r.geometry
        pt = polylabel(g, tolerance=10)
        bairros[r["codbairro"]] = {
            "nome": r["nome"], "d": caminho(r.geometry, minx, maxy),
            "rotulo": [round((pt.x - minx) / ESCALA), round((maxy - pt.y) / ESCALA)],
        }
    # rotulos de bairros exibidos muito proximos: afasta verticalmente (ate 3 rodadas)
    cods = [c for c in mvp if c in bairros]
    for _ in range(3):
        for i, a in enumerate(cods):
            for c in cods[i + 1:]:
                ra, rc = bairros[a]["rotulo"], bairros[c]["rotulo"]
                if abs(ra[0] - rc[0]) < 90 and abs(ra[1] - rc[1]) < 26:
                    desce = c if ra[1] <= rc[1] else a
                    bairros[desce]["rotulo"][1] += 26

    saida = {
        "fonte": "Limite de Bairros (Instituto Pereira Passos / Data.Rio), contornos simplificados em "
                 f"{TOLERANCIA_M} m para desenho",
        "escala_m_por_unidade": ESCALA,
        "viewbox_cidade": [0, 0, round((maxx - minx) / ESCALA), round((maxy - miny) / ESCALA)],
        "viewbox_inicial": vb,
        "bairros": bairros,
    }
    arq = SITE_DATA / "mapa.json"
    arq.write_text(json.dumps(saida, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    pontos = sum(d["d"].count("L") + d["d"].count("M") for d in bairros.values())
    print(f"Bairros desenhados: {len(bairros)} | pontos: {pontos:,} | arquivo: {arq.stat().st_size / 1024:.0f} KB")
    print(f"Enquadramento inicial (bairros exibidos + {MARGEM_M} m): {vb} | cidade: {saida['viewbox_cidade']}")


if __name__ == "__main__":
    main()
