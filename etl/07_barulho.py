"""
07 - Barulho (indice composto; NAO e medicao de decibeis).

Indicadores (maior = pior):
  chamados_1746_1000hab  chamados ao 1746 de perturbacao do sossego / carro de som / poluicao
                         sonora (categorias Servico e Reclamacao), ultimos N meses completos,
                         por 1.000 habitantes. Local: coordenada do chamado; sem coordenada, id_bairro.
  pct_via_pesada         % dos moradores a ate X m de via Estrutural ou Arterial (primaria ou secundaria)
  pct_trilho_brt         % dos moradores a ate X m de linha de trem, metro de superficie (Linha 2) ou BRT
  pct_aeroporto          % dos moradores dentro de faixa de ruido >= 65 dB dos PEZR dos aeroportos

"% dos moradores a ate X m": em cada setor, a populacao exposta e proporcional a fracao da area
do setor dentro da faixa.
"""
from datetime import date

import geopandas as gpd
import pandas as pd

from arcgis import download_layer, layer_info
from bq import consultar
from comum import RAW, carregar_bairros, carregar_setores, config, resumo, salvar_indicadores

CAM = {
    "vias": "CadLog/Trechos_Logradouros/MapServer/0",
    "trem": "Transporte_Trafego/Transporte_publico/MapServer/15",
    "metro": "Transporte_Trafego/Transporte_publico/MapServer/18",
    "brt": "Hosted/Trajetos_BRT/FeatureServer/1",
    "pezr": "Urbanismo/IU_PEZRs/MapServer/301",
}


def camada(nome, arq, **kw):
    p = RAW / f"datario/{arq}.geojson"
    if not p.exists():
        print(f"Baixando {CAM[nome]} ...")
        download_layer(CAM[nome], **kw).to_file(p, driver="GeoJSON")
    return gpd.read_file(p).to_crs(config.CRS_METROS)


def pct_exposto(setores_poli, faixa) -> pd.Series:
    """% da populacao do bairro dentro da faixa (por fracao de area de cada setor)."""
    uniao = faixa.union_all()
    s = setores_poli[setores_poli["pop"] > 0].copy()
    frac = s.geometry.intersection(uniao).area / s.geometry.area
    exp = (s["pop"] * frac).groupby(s["codbairro"]).sum()
    return 100 * exp / s.groupby("codbairro")["pop"].sum()


