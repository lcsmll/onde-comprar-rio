"""
Funcoes usadas por todos os scripts do ETL.

Ideia central ("media dos moradores"): cada indicador e calculado no SETOR
censitario (Censo 2022) e depois vira media do bairro ponderada pela populacao.
Para isso cada setor e representado por um "ponto interno" (representative_point:
um ponto garantidamente dentro do poligono, diferente do centroide, que pode cair fora).
"""
import json
import sys
from datetime import date
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data_raw"
PROC = ROOT / "data_proc"          # intermediarios (fora do git)
SITE_DATA = ROOT / "site" / "data"
PROC.mkdir(exist_ok=True)
SITE_DATA.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402


def cod3(x) -> str:
    """Codigo de bairro sempre como texto de 3 digitos ('4' -> '004')."""
    return str(int(x)).zfill(3)


def carregar_bairros() -> gpd.GeoDataFrame:
    """Malha oficial de bairros (IPP), em metros. Gerada por 01_bairros.py."""
    return gpd.read_parquet(PROC / "bairros.parquet")


def carregar_setores(pontos: bool = True) -> gpd.GeoDataFrame:
    """Setores do Censo 2022 com populacao. pontos=True troca o poligono pelo ponto interno."""
    s = gpd.read_parquet(PROC / "setores.parquet")
    if pontos:
        s = s.set_geometry("ponto")
    return s


def media_pop(setores: pd.DataFrame, coluna: str) -> pd.Series:
    """Media do bairro ponderada pela populacao dos setores (ignora setores sem valor)."""
    d = setores[["codbairro", "pop", coluna]].dropna()
    d = d[d["pop"] > 0]
    soma = (d[coluna] * d["pop"]).groupby(d["codbairro"]).sum()
    peso = d.groupby("codbairro")["pop"].sum()
    return soma / peso


def salvar_indicadores(criterio: str, df: pd.DataFrame, meta: dict) -> None:
    """Grava a tabela (1 linha por bairro) e os metadados (fonte, periodo, avisos)."""
    df = df.copy()
    df.index = df.index.map(cod3)
    df.index.name = "codbairro"
    df.to_csv(PROC / f"ind_{criterio}.csv")
    meta = {"criterio": criterio, "processado_em": date.today().isoformat(), **meta}
    with open(PROC / f"meta_{criterio}.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def codigos_mvp() -> list[str]:
    with open(PROC / "bairros_mvp.json", encoding="utf-8") as f:
        return json.load(f)


def resumo(titulo: str, df: pd.DataFrame, casas: int = 1) -> None:
    """Imprime o resultado para os bairros do MVP e a mediana da cidade."""
    b = carregar_bairros().set_index("codbairro")["nome"]
    mvp = [c for c in codigos_mvp() if c in df.index]
    t = df.loc[mvp].copy()
    t.insert(0, "bairro", b.reindex(t.index).values)
    print(f"\n=== {titulo} ===")
    print(t.round(casas).to_string())
    print("\nMediana da cidade (bairros com pop >= %d):" % config.POP_MINIMA)
    ref = df.loc[df.index.isin(referencia())]
    print(ref.median(numeric_only=True).round(casas).to_string())


def referencia() -> list[str]:
    """Bairros que entram na comparacao (pop >= POP_MINIMA)."""
    b = carregar_bairros()
    return b.loc[b["pop2022"] >= config.POP_MINIMA, "codbairro"].tolist()


# ---------------------------------------------------------------------------
# Casar nomes de bairro escritos livremente (endereco, COR, Caixa) com a malha oficial
# ---------------------------------------------------------------------------
import re
import unicodedata

# Grafias populares/abreviadas -> nome oficial. Acrescente aqui quando o resumo de um
# script listar um nome nao reconhecido.
APELIDOS_BAIRRO = {
    "FREGUESIA JACAREPAGUA": "Freguesia (Jacarepaguá)",
    "FREGUESIA JPA": "Freguesia (Jacarepaguá)",
    "FREGUESIA (JPA)": "Freguesia (Jacarepaguá)",
    "JACAREPAGUA FREGUESIA": "Freguesia (Jacarepaguá)",
    "FREGUESIA ILHA DO GOVERNADOR": "Freguesia (Ilha)",
    "FREGUESIA (ILHA DO GOVERNADOR)": "Freguesia (Ilha)",
    "IRAJ": "Irajá",
    "BRAZ DE PINA": "Brás de Pina",
    "BRAZ DEPINA": "Brás de Pina",
    "OSWALDO CRUZ": "Osvaldo Cruz",
    "FREGUESIA JACAREPAGU": "Freguesia (Jacarepaguá)",   # texto cortado no INEP
    "TAUA - ILHA DO GOVERNADOR": "Tauá",
    "CIDADE UNIVERSITARIA": "Cidade Universitária",
    "RECREIO": "Recreio dos Bandeirantes",
    "BARRA": "Barra da Tijuca",
    "JARDIM BOTANICO": "Jardim Botânico",
    "CAJU": "Caju",
    "VILA VALQUEIRE": "Vila Valqueire",
    "VL VALQUEIRE": "Vila Valqueire",
    "VL DA PENHA": "Vila da Penha",
    "VL ISABEL": "Vila Isabel",
    "PCA SECA": "Praça Seca",
    "PRACA SECA": "Praça Seca",
    "SAO CRISTOVAO": "Imperial de São Cristóvão",   # nome oficial mudou
    "MUZEMA": "Itanhangá",                          # sub-localidade
    "JARDIM MARAVILHA": "Guaratiba",                # sub-localidade
}


def norm_nome(s) -> str:
    """Maiusculas, sem acento, espacos simples (para comparar nomes)."""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s.upper().replace(".", " ")).strip()


def casador_bairros():
    """Retorna uma funcao nome_livre -> codbairro (ou None)."""
    b = carregar_bairros()
    oficial = {norm_nome(n): c for n, c in zip(b["nome"], b["codbairro"])}
    por_nome = dict(zip(b["nome"], b["codbairro"]))
    apelidos = {norm_nome(k): por_nome[v] for k, v in APELIDOS_BAIRRO.items() if v in por_nome}
    tabela = {**oficial, **apelidos}
    chaves = sorted(tabela, key=len, reverse=True)

    freg_jpa, freg_ilha = por_nome.get("Freguesia (Jacarepaguá)"), por_nome.get("Freguesia (Ilha)")

    def casar(nome, termina_com=False, cep=None):
        if nome is None or (isinstance(nome, float) and nome != nome):
            return None
        n = norm_nome(nome)
        # "FREGUESIA" sozinho e ambiguo: decide pelo CEP (Jacarepagua 227xx-228xx, Ilha 219xx)
        if (n == "FREGUESIA" or n.endswith(" FREGUESIA")) and cep:
            cep = str(cep).replace("-", "")
            if cep.startswith(("227", "228")):
                return freg_jpa
            if cep.startswith("219"):
                return freg_ilha
        if n in tabela:
            return tabela[n]
        if termina_com:  # ex.: "RUA X, 10 CASA 2 MEIER" -> procura o nome mais longo no fim
            for k in chaves:
                if n.endswith(" " + k):
                    return tabela[k]
        return None

    return casar


def slug(nome: str) -> str:
    """'Freguesia (Jacarepaguá)' -> 'freguesia-jacarepagua' (mesma regra do app.js)."""
    s = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[()]", "", s).strip()
    return re.sub(r"\s+", "-", s)
