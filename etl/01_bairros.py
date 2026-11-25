"""
01 - Base territorial: bairros (IPP) e setores censitarios com populacao (Censo 2022).

Saidas (data_proc/):
  bairros.parquet   malha oficial + populacao 2022 + area ocupada
  setores.parquet   setores com populacao, codigo do bairro e ponto interno
  bairros_mvp.json  codigos dos bairros exibidos no site
"""
import json

import geopandas as gpd
import pandas as pd

from arcgis import download_layer, layer_info
from comum import PROC, RAW, cod3, config

CAMADA_BAIRROS = "Cartografia/Limites_administrativos/MapServer/4"
CAMADA_SETORES = "Hosted/Mapa_Rio_Camada_Censo_Demográfico_Setores/FeatureServer/0"


def baixar_se_preciso(caminho, camada, **kw):
    if caminho.exists():
        return gpd.read_file(caminho)
    print(f"Baixando {camada} ...")
    g = download_layer(camada, **kw)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    g.to_file(caminho, driver="GeoJSON")
    return g


def main():
    bairros = baixar_se_preciso(RAW / "datario/bairros.geojson", CAMADA_BAIRROS)
    setores = baixar_se_preciso(RAW / "datario/setores_censo2022.geojson", CAMADA_SETORES,
                                out_fields="cd_setor,bairro,codbairro,total_de_p", page_size=2000)

    # --- setores: populacao e ponto interno, em metros
    s = setores.to_crs(config.CRS_METROS)
    s = s.rename(columns={"total_de_p": "pop"})
    s["codbairro"] = s["codbairro"].map(cod3)
    s["pop"] = s["pop"].fillna(0).astype(int)
    s["area_m2"] = s.geometry.area
    s["ponto"] = s.geometry.representative_point()
    s[["cd_setor", "codbairro", "pop", "area_m2", "geometry", "ponto"]].to_parquet(PROC / "setores.parquet")

    # --- bairros: populacao (soma dos setores) e area ocupada (setores com moradores)
    b = bairros.to_crs(config.CRS_METROS)[["codbairro", "nome", "area_plane", "codra", "rp", "geometry"]]
    b["codbairro"] = b["codbairro"].map(cod3)
    b["nome"] = b["nome"].str.strip()
    b["area_km2"] = b.geometry.area / 1e6
    pop = s.groupby("codbairro")["pop"].sum()
    ocup = s[s["pop"] > 0].groupby("codbairro")["area_m2"].sum() / 1e6
    b["pop2022"] = b["codbairro"].map(pop).fillna(0).astype(int)
    b["area_ocupada_km2"] = b["codbairro"].map(ocup).fillna(0)
    # Populacao oficial por bairro (IPP, agregacao do Censo 2022) -- e a que aparece na tela.
    # A soma dos setores (pop2022) pode diferir um pouco porque alguns setores cruzam a divisa;
    # ela e usada nas taxas, para ficar consistente com os calculos por setor.
    csv = next((RAW / "datario/censo").rglob("População_Residente_2022.csv"))
    of = pd.read_csv(csv, sep=";", encoding="latin1")
    b["pop2022_oficial"] = b["codbairro"].map(dict(zip(of["codbairro"].map(cod3), of["Total de pessoas"])))
    b.to_parquet(PROC / "bairros.parquet")

    # --- bairros do MVP: nome -> codigo (para se algum nao existir)
    por_nome = dict(zip(b["nome"], b["codbairro"]))
    faltando = [n for n in config.BAIRROS_MVP_NOMES if n not in por_nome]
    if faltando:
        raise SystemExit(f"ERRO: bairros nao encontrados na malha oficial: {faltando}")
    mvp = [por_nome[n] for n in config.BAIRROS_MVP_NOMES]
    with open(PROC / "bairros_mvp.json", "w", encoding="utf-8") as f:
        json.dump(mvp, f)

    meta = {"bairros": layer_info(CAMADA_BAIRROS).get("_last_edit_iso"),
            "setores": layer_info(CAMADA_SETORES).get("_last_edit_iso")}
    with open(PROC / "meta_base.json", "w", encoding="utf-8") as f:
        json.dump(meta, f)

    # --- resumo
    print(f"Bairros na malha: {len(b)} | setores: {len(s)} | populacao total: {s['pop'].sum():,}")
    sem_pop = b.loc[b["pop2022"] == 0, "nome"].tolist()
    pequenos = b.loc[(b["pop2022"] > 0) & (b["pop2022"] < config.POP_MINIMA), "nome"].tolist()
    print(f"Sem populacao no Censo 2022: {sem_pop}")
    print(f"Com menos de {config.POP_MINIMA} moradores (sem nota): {pequenos}")
    print(f"Bairros na comparacao: {(b['pop2022'] >= config.POP_MINIMA).sum()}")
    t = b.set_index("codbairro").loc[mvp, ["nome", "pop2022", "pop2022_oficial", "area_km2", "area_ocupada_km2"]]
    print("\nBairros do MVP:")
    print(t.round(2).to_string())


if __name__ == "__main__":
    main()
