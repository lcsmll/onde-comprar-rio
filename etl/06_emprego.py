"""
06 - Emprego: distancia ate os polos de emprego.

Para cada setor (ponto interno), distancia em linha reta ate cada polo; o bairro recebe a
media ponderada pela populacao ("distancia media dos moradores").

Polos fixos (config.POLOS): Centro (est. Carioca), Barra (Terminal Alvorada), Zona Sul (est. Botafogo).
Padrao (quando o usuario nao diz onde trabalha): media Centro x Barra ponderada pela
participacao de cada polo nos vinculos formais da RAIS 2016 por bairro (Data.Rio).

Tambem grava a matriz bairro x bairro (distancia media dos moradores do bairro A ate o
ponto interno do bairro B), usada no site quando o usuario escolhe "outro bairro".
"""
import json

import geopandas as gpd
import numpy as np
import pandas as pd
import requests

from comum import PROC, SITE_DATA, carregar_bairros, carregar_setores, cod3, config, media_pop, resumo, salvar_indicadores

RAIS_URL = "https://services1.arcgis.com/OlP4dGNtIcnD3RYf/arcgis/rest/services/RAIS_open/FeatureServer/2/query"


def ponto_do_polo(est, polo):
    modo = {"metro": "Metrô", "brt": "BRT"}[polo["camada"]]
    do_modo = est[est["modo"] == modo]
    nomes = do_modo["nome"].str.strip().str.lower()
    alvo = polo["nome"].lower()
    c = do_modo[nomes == alvo]                      # nome exato primeiro
    if c.empty:                                     # ex.: "Terminal Alvorada" para "Alvorada"
        c = do_modo[nomes.str.endswith(" " + alvo)]
    if len(c) != 1:
        raise SystemExit(f"Polo ambiguo ou nao encontrado ({len(c)} estacoes): {polo}")
    if c.empty:
        raise SystemExit(f"Polo nao encontrado: {polo}")
    return c.iloc[0]


def vinculos_rais_2016() -> pd.Series:
    linhas, offset = [], 0
    while True:
        r = requests.get(RAIS_URL, params={"where": "1=1", "outFields": "Cod_Bairro,Vinc_2016",
                                           "returnGeometry": "false", "f": "json",
                                           "resultOffset": offset, "resultRecordCount": 2000}, timeout=120).json()
        feats = r.get("features", [])
        linhas += [f["attributes"] for f in feats]
        offset += len(feats)
        if not feats or not r.get("exceededTransferLimit"):
            break
    d = pd.DataFrame(linhas)
    return d.groupby(d["Cod_Bairro"].map(cod3))["Vinc_2016"].sum()


def main():
    est = gpd.read_parquet(PROC / "estacoes.parquet")
    s = carregar_setores()
    xy = np.c_[s.geometry.x, s.geometry.y]
    out = pd.DataFrame()
    polos_info = {}
    for k, p in config.POLOS.items():
        e = ponto_do_polo(est, p)
        s[f"dist_{k}_m"] = np.hypot(xy[:, 0] - e.geometry.x, xy[:, 1] - e.geometry.y)
        out[f"dist_{k}_m"] = media_pop(s, f"dist_{k}_m")
        pt = gpd.GeoSeries([e.geometry], crs=config.CRS_METROS).to_crs(4326).iloc[0]
        polos_info[k] = {"rotulo": p["rotulo"], "estacao": e["nome"].strip(), "lat": round(pt.y, 6), "lon": round(pt.x, 6)}

    # peso padrao Centro x Barra pela RAIS 2016
    b = carregar_bairros()
    vinc = vinculos_rais_2016()
    centro = vinc[vinc.index.isin(b.loc[b["area_plane"].astype(str) == config.POLO_CENTRO_AP, "codbairro"])].sum()
    barra = vinc[vinc.index.isin(b.loc[b["codra"] == config.POLO_BARRA_RA, "codbairro"])].sum()
    w_centro = centro / (centro + barra)
    out["dist_padrao_m"] = w_centro * out["dist_centro_m"] + (1 - w_centro) * out["dist_barra_m"]

    # matriz bairro x bairro (km), origem = moradores do bairro, destino = ponto interno do bairro
    destinos = b.set_index("codbairro").geometry.representative_point()
    matriz = {}
    for cod, pt in destinos.items():
        s["_d"] = np.hypot(xy[:, 0] - pt.x, xy[:, 1] - pt.y)
        matriz[cod] = (media_pop(s, "_d") / 1000).round(2)
    mat = pd.DataFrame(matriz)  # linhas = origem, colunas = destino
    with open(SITE_DATA / "distancias.json", "w", encoding="utf-8") as f:
        json.dump({"unidade": "km", "descricao": "distância média em linha reta dos moradores do bairro "
                   "de origem (linha) até o ponto interno do bairro de destino (coluna)",
                   "origens": list(mat.index), "destinos": list(mat.columns),
                   "km": [[None if pd.isna(v) else float(v) for v in row] for row in mat.to_numpy()]},
                  f, separators=(",", ":"))

    meta = {
        "fontes": [{"nome": "Distâncias calculadas a partir da malha de bairros, setores do Censo 2022 e estações (Data.Rio)"},
                   {"nome": "RAIS 2016 por bairro (Data.Rio) - só para o peso padrão Centro x Barra",
                    "url": "https://www.data.rio/datasets/cc9673bd14694b8f9330756f387b899b"}],
        "polos": polos_info,
        "peso_padrao": {"centro": round(w_centro, 3), "barra": round(1 - w_centro, 3),
                        "vinculos_rais_2016": {"centro_ap1": int(centro), "barra_ra24": int(barra)}},
        "indicadores": {"dist_padrao_m": {"rotulo": "Distância média até os polos de emprego (Centro e Barra)",
                                          "unidade": "metros", "maior_e_pior": True, "peso": 1.0}},
        "avisos": ["Distância em linha reta, não tempo de viagem.",
                   f"Sem informar onde trabalha, a distância é {w_centro:.0%} Centro e {1 - w_centro:.0%} Barra, "
                   "conforme a participação de cada polo nos empregos formais (RAIS 2016)."],
    }
    salvar_indicadores("emprego", out, meta)
    print("Polos:", {k: v["estacao"] for k, v in polos_info.items()})
    print(f"Peso padrao (RAIS 2016): Centro {w_centro:.1%} ({centro:,} vinculos AP1) x Barra {1 - w_centro:.1%} "
          f"({barra:,} vinculos RA XXIV)")
    print(f"Matriz de distancias: {mat.shape[0]} x {mat.shape[1]} -> site/data/distancias.json")
    resumo("Emprego (distancia media dos moradores, km)", out / 1000, casas=1)


if __name__ == "__main__":
    main()
