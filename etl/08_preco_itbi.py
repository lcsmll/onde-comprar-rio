"""
08 - Preco de referencia por bairro (ITBI, Secretaria Municipal de Fazenda, via Data.Rio).

Transacoes residenciais de compra e venda e promessa de compra e venda, por bairro e mes.
Indicador: R$/m2 dos ultimos N meses publicados =
    soma(valor medio do imovel x n. de transacoes) / soma(area media x n. de transacoes)
(razao das medias -- a Prefeitura nao publica mediana nem valor por imovel).
NAO entra na nota: serve de informacao e de filtro de orcamento no site.
"""
import pandas as pd
import requests

from comum import carregar_bairros, cod3, config, resumo, salvar_indicadores

SERVICO = "Fazenda/ITBI/MapServer/5"
URL = f"https://pgeo3.rio.rj.gov.br/arcgis/rest/services/{SERVICO}/query"


def baixar(where: str) -> pd.DataFrame:
    linhas, offset = [], 0
    while True:
        r = requests.get(URL, params={"where": where, "outFields": "*", "returnGeometry": "false",
                                      "f": "json", "resultOffset": offset, "resultRecordCount": 2000},
                         timeout=120).json()
        if "error" in r:
            raise SystemExit(f"Erro na API do ITBI: {r['error']}")
        feats = r.get("features", [])
        linhas += [f["attributes"] for f in feats]
        offset += len(feats)
        if not feats or not r.get("exceededTransferLimit"):
            break
    return pd.DataFrame(linhas)


def main():
    ano_atual = pd.Timestamp.today().year
    d = baixar(f"uso='RESIDENCIAL' AND ano_transação >= {ano_atual - 2}")
    d["t"] = d["ano_transação"] * 100 + d["mês_transação"]
    meses = sorted(d["t"].unique())[-config.ITBI_MESES:]
    d = d[d["t"].isin(meses)].copy()
    d["codbairro"] = d["codbairro"].map(cod3)
    n = d["total_transações"]
    d["valor_x_n"] = d["média_valor_imóvel"] * n
    d["area_x_n"] = d["média_área_construída"] * n
    g = d.groupby("codbairro")[["total_transações", "valor_x_n", "area_x_n"]].sum()
    out = pd.DataFrame({
        "transacoes": g["total_transações"],
        "valor_medio": g["valor_x_n"] / g["total_transações"],
        "area_media_m2": g["area_x_n"] / g["total_transações"],
    })
    out["rs_m2"] = g["valor_x_n"] / g["area_x_n"]
    out = out.reindex(carregar_bairros()["codbairro"])

    fmt = lambda t: f"{t // 100}-{t % 100:02d}"
    meta = {
        "fonte": "Prefeitura do Rio - Secretaria Municipal de Fazenda, ITBI (transações imobiliárias por bairro e mês)",
        "url": "https://www.data.rio/datasets/0965968f12424f8792b240568616e6aa",
        "servico": SERVICO,
        "periodo": f"{fmt(meses[0])} a {fmt(meses[-1])}",
        "naturezas": "compra e venda; promessa de compra e venda (imóveis residenciais)",
        "avisos": ["Mistura casas e apartamentos, novos e usados.",
                   "R$/m² calculado como valor médio dividido pela área média (a Prefeitura não publica a mediana).",
                   "Valor declarado para o ITBI. O último mês não é publicado pela Prefeitura."],
    }
    salvar_indicadores("preco", out, meta)
    print(f"Periodo: {meta['periodo']} | transacoes no periodo: {int(out['transacoes'].sum()):,}")
    print("Bairros sem transacao no periodo:", int(out["transacoes"].isna().sum()))
    resumo("Preco (ITBI)", out, casas=0)


if __name__ == "__main__":
    main()
