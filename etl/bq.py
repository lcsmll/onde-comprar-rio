"""
Consultas ao BigQuery publico da Prefeitura (projeto 'datario').

Login (uma vez): ~/google-cloud-sdk/bin/gcloud auth application-default login
O resultado de cada consulta fica salvo em data_raw/bigquery/<nome>.csv.
Rodar de novo reaproveita o arquivo; para buscar dados novos: --atualizar
"""
import sys

import pandas as pd

from comum import RAW, config

PASTA = RAW / "bigquery"


def consultar(nome: str, sql: str) -> pd.DataFrame:
    PASTA.mkdir(parents=True, exist_ok=True)
    arq = PASTA / f"{nome}.csv"
    if arq.exists() and "--atualizar" not in sys.argv:
        print(f"(usando {arq.name} ja baixado; rode com --atualizar para buscar de novo)")
        return pd.read_csv(arq)

    import google.auth
    from google.cloud import bigquery
    cred, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/bigquery.readonly"])
    cli = bigquery.Client(project=config.BQ_PROJETO, credentials=cred)
    job = cli.query(sql)
    df = job.result().to_dataframe()
    print(f"BigQuery '{nome}': {len(df):,} linhas, leu {job.total_bytes_processed / 1e9:.2f} GB")
    df.to_csv(arq, index=False)
    return df
