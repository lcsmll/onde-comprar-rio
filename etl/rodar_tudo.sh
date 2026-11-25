#!/usr/bin/env bash
# Roda o ETL completo, em ordem, a partir da pasta do projeto:
#   bash etl/rodar_tudo.sh              (reaproveita consultas ja salvas do BigQuery)
#   bash etl/rodar_tudo.sh --atualizar  (busca dados novos do BigQuery tambem)
set -euo pipefail
cd "$(dirname "$0")/.."
PY=.venv/bin/python
for s in 01_bairros 02_violencia 03_alagamento 04_escolas 05_transporte 06_emprego \
         07_barulho 08_preco_itbi 09_imoveis_caixa 10_parametros_financiamento 11_mapa 99_montar_notas 12_paginas_bairros; do
  echo; echo "################ $s ################"
  $PY -W ignore "etl/$s.py" "$@"
done
