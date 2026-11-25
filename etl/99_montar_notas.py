"""
99 - Transforma indicadores em notas 0-10 e gera site/data/bairros.json.

Nota de um indicador = posicao do bairro entre os bairros da cidade com pop >= POP_MINIMA:
    nota = 10 x (fracao dos OUTROS bairros de referencia que estao PIOR + metade dos empatados)
Ex.: 8,0 = "melhor que 80% dos bairros do Rio neste indicador".
Nota do criterio = media ponderada das notas dos indicadores (pesos em config / meta).
Nota final = feita no site, com os pesos (1 a 5) escolhidos pelo usuario.

Rode depois de 01 a 10.
"""
import json
from datetime import date

import numpy as np
import pandas as pd

from comum import PROC, SITE_DATA, carregar_bairros, codigos_mvp, config, referencia


def ler(crit):
    df = pd.read_csv(PROC / f"ind_{crit}.csv", dtype={"codbairro": str}).set_index("codbairro")
    meta = json.loads((PROC / f"meta_{crit}.json").read_text(encoding="utf-8"))
    return df, meta


def nota_percentil(valores: pd.Series, maior_e_pior: bool, ref: list[str]) -> pd.Series:
    r = valores.reindex(ref).dropna()
    out = {}
    for cod, v in valores.items():
        if pd.isna(v) or cod not in ref:
            out[cod] = np.nan
            continue
        outros = r.drop(cod, errors="ignore").to_numpy()
        pior = (outros > v).sum() if maior_e_pior else (outros < v).sum()
        empate = (outros == v).sum()
        out[cod] = 10 * (pior + 0.5 * empate) / len(outros)
    return pd.Series(out)


def media_ponderada(notas: pd.DataFrame, pesos: dict) -> pd.Series:
    cols = [c for c in pesos if pesos[c] > 0]
    w = pd.Series({c: pesos[c] for c in cols})
    n = notas[cols]
    soma_w = n.notna().mul(w).sum(axis=1)
    return (n.mul(w).sum(axis=1) / soma_w).where(soma_w > 0)


def r1(x):
    return None if x is None or pd.isna(x) else round(float(x), 1)


