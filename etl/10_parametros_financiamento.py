"""
10 - Parametros do simulador -> site/data/parametros_financiamento.json

- MCMV: valores da pagina oficial do Ministerio das Cidades (transcritos abaixo, com URL e data).
  QUANDO O GOVERNO MUDAR AS REGRAS: atualize o bloco MCMV e a data de consulta.
- Taxa SBPE padrao: buscada automaticamente na API de taxas de juros do Banco Central
  (media das operacoes contratadas da Caixa no ultimo mes publicado).
- ITBI: aliquota da Prefeitura (Carioca Digital).
"""
import json
from datetime import date

import requests

from comum import SITE_DATA

CONSULTA = "2026-11-25"
URL_MCMV = ("https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/habitacao/"
            "programa-minha-casa-minha-vida/mcmv-fgts")
URL_CAIXA_MUN = "https://www.caixa.gov.br/Downloads/fgts-tabela-municipios/TABELA_MUNICIPIOS_VIGENCIA_01JAN2026.xlsx"
URL_BCB = "https://olinda.bcb.gov.br/olinda/servico/taxaJuros/versao/v2/odata/TaxasJurosMensalPorMes"
MODALIDADE_SBPE = "Financiamento imobiliário com taxas de mercado - Pós-fixado referenciado em TR"
CNPJ8_CAIXA = "00360305"

# Tabela de juros do MCMV (regiao Sudeste), conforme a pagina do Ministerio (atualizada em 28/10/2026).
# renda_ate = limite superior da sub-faixa de renda familiar bruta mensal.
MCMV = {
    "fonte": "Ministério das Cidades - Minha Casa, Minha Vida, Linha Financiada (FGTS)",
    "url": URL_MCMV,
    "pagina_atualizada_em": "2026-10-28",
    "consultado_em": CONSULTA,
    "regiao": "Sudeste (S, SE e CO na tabela oficial)",
    "faixas": [
        {"faixa": "Faixa 1", "renda_ate": 2160.00, "juros_cotista": 4.25, "juros_nao_cotista": 4.75, "teto_imovel": 275000},
        {"faixa": "Faixa 1", "renda_ate": 2850.00, "juros_cotista": 4.50, "juros_nao_cotista": 5.00, "teto_imovel": 275000},
        {"faixa": "Faixa 1", "renda_ate": 3200.00, "juros_cotista": 4.75, "juros_nao_cotista": 5.25, "teto_imovel": 275000},
        {"faixa": "Faixa 2", "renda_ate": 3500.00, "juros_cotista": 5.00, "juros_nao_cotista": 5.50, "teto_imovel": 275000},
        {"faixa": "Faixa 2", "renda_ate": 4000.00, "juros_cotista": 5.50, "juros_nao_cotista": 6.00, "teto_imovel": 275000},
        {"faixa": "Faixa 2", "renda_ate": 5000.00, "juros_cotista": 6.50, "juros_nao_cotista": 7.00, "teto_imovel": 275000},
        {"faixa": "Faixa 3", "renda_ate": 9600.00, "juros_cotista": 7.66, "juros_nao_cotista": 8.16, "teto_imovel": 400000},
        {"faixa": "Classe Média", "renda_ate": 13000.00, "juros_cotista": 10.00, "juros_nao_cotista": 10.00, "teto_imovel": 600000},
    ],
    "notas_juros": "Nas linhas com dois valores na tabela oficial (R$ 3.500,01 a R$ 5.000 e Faixa 3), "
                   "o primeiro foi lido como cotista e o segundo como não cotista do FGTS.",
    "teto_faixas_1_2_fonte": {
        "texto": "Rio de Janeiro: R$ 275.000 (recorte A, grupo regional 1), máximo citado pelo Ministério para as Faixas 1 e 2.",
        "url": URL_CAIXA_MUN, "vigencia": "2026-01-01"},
    "subsidio_maximo": 55000,
    "subsidio_texto": "Famílias com renda até R$ 5.000 podem receber desconto (subsídio) de até R$ 55 mil "
                      "(fora da Região Norte). O valor é definido pela Caixa conforme renda e localização.",
    "prazo_max_anos": 35,
    "pro_cotista": {"juros": 8.66, "texto": "Pró-Cotista (FGTS): sem limite de renda, taxa de 8,66% a.a. "
                    "Exige ser cotista do FGTS; consulte as condições no banco."},
    "divergencia": "A planilha de municípios da Caixa (vigência 01/01/2026) ainda traz renda até R$ 12.000 e "
                   "tetos de R$ 350 mil (Faixa 3) e R$ 500 mil (Classe Média). Este app usa a página do "
                   "Ministério, atualizada em 28/10/2026.",
}


