"""
02 - Violencia (ISP-RJ).

Regra:
  1. Ultimos N meses publicados pelo ISP (config.VIOLENCIA_MESES).
  2. Populacao de cada CISP = soma dos setores do Censo 2022 cujo ponto interno cai na CISP.
  3. Taxa por 100 mil da CISP. Cada setor herda a taxa da sua CISP.
  4. Taxa do bairro = media dos setores ponderada pela populacao
     (bairro dividido entre delegacias fica com a mistura correta).

Saida: data_proc/ind_violencia.csv + meta_violencia.json
"""
import geopandas as gpd
import pandas as pd
import requests

from comum import RAW, carregar_setores, config, media_pop, resumo, salvar_indicadores

URL_DADOS = "https://www.ispdados.rj.gov.br/Arquivos/BaseDPEvolucaoMensalCisp.csv"
URL_LIMITES = "https://www.ispdados.rj.gov.br/Arquivos/CISPshp.rar"
PASTA = RAW / "isp"


def baixar_dados():
    """Sempre baixa a versao mais nova do CSV mensal (7 MB)."""
    PASTA.mkdir(parents=True, exist_ok=True)
    r = requests.get(URL_DADOS, timeout=180)
    r.raise_for_status()
    (PASTA / "BaseDPEvolucaoMensalCisp.csv").write_bytes(r.content)


def main():
    baixar_dados()
    shp = PASTA / "cisp_shp/CISP.shp"
    if not shp.exists():
        raise SystemExit(f"Falta o shapefile das CISPs. Baixe {URL_LIMITES} e extraia em {shp.parent} "
                         "(ex.: unrar x CISPshp.rar data_raw/isp/cisp_shp/)")

    d = pd.read_csv(PASTA / "BaseDPEvolucaoMensalCisp.csv", sep=";", encoding="latin1")
    d["t"] = d["ano"] * 100 + d["mes"]
    meses = sorted(d["t"].unique())[-config.VIOLENCIA_MESES:]
    d = d[d["t"].isin(meses)]
    provisorios = sorted(d.loc[d["fase"] < 3, "t"].unique())

    soma = pd.DataFrame(index=sorted(d["cisp"].unique()))
    for ind, (cols, _peso, _rot) in config.VIOLENCIA_INDICADORES.items():
        soma[ind] = d.groupby("cisp")[cols].sum().sum(axis=1)

    # populacao por CISP a partir dos setores
    cisp = gpd.read_file(shp).to_crs(config.CRS_METROS)[["CISP", "geometry"]]
    setores = carregar_setores()
    j = gpd.sjoin(setores, cisp, predicate="within", how="left")
    sem_cisp = j.loc[j["CISP"].isna(), "pop"].sum()
    pop_cisp = j.groupby("CISP")["pop"].sum()

    taxas = soma.div(pop_cisp, axis=0) * 1e5          # por 100 mil
    taxas = taxas[pop_cisp.reindex(taxas.index) > 0]

    # cada setor herda a taxa da CISP; bairro = media ponderada pela populacao
    j = j.join(taxas, on="CISP")
    out = pd.DataFrame({ind: media_pop(j, ind) for ind in config.VIOLENCIA_INDICADORES})

    # quais CISPs cobrem cada bairro (para o aviso na tela)
    comp = (j.groupby(["codbairro", "CISP"])["pop"].sum()
              .groupby(level=0).transform(lambda x: x / x.sum()))
    comp = comp[comp >= 0.01].round(3)
    cisps_por_bairro = {b: [{"cisp": int(c), "pct_pop": float(p)} for (_, c), p in g.items()]
                        for b, g in comp.groupby(level=0)}
    out["cisps"] = out.index.map(lambda b: cisps_por_bairro.get(b, []))

    fmt = lambda t: f"{t // 100}-{t % 100:02d}"
    meta = {
        "fonte": "ISP-RJ - Instituto de Segurança Pública (dados abertos por CISP)",
        "url": "https://www.ispdados.rj.gov.br/",
        "arquivo": URL_DADOS,
        "periodo": f"{fmt(meses[0])} a {fmt(meses[-1])}",
        "meses_provisorios": [fmt(t) for t in provisorios],
        "populacao": "Censo 2022 (IBGE), somada por setor censitário dentro de cada CISP",
        "pop_fora_de_cisp": int(sem_cisp),
        "indicadores": {k: {"rotulo": r, "peso": p, "colunas_isp": c, "unidade": "por 100 mil hab.",
                            "maior_e_pior": True}
                        for k, (c, p, r) in config.VIOLENCIA_INDICADORES.items()},
        "avisos": ["O ISP publica por área de delegacia (CISP), não por bairro. Bairros na mesma "
                   "área de delegacia têm números iguais ou parecidos.",
                   "A letalidade violenta pesa 70% por ser o dado mais confiável. Roubos por morador são "
                   "maiores em áreas de comércio e passagem e costumam ser menos registrados onde se denuncia menos."],
    }
    salvar_indicadores("violencia", out, meta)

    print(f"Periodo: {meta['periodo']} | meses provisorios: {meta['meses_provisorios']}")
    print(f"CISPs com dados: {len(taxas)} | populacao sem CISP: {sem_cisp}")
    resumo("Violencia (taxas por 100 mil)", out.drop(columns="cisps"))


if __name__ == "__main__":
    main()
