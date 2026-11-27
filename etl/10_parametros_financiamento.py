"""
10 - Parametros do simulador -> site/data/parametros_financiamento.json

- MCMV: valores da pagina oficial do Ministerio das Cidades (transcritos abaixo, com URL e data).
  QUANDO O GOVERNO MUDAR AS REGRAS: atualize o bloco MCMV e a data de consulta.
- Taxa SBPE padrao: buscada automaticamente na API de taxas de juros do Banco Central
  (media das operacoes contratadas da Caixa no ultimo mes publicado).
- ITBI: aliquota da Prefeitura (Carioca Digital).
- Cota maxima de financiamento (COTA_MAX): por linha e sistema, com fonte. Conferir junto com o MCMV.
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


# Cota maxima de financiamento: % do valor do imovel que o banco financia (o resto e a entrada,
# em dinheiro e/ou FGTS). Uma por linha e por sistema de amortizacao, cada uma com a fonte oficial.
# Decisao do usuario (27/11/2026): MCMV com 80% no SAC e na Price (regra geral da IN 48/2022, art. 34)
# e cota menor de imovel usado pela norma do orcamento do FGTS em vigor (IN 45/2025),
# Pro-Cotista registrado com os numeros da pagina do FGTS (o app nao simula essa linha).
URL_CAIXA_SBPE = ("https://caixanoticias.caixa.gov.br/Paginas/Not%C3%ADcias/2025/12-DEZEMBRO/"
                  "CAIXA-volta-a-permitir-mais-de-um-financiamento--imobiliario-pelo-SBPE.aspx")
URL_IN48 = ("https://www.gov.br/cidades/pt-br/acesso-a-informacao/institucional/base-juridica/"
            "instrucoes-normativas/IN_48_de_19.12.22__compilada_em_09.04.2026_.pdf")
# Orcamento do FGTS de 2026 (revoga a IN 30/2024, que tinha a cota de 65% no usado para renda de
# R$ 4.700,01 a R$ 8.600). Ver docs/ESCOPO.md, secao 26.
URL_IN45 = ("https://www.gov.br/cidades/pt-br/acesso-a-informacao/institucional/base-juridica/"
            "instrucoes-normativas/2026/20261014_INSTRUO_NORMATIVA_N._45_COMPILADA_ARQUIVOCORRIGIDO.pdf")
FONTE_IN45 = "IN MCID 45/2025 (orçamento do FGTS de 2026, versão compilada em 14/10/2026)"
URL_CLASSE_MEDIA = ("https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/habitacao/"
                    "programa-minha-casa-minha-vida/minha-casa-minha-vida-classe-media/minha-casa-minha-vida-classe-media-1")
URL_FGTS_FIN = "https://www.fgts.gov.br/Paginas/subpaginas/financiamentos.aspx"

COTA_MAX = {
    # Cada linha: "sac" e "price" = cota de imovel novo; "usado" = regras de cota menor para imovel usado
    # no Sul e Sudeste (o Rio esta no Sudeste). Cada regra vale para uma faixa do MCMV ("faixa") ou para
    # um intervalo de renda ("renda_de" e "renda_ate"); o site usa a menor entre a cota da linha e a da regra.
    "sbpe": {
        "sac": 0.80, "price": 0.70,
        "fonte": "CAIXA Notícias: \"CAIXA volta a permitir mais de um financiamento imobiliário pelo SBPE\" (09/12/2025)",
        "url": URL_CAIXA_SBPE, "data": "2025-12-09", "consultado_em": "2026-11-27",
        "texto": "A Caixa financia pelo SBPE até 80% do valor do imóvel no SAC e até 70% na Price "
                 "(regra em vigor desde 13/10/2025). Outros bancos podem ter cotas diferentes.",
        "usado": [],
        "usado_texto": "A Caixa não publica cota diferente para imóvel usado no SBPE; o app usa a mesma.",
    },
    "mcmv": {
        "sac": 0.80, "price": 0.80,
        "fonte": "Ministério das Cidades: Instrução Normativa nº 48/2022, art. 34 (versão compilada em 09/04/2026)",
        "url": URL_IN48, "data": "2026-04-09", "consultado_em": "2026-11-27",
        "texto": "No Minha Casa, Minha Vida (FGTS), a entrada mínima é de 20% do valor do imóvel, ou seja, "
                 "o financiamento vai até 80%. No SAC, o banco pode aceitar entrada de até 10%; o app usa os 20%, "
                 "que valem em qualquer caso.",
        "usado": [
            {"faixa": "Classe Média", "cota": 0.60, "regiao": "Sul e Sudeste",
             "fonte": FONTE_IN45 + ", art. 6º", "url": URL_IN45},
        ],
        "usado_texto": "Para imóvel usado no Sul e no Sudeste, a cota da Classe Média cai para 60% "
                       "(IN 45/2025, orçamento do FGTS de 2026). Nas Faixas 1, 2 e 3 não há cota menor para "
                       "usado em 2026: a regra de 65% da IN 30/2024 foi revogada.",
    },
    "pro_cotista": {
        "sac": 0.90, "price": 0.80,
        "fonte": "FGTS: página Financiamentos, Programa Pró-Cotista",
        "url": URL_FGTS_FIN, "data": None, "consultado_em": "2026-11-27",
        "texto": "Pró-Cotista: até 90% do valor de avaliação no SAC e 80% na Price. Para imóvel usado, "
                 "até 50%, com renda de até R$ 12 mil (IN 45/2025, art. 5º). O app não simula esta linha.",
        "usado": [{"renda_de": 0, "renda_ate": 12000, "cota": 0.50, "fonte": FONTE_IN45 + ", art. 5º", "url": URL_IN45}],
    },
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
        "cota_max": COTA_MAX,
        "cota_max_texto": "O banco financia só uma parte do imóvel (a cota); o resto é a entrada, em dinheiro e FGTS. "
                          "O app usa a cota da Caixa no SBPE (80% no SAC e 70% na Price, CAIXA Notícias, dez/2025) "
                          "e a do Minha Casa, Minha Vida (80%, IN 48/2022 do Ministério das Cidades; 60% no imóvel usado "
                          "da Classe Média, IN 45/2025). Outros bancos podem exigir entrada maior.",
        "aluguel_aviso": "Comparação simples: não considera valorização do imóvel, reajuste do aluguel nem rendimento "
                         "da entrada se ela ficasse aplicada.",
    }
    (SITE_DATA / "parametros_financiamento.json").write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Taxa SBPE padrao: {sbpe['juros_ano']}% a.a. ({sbpe['banco']}, {sbpe['mes']})")
    print(f"MCMV: {len(MCMV['faixas'])} sub-faixas; pagina do Ministerio de {MCMV['pagina_atualizada_em']}")
    for k, c in COTA_MAX.items():
        print(f"Cota {k}: SAC {c['sac']:.0%}, Price {c['price']:.0%}")
    print("Gravado site/data/parametros_financiamento.json")


if __name__ == "__main__":
    main()