def main():
    b = carregar_bairros().set_index("codbairro")
    ref = referencia()
    exibidos = list(b.index) if config.EXIBIR_TODOS else codigos_mvp()

    criterios, metas = {}, {}
    for crit in config.CRITERIOS:
        df, meta = ler(crit)
        metas[crit] = meta
        ind_meta = meta["indicadores"]
        notas = pd.DataFrame({k: nota_percentil(df[k], v["maior_e_pior"], ref) for k, v in ind_meta.items()})
        if crit == "escolas":
            por_tipo = {t: media_ponderada(notas, p) for t, p in config.ESCOLAS_PESOS.items()}
            nota = por_tipo["tanto_faz"]
        else:
            nota = media_ponderada(notas, {k: v["peso"] for k, v in ind_meta.items()})
            por_tipo = None
        criterios[crit] = {"df": df, "notas": notas, "nota": nota, "por_tipo": por_tipo}

    preco, meta_preco = ler("preco")
    medianas = {c: criterios[c]["df"].reindex(ref).median(numeric_only=True) for c in criterios}

    # distribuicao de referencia do emprego (o site recalcula a nota se o usuario escolher o polo)
    emp = criterios["emprego"]["df"]
    # {polo: {codbairro: km}} so dos bairros de referencia (o site recalcula o percentil)
    ref_emprego = {k: {c: round(float(v) / 1000, 2) for c, v in emp.loc[emp.index.isin(ref), f"dist_{k}_m"].dropna().items()}
                   for k in config.POLOS}

    bairros_json = []
    for cod in exibidos:
        linha = b.loc[cod]
        item = {"codbairro": cod, "nome": linha["nome"], "regiao": linha["rp"],
                "populacao_2022": int(linha["pop2022_oficial"]) if pd.notna(linha["pop2022_oficial"]) else int(linha["pop2022"]),
                "tem_nota": cod in ref, "criterios": {}, "ruido_db_oficial": None}
        for crit, c in criterios.items():
            df, notas = c["df"], c["notas"]
            inds = []
            for k, v in metas[crit]["indicadores"].items():
                inds.append({"id": k, "rotulo": v["rotulo"], "unidade": v["unidade"],
                             "valor": r1(df.at[cod, k]) if cod in df.index else None,
                             "mediana_cidade": r1(medianas[crit].get(k)),
                             "nota": r1(notas.at[cod, k]) if cod in notas.index else None,
                             "peso": v.get("peso"), "maior_e_pior": v["maior_e_pior"]})
            bloco = {"nota": r1(c["nota"].get(cod)), "indicadores": inds}
            if c["por_tipo"]:
                bloco["nota_por_tipo"] = {t: r1(s.get(cod)) for t, s in c["por_tipo"].items()}
            if crit == "violencia":
                cisps = df.at[cod, "cisps"] if cod in df.index else "[]"
                bloco["cisps"] = json.loads(cisps.replace("'", '"')) if isinstance(cisps, str) else []
            if crit == "escolas":
                bloco["contagem_no_bairro"] = {k: int(df.at[cod, k]) for k in
                                               ("n_publicas_no_bairro", "n_privadas_no_bairro", "n_com_ideb_no_bairro")}
            if crit == "transporte":
                bloco["estacao_mais_comum"] = df.at[cod, "estacao_mais_comum"]
            if crit == "emprego":
                bloco["dist_km"] = {k: r1(df.at[cod, f"dist_{k}_m"] / 1000) for k in config.POLOS}
            if crit == "barulho":
                bloco["chamados_1746_n"] = int(df.at[cod, "chamados_1746_n"])
            if crit == "alagamento":
                bloco["cor_n"] = int(df.at[cod, "cor_n"])
            item["criterios"][crit] = bloco
        p = preco.loc[cod] if cod in preco.index else None
        item["preco_itbi"] = None if p is None or pd.isna(p["rs_m2"]) else {
            "rs_m2": int(round(p["rs_m2"])), "transacoes": int(p["transacoes"]),
            "valor_medio": int(round(p["valor_medio"])), "area_media_m2": r1(p["area_media_m2"])}
        bairros_json.append(item)

    base = json.loads((PROC / "meta_base.json").read_text())
    saida = {
        "gerado_em": date.today().isoformat(),
        "metodo_nota": "Nota de 0 a 10 = posição do bairro entre os bairros do Rio com pelo menos "
                       f"{config.POP_MINIMA} moradores ({len(ref)} bairros). Ex.: 8,0 = melhor que 80% deles.",
        "criterios": config.CRITERIOS,
        "referencia_codigos": ref,
        # mediana do R$/m2 (ITBI) dos bairros de referencia: usada no resumo em texto do site
        "preco_mediana_rs_m2": int(round(preco.reindex(ref)["rs_m2"].median())),
        "todos_bairros": {c: n for c, n in zip(b.index, b["nome"])},
        "pesos_perfil": config.PESOS_PERFIL,
        "escolas_pesos_por_tipo": config.ESCOLAS_PESOS,
        "emprego": {"polos": metas["emprego"]["polos"], "peso_padrao": metas["emprego"]["peso_padrao"],
                    "referencia_km": ref_emprego, "n_referencia": len(ref)},
        "fontes": {**{c: metas[c] for c in config.CRITERIOS}, "preco": meta_preco,
                   "base": {"nome": "Malha de bairros (IPP) e setores do Censo 2022 (IBGE, via Data.Rio)",
                            "editado_em": base}},
        "bairros": bairros_json,
    }
    (SITE_DATA / "bairros.json").write_text(json.dumps(saida, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    # --- tabela para conferencia
    t = pd.DataFrame({crit: criterios[crit]["nota"] for crit in config.CRITERIOS}).loc[exibidos]
    t.insert(0, "bairro", b.loc[exibidos, "nome"])
    for perfil, pesos in config.PESOS_PERFIL.items():
        t[f"FINAL_{perfil}"] = sum(t[c] * w for c, w in pesos.items()) / sum(pesos.values())
    t["R$/m2"] = preco.reindex(exibidos)["rs_m2"].round(0)
    pd.set_option("display.width", 250)
    print(f"Bairros de referencia: {len(ref)} | exibidos: {len(exibidos)}")
    print(t.sort_values("FINAL_familia", ascending=False).round(1).to_string())
    print(f"\nGravado site/data/bairros.json ({(SITE_DATA / 'bairros.json').stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
