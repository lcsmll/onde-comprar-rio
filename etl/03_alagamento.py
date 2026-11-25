"""
03 - Alagamento.

Indicadores (maior = pior):
  ismfi    Indice de Suscetibilidade do Meio Fisico a Inundacoes (COPPE/UFRJ 2016, Data.Rio),
           valor do setor ISMFI onde cai o ponto interno de cada setor de 2022;
           media do bairro ponderada pela populacao.
  cor_km2  Ocorrencias de alagamento registradas pelo COR (BigQuery datario), por km2 de
           area ocupada do bairro (area dos setores com moradores).

Saida: data_proc/ind_alagamento.csv + meta_alagamento.json
"""
import geopandas as gpd
import pandas as pd

from arcgis import download_layer
from bq import consultar
from comum import RAW, carregar_bairros, casador_bairros, carregar_setores, config, media_pop, resumo, salvar_indicadores

CAMADA_ISMFI = "Estudos/ISMFI_Indice_de_Suscetibilidade_do_Meio_Fisico_a_Inundacoes/MapServer/0"


def main():
    # --- ISMFI
    arq = RAW / "datario/ismfi_setores.geojson"
    if not arq.exists():
        download_layer(CAMADA_ISMFI, out_fields="cd_geocodi,ismfi_v45").to_file(arq, driver="GeoJSON")
    ismfi = gpd.read_file(arq).to_crs(config.CRS_METROS)[["ismfi_v45", "geometry"]]
    setores = carregar_setores()
    j = gpd.sjoin(setores, ismfi, predicate="within", how="left")
    j = j[~j.index.duplicated()]
    sem = j["ismfi_v45"].isna()
    print(f"Setores 2022 sem ISMFI (fora da cobertura do estudo): {sem.sum()} "
          f"({j.loc[sem, 'pop'].sum():,} moradores)")
    out = pd.DataFrame({"ismfi": media_pop(j, "ismfi_v45")})

    # --- COR (BigQuery)
    pops = ",".join(f"'{p}'" for p in config.COR_POPS_ALAGAMENTO)  # id_pop e texto na tabela
    cor = consultar("cor_alagamento", f"""
        SELECT id_evento, id_pop, data_inicio, latitude, longitude, bairro
        FROM `datario.adm_cor_comando.ocorrencias`
        WHERE id_pop IN ({pops}) AND latitude IS NOT NULL""")
    cor = cor.drop_duplicates("id_evento")
    pts = gpd.GeoDataFrame(cor, geometry=gpd.points_from_xy(cor.longitude, cor.latitude), crs=4326)
    pts = pts.to_crs(config.CRS_METROS)
    b = carregar_bairros()
    jb = gpd.sjoin(pts, b[["codbairro", "geometry"]], predicate="within", how="left")
    jb = jb[~jb.index.duplicated()]
    # coordenada invalida (0,0 ou fora do municipio): usa o nome do bairro do registro
    casar = casador_bairros()
    sem = jb["codbairro"].isna()
    jb.loc[sem, "codbairro"] = jb.loc[sem, "bairro"].map(casar)
    recuperados = int(sem.sum() - jb["codbairro"].isna().sum())
    fora = int(jb["codbairro"].isna().sum())
    nao_reconhecidos = jb.loc[jb["codbairro"].isna(), "bairro"].dropna().value_counts()
    n = jb.groupby("codbairro").size()
    area = b.set_index("codbairro")["area_ocupada_km2"]
    out["cor_n"] = n.reindex(area.index).fillna(0)
    out["cor_km2"] = out["cor_n"] / area.where(area > 0)
    datas = pd.to_datetime(cor["data_inicio"], utc=True)
    meta_extra = {"cor_coord_invalida_recuperada": recuperados, "cor_descartadas": fora}

    meta = {
        "fontes": [
            {"nome": "ISMFI - Índice de Suscetibilidade do Meio Físico a Inundações (COPPE/UFRJ, 2016)",
             "url": "https://pgeo3.rio.rj.gov.br/arcgis/rest/services/" + CAMADA_ISMFI,
             "periodo": "estudo de 2016 (setores do Censo 2010)"},
            {"nome": "COR - Centro de Operações Rio, ocorrências (BigQuery datario.adm_cor_comando.ocorrencias)",
             "url": "https://www.data.rio/",
             "periodo": f"{datas.min():%Y-%m} a {datas.max():%Y-%m}"},
        ],
        "indicadores": {
            "ismfi": {"rotulo": "Suscetibilidade a inundação (ISMFI, 0 a 100)", "peso": config.ALAGAMENTO_PESOS["ismfi"],
                      "unidade": "índice", "maior_e_pior": True},
            "cor_km2": {"rotulo": "Ocorrências de alagamento no COR por km² ocupado",
                        "peso": config.ALAGAMENTO_PESOS["cor_km2"], "unidade": "por km²", "maior_e_pior": True},
        },
        **meta_extra,
        "cor_tipos": "Bolsão d'água em via, Alagamento, Lâmina d'água, Enchente, Alagamentos e enchentes",
        "avisos": ["O ISMFI é um estudo de 2016 e não considera obras de drenagem posteriores.",
                   f"Os registros do COR vão só até {datas.max():%m/%Y} e se concentram em vias de trânsito."],
    }
    salvar_indicadores("alagamento", out, meta)
    print(f"COR: {len(cor):,} ocorrencias ({datas.min():%Y-%m} a {datas.max():%Y-%m})")
    print(f"  coordenada invalida, bairro recuperado pelo nome: {recuperados}; descartadas: {fora}")
    if len(nao_reconhecidos):
        print("  nomes de bairro nao reconhecidos (acrescentar em APELIDOS_BAIRRO?):", nao_reconhecidos.to_dict())
    resumo("Alagamento", out)


if __name__ == "__main__":
    main()
