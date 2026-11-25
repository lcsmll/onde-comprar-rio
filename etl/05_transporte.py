"""
05 - Transporte (Data.Rio): estacoes de metro, trem (so no municipio), BRT e VLT.

Indicadores por setor (ponto interno) -> media do bairro ponderada pela populacao:
  dist_estacao_m  distancia em linha reta ate a estacao mais proxima (menor = melhor)
  estacoes_1km    numero de estacoes a ate TRANSPORTE_RAIO_M (maior = melhor)

Tambem grava data_proc/estacoes.parquet (usado por 06_emprego e 07_barulho).
"""
import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from arcgis import download_layer, layer_info
from comum import PROC, RAW, carregar_setores, config, media_pop, resumo, salvar_indicadores

CAMADAS = {
    "metro": "Transporte_Trafego/Transporte_publico/MapServer/19",
    "trem": "Transporte_Trafego/Transporte_publico/MapServer/16",
    "vlt": "Transporte_Trafego/Transporte_publico/MapServer/9",
    "brt": "Hosted/Estações_BRT/FeatureServer/0",
}
ARQ = {"metro": "metro_estacoes", "trem": "trem_estacoes", "vlt": "vlt_paradas", "brt": "brt_estacoes"}


def carregar(modo):
    arq = RAW / f"datario/{ARQ[modo]}.geojson"
    if not arq.exists():
        download_layer(CAMADAS[modo]).to_file(arq, driver="GeoJSON")
    return gpd.read_file(arq)


def main():
    partes = []
    m = carregar("metro")
    m = m[m["flg_ativa"] == 1]
    partes.append(m.assign(modo="Metrô")[["nome", "modo", "geometry"]])
    t = carregar("trem")
    t = t[t["flg_mun"] == 1]                      # so estacoes dentro do municipio
    partes.append(t.assign(modo="Trem")[["nome", "modo", "geometry"]])
    v = carregar("vlt")
    v = v[v["em_operação"].astype(str) == "1"]
    partes.append(v.assign(modo="VLT")[["nome", "modo", "geometry"]])
    b = carregar("brt").explode(index_parts=False)  # a camada do BRT vem como multiponto
    partes.append(b.assign(modo="BRT")[["nome", "modo", "geometry"]])

    est = pd.concat([p.to_crs(config.CRS_METROS) for p in partes], ignore_index=True)
    est = gpd.GeoDataFrame(est, geometry="geometry", crs=config.CRS_METROS)
    # mesma estacao listada duas vezes (ex.: BRT em dois corredores): junta pontos a < 30 m do mesmo modo
    est["gx"], est["gy"] = (est.geometry.x // 30).astype(int), (est.geometry.y // 30).astype(int)
    antes = len(est)
    est = est.drop_duplicates(["modo", "gx", "gy"]).drop(columns=["gx", "gy"])
    est.to_parquet(PROC / "estacoes.parquet")

    s = carregar_setores()
    xy = np.c_[s.geometry.x, s.geometry.y]
    arvore = cKDTree(np.c_[est.geometry.x, est.geometry.y])
    s["dist_estacao_m"], _ = arvore.query(xy)
    s["estacoes_1km"] = [len(i) for i in arvore.query_ball_point(xy, r=config.TRANSPORTE_RAIO_M)]
    out = pd.DataFrame({k: media_pop(s, k) for k in ("dist_estacao_m", "estacoes_1km")})

    # estacao mais proxima do "centro de populacao" do bairro, para o texto da tela
    _, idx = arvore.query(xy)
    s["mais_proxima"] = (est["nome"].str.strip() + " (" + est["modo"] + ")").to_numpy()[idx]
    out["estacao_mais_comum"] = s.groupby("codbairro").apply(
        lambda g: g.groupby("mais_proxima")["pop"].sum().idxmax())

    meta = {
        "fonte": "Data.Rio / Prefeitura do Rio - camadas de transporte público",
        "url": "https://www.data.rio/",
        "camadas": {k: {"servico": v, "editado_em": layer_info(v).get("_last_edit_iso")} for k, v in CAMADAS.items()},
        "estacoes_por_modo": est["modo"].value_counts().to_dict(),
        "indicadores": {
            "dist_estacao_m": {"rotulo": "Distância média até a estação mais próxima (linha reta)",
                               "peso": config.TRANSPORTE_PESOS["dist_estacao_m"], "unidade": "metros", "maior_e_pior": True},
            "estacoes_1km": {"rotulo": f"Estações a até {config.TRANSPORTE_RAIO_M/1000:g} km",
                             "peso": config.TRANSPORTE_PESOS["estacoes_1km"], "unidade": "estações", "maior_e_pior": False},
        },
        "avisos": ["Distância em linha reta; o caminho a pé real costuma ser maior.",
                   "Considera metrô, trem, BRT e VLT. Ônibus comum não entra."],
    }
    salvar_indicadores("transporte", out, meta)
    print(f"Estacoes: {len(est)} (removidas {antes - len(est)} duplicadas) -> {meta['estacoes_por_modo']}")
    resumo("Transporte", out, casas=0)


if __name__ == "__main__":
    main()