def ultimos_meses(n):
    hoje = date.today()
    fim = date(hoje.year, hoje.month, 1)                      # 1o dia do mes atual (exclusivo)
    ini_m = (fim.year * 12 + fim.month - 1) - n
    ini = date(ini_m // 12, ini_m % 12 + 1, 1)
    return ini, fim


def main():
    b = carregar_bairros()
    setores = carregar_setores(pontos=False)
    out = pd.DataFrame(index=b["codbairro"])

    # --- 1746
    ini, fim = ultimos_meses(config.BARULHO_1746_MESES)
    f = config.BARULHO_1746_FILTRO
    lst = lambda xs: ",".join("'" + x.replace("'", "\\'") + "'" for x in xs)
    ch = consultar(f"1746_barulho_{ini:%Y%m}_{fim:%Y%m}", f"""
        SELECT c.id_chamado, c.data_inicio, c.latitude, c.longitude, c.id_bairro, b.nome AS bairro_nome
        FROM `datario.adm_central_atendimento_1746.chamado` c
        LEFT JOIN `datario.dados_mestres.bairro` b ON CAST(c.id_bairro AS STRING) = CAST(b.id_bairro AS STRING)
        WHERE c.data_particao >= '{ini}' AND c.data_inicio >= '{ini}' AND c.data_inicio < '{fim}'
          AND c.tipo IN ({lst(f['tipos'])}) AND c.subtipo IN ({lst(f['subtipos'])})
          AND c.categoria IN ({lst(f['categorias'])})""")
    ch = ch.drop_duplicates("id_chamado")
    com = ch[ch["latitude"].notna() & (ch["latitude"] != 0)]
    pts = gpd.GeoDataFrame(com, geometry=gpd.points_from_xy(com.longitude, com.latitude), crs=4326).to_crs(config.CRS_METROS)
    j = gpd.sjoin(pts, b[["codbairro", "geometry"]], predicate="within", how="left")
    j = j[~j.index.duplicated()]
    # sem coordenada (ou coordenada fora): usa o nome do bairro do cadastro do 1746
    from comum import casador_bairros
    casar = casador_bairros()
    resto = pd.concat([ch[~ch.index.isin(com.index)], ch.loc[j.index[j["codbairro"].isna()]]])
    resto = resto.assign(codbairro=resto["bairro_nome"].map(casar))
    loc = pd.concat([j.loc[j["codbairro"].notna(), "codbairro"], resto["codbairro"].dropna()])
    n = loc.value_counts()
    out["chamados_1746_n"] = n.reindex(out.index).fillna(0)
    pop = b.set_index("codbairro")["pop2022"]
    out["chamados_1746_1000hab"] = 1000 * out["chamados_1746_n"] / pop.where(pop > 0)
    descartados = int(len(ch) - len(loc))

    # --- vias pesadas
    vias_lst = lst(config.BARULHO_VIAS_PESADAS)
    vias = camada("vias", "vias_pesadas", where=f"hierarquia IN ({vias_lst})", out_fields="hierarquia,completo")
    out["pct_via_pesada"] = pct_exposto(setores, vias.buffer(config.BARULHO_VIA_BUFFER_M))

    # --- trilhos e BRT
    trem = camada("trem", "trem_linhas")
    metro = camada("metro", "metro_linhas")
    metro_sup = metro[metro["tipo"].astype(str).str.contains("2")]   # Linha 2 (superficie)
    brt = camada("brt", "brt_trajetos")
    linhas = pd.concat([trem.geometry, metro_sup.geometry, brt.geometry])
    out["pct_trilho_brt"] = pct_exposto(setores, linhas.buffer(config.BARULHO_TRILHO_BUFFER_M))

    # --- aeroportos (PEZR)
    pezr = camada("pezr", "pezr")
    pezr = pezr[pezr["ruido_minimo"] >= config.BARULHO_PEZR_MIN_DB]
    out["pct_aeroporto"] = pct_exposto(setores, pezr.geometry)
    out = out.fillna({"pct_via_pesada": 0, "pct_trilho_brt": 0, "pct_aeroporto": 0})
    out.loc[pop.reindex(out.index) == 0, ["pct_via_pesada", "pct_trilho_brt", "pct_aeroporto"]] = None

    meta = {
        "fontes": [
            {"nome": "Central 1746 - chamados (BigQuery datario.adm_central_atendimento_1746.chamado)",
             "url": "https://www.data.rio/", "periodo": f"{ini:%Y-%m} a {(pd.Timestamp(fim) - pd.Timedelta(days=1)):%Y-%m}"},
            {"nome": "Logradouros com hierarquia viária (Data.Rio)", "servico": CAM["vias"]},
            {"nome": "Linhas de trem e metrô, trajetos do BRT (Data.Rio)", "servico": [CAM["trem"], CAM["metro"], CAM["brt"]]},
            {"nome": "Planos Específicos de Zoneamento de Ruído dos aeroportos (PEZR, Prefeitura)", "servico": CAM["pezr"],
             "editado_em": layer_info(CAM["pezr"]).get("_last_edit_iso")},
        ],
        "chamados_total": int(len(ch)), "chamados_sem_local": descartados,
        "filtro_1746": f,
        "indicadores": {
            "chamados_1746_1000hab": {"rotulo": "Chamados ao 1746 por barulho, por mil habitantes",
                                      "peso": config.BARULHO_PESOS["chamados_1746_1000hab"], "unidade": "por mil hab.", "maior_e_pior": True},
            "pct_via_pesada": {"rotulo": f"Moradores a até {config.BARULHO_VIA_BUFFER_M} m de via estrutural ou arterial (primária ou secundária)",
                               "peso": config.BARULHO_PESOS["pct_via_pesada"], "unidade": "%", "maior_e_pior": True},
            "pct_trilho_brt": {"rotulo": f"Moradores a até {config.BARULHO_TRILHO_BUFFER_M} m de trem, metrô de superfície ou BRT",
                               "peso": config.BARULHO_PESOS["pct_trilho_brt"], "unidade": "%", "maior_e_pior": True},
            "pct_aeroporto": {"rotulo": f"Moradores em zona de ruído de aeroporto ({config.BARULHO_PEZR_MIN_DB} dB ou mais)",
                              "peso": config.BARULHO_PESOS["pct_aeroporto"], "unidade": "%", "maior_e_pior": True},
        },
        "ruido_db_oficial": None,
        "avisos": ["Índice composto, não é medição de decibéis. O Rio ainda não publicou o mapa de ruído da Lei 7.479/2022.",
                   "O número de chamados mede reclamações, que também dependem do hábito de reclamar no bairro.",
                   "Metrô de superfície: considerada a Linha 2 inteira (as Linhas 1 e 4 são subterrâneas)."],
    }
    salvar_indicadores("barulho", out, meta)
    print(f"1746: {len(ch):,} chamados ({meta['fontes'][0]['periodo']}); sem local identificado: {descartados}")
    print(f"Vias pesadas: {len(vias):,} trechos | PEZR >= {config.BARULHO_PEZR_MIN_DB} dB: {len(pezr)} poligonos")
    resumo("Barulho", out)


if __name__ == "__main__":
    main()
