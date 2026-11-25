"""
04 - Escolas (INEP).

Entradas:
  data_raw/inep/catalogo/catalogo_escolas_rio_*.csv  (exportado do Catalogo de Escolas - ver README)
  data_raw/inep/divulgacao_*_escolas_<IDEB_ANO>.zip    (Ideb por escola; ver etl/ferramentas/baixar_dados.sh)

Escolas consideradas: "em funcionamento e sem restricao de atendimento" que oferecem
Educacao Infantil, Ensino Fundamental ou Ensino Medio.

Indicadores por setor (ponto interno), depois media do bairro ponderada pela populacao:
  oferta_publica  n. de escolas publicas a ate ESCOLA_RAIO_OFERTA_M
  oferta_privada  n. de escolas particulares a ate ESCOLA_RAIO_OFERTA_M
  ideb_publica    media do Ideb (config.IDEB_ANO) das escolas publicas a ate ESCOLA_RAIO_IDEB_M
Escolas sem coordenada: localizadas pelo bairro escrito no endereco; contam para
todos os moradores daquele bairro (entram na oferta, nao no IDEB).
"""
import zipfile

import geopandas as gpd
import numpy as np
import openpyxl
import pandas as pd
from scipy.spatial import cKDTree

from comum import PROC, RAW, carregar_bairros, carregar_setores, casador_bairros, config, media_pop, resumo, salvar_indicadores

PASTA = RAW / "inep"
ETAPAS = ("Educação Infantil", "Ensino Fundamental", "Ensino Médio")
A = config.IDEB_ANO  # edicao do Ideb usada (config.py)


def ler_ideb() -> pd.DataFrame:
    """IDEB das escolas do municipio do Rio (cache em data_proc, a leitura do xlsx demora)."""
    cache = PROC / f"ideb_rio_{A}.csv"
    if cache.exists():
        return pd.read_csv(cache)
    linhas = []
    for etapa in ["anos_iniciais", "anos_finais", "ensino_medio"]:
        nome = f"divulgacao_{etapa}_escolas_{A}.xlsx"
        arq = PASTA / "ext" / nome
        if not arq.exists():
            with zipfile.ZipFile(PASTA / f"divulgacao_{etapa}_escolas_{A}.zip") as z:
                membro = next(m for m in z.namelist() if m.endswith(".xlsx"))
                arq.parent.mkdir(parents=True, exist_ok=True)
                arq.write_bytes(z.read(membro))
        ws = openpyxl.load_workbook(arq, read_only=True).worksheets[0]
        cab = None
        for row in ws.iter_rows(values_only=True):
            if cab is None:
                if row and row[0] == "SG_UF":
                    cab = list(row)
                    i_mun, i_id, i_rede, i_ideb = (cab.index(c) for c in
                                                   ("CO_MUNICIPIO", "ID_ESCOLA", "REDE", f"VL_OBSERVADO_{A}"))
                continue
            if str(row[i_mun]) == "3304557":
                linhas.append({"cod": int(row[i_id]), "rede": row[i_rede], "etapa": etapa,
                               "ideb": pd.to_numeric(str(row[i_ideb]).replace(",", "."), errors="coerce")})
        print(f"  IDEB {etapa}: lido")
    d = pd.DataFrame(linhas)
    d.to_csv(cache, index=False)
    return d


