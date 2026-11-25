#!/usr/bin/env bash
# Baixa os arquivos que o ETL precisa e que NAO sao baixados pelos proprios scripts.
# (Catalogo de Escolas do INEP e lista da Caixa sao manuais: ver README.)
#
#   bash etl/ferramentas/baixar_dados.sh
#
# O servidor do INEP envia a cadeia de certificados incompleta; o arquivo etl/ca_inep.pem
# completa a cadeia (com o intermediario oficial da RNP/GlobalSign) SEM desligar a verificacao.
# Se o INEP ou o ISP estiverem fora do ar (acontece), o script para sem estragar nada: tente mais tarde.
set -euo pipefail
cd "$(dirname "$0")/../.."
# baixa para um arquivo temporario e so substitui o antigo se terminar (falha nunca estraga o que ja existe)
baixar() {  # baixar URL DESTINO [opcoes extras do curl]
  local url="$1" destino="$2"; shift 2
  curl -fSL --retry 4 --retry-delay 10 --connect-timeout 30 "$@" -o "$destino.parcial" "$url" && mv "$destino.parcial" "$destino"
}
ANO=$(.venv/bin/python -c "import sys; sys.path.insert(0,'etl'); import config; print(config.IDEB_ANO)")

echo "== ISP: limites das delegacias (CISP)"
mkdir -p data_raw/isp/cisp_shp
baixar https://www.ispdados.rj.gov.br/Arquivos/CISPshp.rar data_raw/isp/CISPshp.rar
unrar x -o+ -inul data_raw/isp/CISPshp.rar data_raw/isp/cisp_shp/
ls data_raw/isp/cisp_shp

echo "== INEP: Ideb $ANO por escola"
mkdir -p data_raw/inep
for etapa in anos_iniciais anos_finais ensino_medio; do
  baixar "https://download.inep.gov.br/ideb/resultados/divulgacao_${etapa}_escolas_${ANO}.zip" \
    "data_raw/inep/divulgacao_${etapa}_escolas_${ANO}.zip" --cacert etl/ca_inep.pem
done
rm -rf data_raw/inep/ext data_proc/ideb_rio_*.csv   # forca reler o Ideb novo
ls -la data_raw/inep/*.zip
echo "Pronto. Agora rode: bash etl/rodar_tudo.sh --atualizar"
