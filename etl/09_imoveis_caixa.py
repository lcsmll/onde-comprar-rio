"""
09 - Imoveis a venda da Caixa (lista oficial de imoveis retomados: venda direta e leilao).

Entrada: data_raw/caixa/Lista_imoveis_RJ.csv -- baixado MANUALMENTE no navegador
(o site da Caixa tem CAPTCHA; ver README). Se o arquivo nao existir, grava lista vazia.

Saida: site/data/imoveis_caixa.json
"""
import json
import re
from datetime import date, datetime

import pandas as pd

from comum import RAW, SITE_DATA, carregar_bairros, casador_bairros, codigos_mvp

ARQ = RAW / "caixa" / "Lista_imoveis_RJ.csv"


def num_br(x):
    """'1.234.567,89' -> 1234567.89"""
    if pd.isna(x):
        return None
    s = re.sub(r"[^\d,.-]", "", str(x)).replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def ler_lista() -> pd.DataFrame:
    bruto = ARQ.read_bytes()
    texto = None
    for enc in ("utf-8-sig", "latin1"):
        try:
            texto = bruto.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    linhas = texto.splitlines()
    # o arquivo comeca com linhas de titulo; o cabecalho e a linha que tem "Bairro" e "Pre"
    i = next(i for i, l in enumerate(linhas) if "Bairro" in l and "Pre" in l)
    sep = ";" if linhas[i].count(";") >= linhas[i].count(",") else ","
    from io import StringIO
    d = pd.read_csv(StringIO("\n".join(linhas[i:])), sep=sep, dtype=str)
    d.columns = [c.strip() for c in d.columns]
    return d


def col(d, *palavras):
    for c in d.columns:
        cn = c.lower()
        if all(p in cn for p in palavras):
            return c
    return None


def main():
    saida = {"gerado_em": date.today().isoformat(), "fonte": "Caixa Econômica Federal - Venda de Imóveis",
             "url": "https://venda-imoveis.caixa.gov.br/", "data_lista": None, "imoveis": []}
    if not ARQ.exists():
        print(f"AVISO: {ARQ} nao encontrado -- gravando lista vazia. Baixe a lista do RJ no site da Caixa (ver README).")
        (SITE_DATA / "imoveis_caixa.json").write_text(json.dumps(saida, ensure_ascii=False), encoding="utf-8")
        return

    d = ler_lista()
    c_cid, c_bai, c_end = col(d, "cidade"), col(d, "bairro"), col(d, "endere")
    c_preco, c_aval, c_desc = col(d, "pre"), col(d, "avalia"), col(d, "desconto")
    c_descr, c_mod, c_link, c_num = col(d, "descri"), col(d, "modalidade"), col(d, "link"), col(d, "imóvel") or col(d, "imovel")
    print("Colunas encontradas:", list(d.columns))
    d = d[d[c_cid].str.strip().str.upper().str.replace("Ã", "A") == "RIO DE JANEIRO"].copy()

    casar = casador_bairros()
    d["codbairro"] = d[c_bai].map(casar)
    descr = d[c_descr].fillna("") if c_descr else pd.Series("", index=d.index)
    d["tipo"] = descr.str.extract(r"^\s*([A-Za-zÀ-ú ]+?)\s*,", expand=False).str.strip()
    area_priv = descr.str.extract(r"([\d.,]+)\s*de [áa]rea privativa", expand=False).map(num_br)
    area_tot = descr.str.extract(r"([\d.,]+)\s*de [áa]rea total", expand=False).map(num_br)
    d["area_m2"] = area_priv.where(area_priv > 0, area_tot)
    d["quartos"] = descr.str.extract(r"(\d+)\s*qto", expand=False).astype("Int64")

    nomes = carregar_bairros().set_index("codbairro")["nome"]
    for _, r in d.iterrows():
        saida["imoveis"].append({
            "numero": (r[c_num] or "").strip() if c_num else None,
            "codbairro": r["codbairro"], "bairro_anuncio": (r[c_bai] or "").strip(),
            "bairro": nomes.get(r["codbairro"]) if r["codbairro"] else None,
            "endereco": (r[c_end] or "").strip() if c_end else None,
            "tipo": r["tipo"] if isinstance(r["tipo"], str) else None,
            "area_m2": None if pd.isna(r["area_m2"]) else round(float(r["area_m2"]), 1),
            "quartos": None if pd.isna(r["quartos"]) else int(r["quartos"]),
            "preco": num_br(r[c_preco]), "valor_avaliacao": num_br(r[c_aval]) if c_aval else None,
            "desconto_pct": num_br(r[c_desc]) if c_desc else None,
            "modalidade": (r[c_mod] or "").strip() if c_mod else None,
            "link": (r[c_link] or "").strip() if c_link else None,
            "descricao": (r[c_descr] or "").strip() if c_descr else None,
        })
    saida["data_lista"] = datetime.fromtimestamp(ARQ.stat().st_mtime).date().isoformat()
    (SITE_DATA / "imoveis_caixa.json").write_text(json.dumps(saida, ensure_ascii=False), encoding="utf-8")

    print(f"Imoveis no municipio do Rio: {len(d)} | sem bairro reconhecido: {d['codbairro'].isna().sum()}")
    nr = d.loc[d["codbairro"].isna(), c_bai].value_counts().head(15)
    if len(nr):
        print("Bairros nao reconhecidos (acrescentar em APELIDOS_BAIRRO?):", nr.to_dict())
    mvp = d[d["codbairro"].isin(codigos_mvp())]
    print("\nImoveis nos bairros do MVP:")
    print(mvp.groupby(mvp["codbairro"].map(nomes)).agg(n=("codbairro", "size"),
          preco_mediano=(c_preco, lambda x: pd.Series(x.map(num_br)).median())).to_string())


if __name__ == "__main__":
    main()
