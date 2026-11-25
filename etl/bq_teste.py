"""
Teste de acesso ao BigQuery publico da Prefeitura do Rio (projeto 'datario').

Como rodar (uma vez):
    .venv/bin/python etl/bq_teste.py SEU_PROJETO_GOOGLE_CLOUD

- SEU_PROJETO_GOOGLE_CLOUD e o ID de um projeto seu no Google Cloud (pode ser no
  modo "sandbox", gratuito, sem cartao). E nele que a consulta e "cobrada" -- dentro
  da cota gratis de 1 TB por mes.
- Antes, faca o login uma vez com a ferramenta oficial do Google:
      gcloud auth application-default login
  O token fica em ~/.config/gcloud/ e nao vai para o git.

O que o script faz: le o esquema das duas tabelas e estima (dry run) quantos
bytes as consultas do ETL vao ler. Nao baixa dados ainda.
"""
import sys

import google.auth
from google.cloud import bigquery

SCOPES = ["https://www.googleapis.com/auth/bigquery.readonly"]

# O Data.Rio cita dois nomes para a tabela do 1746; o script usa o primeiro que existir.
CANDIDATAS = {
    "1746": ["datario.adm_central_atendimento_1746.chamado",
             "datario.administracao_servicos_publicos.chamado_1746"],
    "COR": ["datario.adm_cor_comando.ocorrencias"],
}
TABELAS = {}


def main(projeto: str) -> None:
    # Usa o login padrao do Google (feito uma vez com: gcloud auth application-default login)
    cred, _ = google.auth.default(scopes=SCOPES)
    client = bigquery.Client(project=projeto, credentials=cred)

    for nome, opcoes in CANDIDATAS.items():
        for tabela in opcoes:
            try:
                t = client.get_table(tabela)
                TABELAS[nome] = tabela
                break
            except Exception as e:
                print(f"   ({tabela} indisponivel: {type(e).__name__})")
        else:
            sys.exit(f"Nenhuma tabela encontrada para {nome}")
        print(f"\n== {nome}: {tabela}")
        print(f"   linhas: {t.num_rows:,}   tamanho: {t.num_bytes/1e9:.2f} GB   modificada: {t.modified:%Y-%m-%d}")
        print("   colunas:", ", ".join(f.name for f in t.schema))

    # Estimativa de custo (dry run = nao executa, so calcula bytes lidos)
    consultas = {
        "1746 tipos": f"SELECT tipo, subtipo, COUNT(*) n FROM `{TABELAS['1746']}` "
                      "WHERE data_inicio >= '2024-01-01' GROUP BY 1,2",
        "COR tipos": f"SELECT id_pop, COUNT(*) n FROM `{TABELAS['COR']}` GROUP BY 1",
    }
    cfg = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    print()
    for nome, sql in consultas.items():
        try:
            job = client.query(sql, job_config=cfg)
            print(f"dry run '{nome}': leria {job.total_bytes_processed/1e9:.2f} GB")
        except Exception as e:  # nomes de coluna podem diferir; o esquema acima mostra os certos
            print(f"dry run '{nome}': erro -> {e}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Uso: .venv/bin/python etl/bq_teste.py SEU_PROJETO_GOOGLE_CLOUD")
    main(sys.argv[1])