def taxa_sbpe_bcb():
    """Ultimo mes publicado: taxa media anual da Caixa, credito imobiliario a taxas de mercado, TR."""
    from urllib.parse import quote  # a API do BCB exige espacos como %20 (nao aceita "+")
    filtro = quote(f"Modalidade eq '{MODALIDADE_SBPE}' and cnpj8 eq '{CNPJ8_CAIXA}'")
    url = f"{URL_BCB}?$format=json&$top=1&$orderby=anoMes%20desc&$filter={filtro}"
    r = requests.get(url, timeout=90)
    r.raise_for_status()
    v = r.json()["value"][0]
    return {"juros_ano": v["TaxaJurosAoAno"], "mes": v["anoMes"], "banco": v["InstituicaoFinanceira"],
            "modalidade": v["Modalidade"],
            "fonte": "Banco Central do Brasil - Taxas de juros de operações de crédito (média das operações contratadas)",
            "url": "https://www.bcb.gov.br/estatisticas/txjuros", "api": URL_BCB,
            "aviso": "Média das operações contratadas no mês, não é a taxa de balcão. Edite com a taxa que o banco oferecer."}


def main():
    sbpe = taxa_sbpe_bcb()
    p = {
        "gerado_em": date.today().isoformat(),
        "aviso_geral": "Simulação estimada. A aprovação e as condições finais dependem do banco.",
        "comprometimento_renda_max": 0.30,
        "comprometimento_renda_texto": "Parcela de até 30% da renda bruta: referência usual dos bancos, "
                                       "adotada neste app (não é um número de lei).",
        "prazo_padrao_anos": 30,
        "mcmv": MCMV,
        "sbpe": sbpe,
        "itbi": {"aliquota": 0.03, "fonte": "Prefeitura do Rio - Carioca Digital (Lei 6.250/2017)",
                 "url": "https://carioca.rio/servicos/itbi-simulacao-de-valor-e-pedido-de-guia/",
                 "consultado_em": CONSULTA,
                 "nota": "A base de cálculo é o valor de mercado do imóvel; a Prefeitura pode usar valor de "
                         "referência maior que o preço declarado."},
        "custos_sem_valor": [
            {"item": "Escritura e registro (cartório)", "texto": "Consulte o cartório. No primeiro imóvel residencial "
             "financiado pelo SFH, os emolumentos têm 50% de desconto (Lei 6.015/1973, art. 290).",
             "url": "https://www.planalto.gov.br/ccivil_03/leis/l6015compilada.htm"},
            {"item": "Avaliação do imóvel pelo banco", "texto": "Consulte o banco."},
        ],
        "fgts_avisos": [
            "Mínimo de 3 anos de trabalho sob o regime do FGTS (somando períodos).",
            "Não ter imóvel no município onde mora ou trabalha (nem nos vizinhos da região metropolitana).",
            "Não ter financiamento ativo no Sistema Financeiro da Habitação (SFH).",
            "O imóvel deve ser residencial e estar dentro das regras do SFH.",
        ],
        "simplificacoes": "Sem TR, sem seguros obrigatórios (MIP e DFI) e sem tarifas mensais: os valores reais ficam um pouco maiores.",
        "cota_max_financiamento": None,
        "cota_max_texto": "O banco pode exigir entrada maior; este app não aplica limite de cota por falta de fonte oficial aberta.",
        "aluguel_aviso": "Comparação simples: não considera valorização do imóvel, reajuste do aluguel nem rendimento "
                         "da entrada se ela ficasse aplicada.",
    }
    (SITE_DATA / "parametros_financiamento.json").write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Taxa SBPE padrao: {sbpe['juros_ano']}% a.a. ({sbpe['banco']}, {sbpe['mes']})")
    print(f"MCMV: {len(MCMV['faixas'])} sub-faixas; pagina do Ministerio de {MCMV['pagina_atualizada_em']}")
    print("Gravado site/data/parametros_financiamento.json")


if __name__ == "__main__":
    main()