def main():
    arqs = sorted((PASTA / "catalogo").glob("catalogo_escolas_rio_*.csv"))
    if not arqs:
        raise SystemExit("Falta o CSV do Catalogo de Escolas em data_raw/inep/catalogo/ (ver README).")
    arq = arqs[-1]
    c = pd.read_csv(arq, encoding="utf-8-sig", dtype=str)
    total = len(c)
    c = c[c["Restrição de Atendimento"].str.contains("FUNCIONAMENTO E SEM RESTRI", na=False)]
    etapas = c["Etapas e Modalidade de Ensino Oferecidas"].fillna("")
    c = c[etapas.apply(lambda s: any(e in s for e in ETAPAS))].copy()
    c["cod"] = c["Código INEP"].astype(int)
    c["publica"] = c["Dependência Administrativa"].isin(["Municipal", "Estadual", "Federal"])
    for k in ("Latitude", "Longitude"):
        c[k] = pd.to_numeric(c[k].str.strip(), errors="coerce")

    # --- localizacao: coordenada; se faltar, bairro escrito no endereco ("... BAIRRO. CEP Rio de Janeiro - RJ.")
    com = c[c["Latitude"].notna()].copy()
    g = gpd.GeoDataFrame(com, geometry=gpd.points_from_xy(com.Longitude, com.Latitude), crs=4326)
    g = g.to_crs(config.CRS_METROS)
    b = carregar_bairros()
    g = gpd.sjoin(g, b[["codbairro", "geometry"]], predicate="within", how="left")
    g = g[~g.index.duplicated()]
    casar = casador_bairros()
    sem = c[c["Latitude"].isna()].copy()
    partes = sem["Endereço"].str.extract(r"^(?P<trecho>.*?)\.\s*(?P<cep>\d{5}-?\d{3})\s+Rio de Janeiro")
    sem["codbairro"] = [casar(t, termina_com=True, cep=cep) for t, cep in zip(partes["trecho"], partes["cep"])]
    nao_loc = sem[sem["codbairro"].isna()]

    # --- IDEB: media das etapas que a escola tem
    ideb = ler_ideb().dropna(subset=["ideb"]).groupby("cod")["ideb"].mean()
    g["ideb"] = g["cod"].map(ideb)

    # --- contagens por raio a partir do ponto interno de cada setor
    s = carregar_setores()
    xy_s = np.c_[s.geometry.x, s.geometry.y]
    out_setor = pd.DataFrame(index=s.index)
    for rotulo, mask in (("oferta_publica", g["publica"]), ("oferta_privada", ~g["publica"])):
        pts = g[mask]
        arvore = cKDTree(np.c_[pts.geometry.x, pts.geometry.y])
        out_setor[rotulo] = [len(v) for v in arvore.query_ball_point(xy_s, r=config.ESCOLA_RAIO_OFERTA_M)]
        # escolas sem coordenada: somam para todos os setores do bairro delas
        extra = sem[(sem["publica"] == (rotulo == "oferta_publica")) & sem["codbairro"].notna()]
        out_setor[rotulo] += s["codbairro"].map(extra.groupby("codbairro").size()).fillna(0).values

    pub = g[g["publica"] & g["ideb"].notna()]
    arvore = cKDTree(np.c_[pub.geometry.x, pub.geometry.y])
    vals = pub["ideb"].to_numpy()
    out_setor["ideb_publica"] = [vals[v].mean() if v else np.nan
                                 for v in arvore.query_ball_point(xy_s, r=config.ESCOLA_RAIO_IDEB_M)]
    s = s.join(out_setor)
    out = pd.DataFrame({k: media_pop(s, k) for k in ("oferta_publica", "oferta_privada", "ideb_publica")})

    # contagens dentro do bairro (para mostrar na tela)
    todas = pd.concat([g[["codbairro", "publica"]], sem[["codbairro", "publica"]]])
    out["n_publicas_no_bairro"] = todas[todas.publica].groupby("codbairro").size()
    out["n_privadas_no_bairro"] = todas[~todas.publica].groupby("codbairro").size()
    out["n_com_ideb_no_bairro"] = g[g["ideb"].notna()].groupby("codbairro").size()
    out[["n_publicas_no_bairro", "n_privadas_no_bairro", "n_com_ideb_no_bairro"]] = \
        out[["n_publicas_no_bairro", "n_privadas_no_bairro", "n_com_ideb_no_bairro"]].fillna(0).astype(int)

    meta = {
        "fontes": [
            {"nome": "INEP - Catálogo de Escolas (Censo Escolar)", "arquivo": arq.name,
             "url": "https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/inep-data/catalogo-de-escolas"},
            {"nome": f"INEP - Ideb {A} por escola", "periodo": f"Ideb {A}",
             "url": "https://www.gov.br/inep/pt-br/areas-de-atuacao/pesquisas-estatisticas-e-indicadores/ideb/resultados"},
        ],
        "escolas_consideradas": int(len(c)), "linhas_no_arquivo": total,
        "localizadas_por_coordenada": int(len(g)), "localizadas_pelo_endereco": int(sem["codbairro"].notna().sum()),
        "nao_localizadas": int(len(nao_loc)),
        "indicadores": {
            "oferta_publica": {"rotulo": f"Escolas públicas a até {config.ESCOLA_RAIO_OFERTA_M/1000:g} km",
                               "unidade": "escolas", "maior_e_pior": False},
            "ideb_publica": {"rotulo": f"Ideb {A} médio das escolas públicas a até {config.ESCOLA_RAIO_IDEB_M/1000:g} km",
                             "unidade": "Ideb (0 a 10)", "maior_e_pior": False},
            "oferta_privada": {"rotulo": f"Escolas particulares a até {config.ESCOLA_RAIO_OFERTA_M/1000:g} km",
                               "unidade": "escolas", "maior_e_pior": False},
        },
        "pesos_por_tipo": config.ESCOLAS_PESOS,
        "avisos": ["Não existe indicador oficial de qualidade para escolas particulares: elas entram só pela quantidade.",
                   "Escolas sem coordenada no catálogo foram localizadas pelo bairro escrito no endereço."],
    }
    salvar_indicadores("escolas", out, meta)
    print(f"Escolas consideradas: {len(c)} de {total} | por coordenada: {len(g)} | pelo endereco: "
          f"{sem['codbairro'].notna().sum()} | nao localizadas: {len(nao_loc)}")
    if len(nao_loc):
        print("Enderecos nao localizados (acrescentar apelido?):")
        print(nao_loc["Endereço"].head(15).to_string())
    print(f"Escolas publicas com Ideb {A}: {g['ideb'].notna().sum()}")
    resumo("Escolas", out)


if __name__ == "__main__":
    main()
