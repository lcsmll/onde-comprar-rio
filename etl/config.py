"""
Parametros do ETL. Tudo que e "regra" do calculo fica aqui, com comentario.
Mudar um numero aqui e rodar os scripts de novo e suficiente -- nada fica
escondido dentro do codigo dos criterios.
"""

# ---------------------------------------------------------------------------
# Bairros exibidos no site (codigo oficial do IPP, 3 digitos).
# O ETL calcula TODOS os bairros da cidade; esta lista so controla o que o site mostra.
# Para abrir a cidade inteira: EXIBIR_TODOS = True
# ---------------------------------------------------------------------------
EXIBIR_TODOS = True   # 25/11/2026: cidade inteira (era so a lista abaixo)
# Nomes exatos (como na malha oficial); 01_bairros.py converte em codigos e para se algum nao existir.
BAIRROS_MVP_NOMES = [
    "Méier", "Cachambi", "Tijuca", "Vila Isabel", "Grajaú", "Madureira", "Irajá",
    "Penha", "Vila da Penha", "Praça Seca", "Tanque", "Taquara",
    "Freguesia (Jacarepaguá)", "Pechincha", "Vila Valqueire",
]

# Bairros com menos moradores que isto nao recebem nota (e nao entram na comparacao).
POP_MINIMA = 1000

# Sistema de coordenadas em metros usado nos calculos de distancia/area (SIRGAS 2000 / UTM 23S).
CRS_METROS = 31983

# ---------------------------------------------------------------------------
# Violencia (ISP)
# ---------------------------------------------------------------------------
VIOLENCIA_MESES = 12  # ultimos N meses publicados
# Pesos revistos em 25/11/2026 (eram 50/20/20/10): roubo por morador infla em areas de
# passagem (ex.: entorno do Maracana) e e subnotificado onde se denuncia menos; a letalidade
# (morte quase sempre e registrada) e o indicador mais confiavel e passa a dominar.
VIOLENCIA_INDICADORES = {
    # id: (colunas do ISP somadas, peso no criterio, rotulo)
    "letalidade_100k": (["letalidade_violenta"], 0.70, "Letalidade violenta"),
    "roubo_veiculo_100k": (["roubo_veiculo"], 0.10, "Roubo de veículo"),
    "roubo_rua_100k": (["roubo_rua"], 0.10, "Roubo de rua (transeunte, celular e coletivo)"),
    "roubo_residencia_100k": (["roubo_residencia"], 0.10, "Roubo a residência"),
}

# ---------------------------------------------------------------------------
# Alagamento
# ---------------------------------------------------------------------------
ALAGAMENTO_PESOS = {"ismfi": 0.70, "cor_km2": 0.30}
COR_POPS_ALAGAMENTO = [5, 6, 31, 32, 33]  # bolsao, alagamentos e enchentes, alagamento, enchente, lamina d'agua

# ---------------------------------------------------------------------------
# Escolas
# ---------------------------------------------------------------------------
# Edicao do Ideb por escola (o INEP divulga a cada 2 anos; a de 2027 deve sair em 2028).
# Para atualizar: troque o ano, baixe os arquivos (etl/ferramentas/baixar_dados.sh) e rode o ETL.
IDEB_ANO = 2025
ESCOLA_RAIO_OFERTA_M = 1500
ESCOLA_RAIO_IDEB_M = 2000
ESCOLAS_PESOS = {  # por tipo de escola procurada (pergunta extra da familia)
    "tanto_faz": {"oferta_publica": 0.35, "ideb_publica": 0.35, "oferta_privada": 0.30},
    "publica": {"oferta_publica": 0.50, "ideb_publica": 0.50, "oferta_privada": 0.0},
    "particular": {"oferta_publica": 0.0, "ideb_publica": 0.0, "oferta_privada": 1.0},
}

# ---------------------------------------------------------------------------
# Transporte
# ---------------------------------------------------------------------------
TRANSPORTE_RAIO_M = 1000
# Revisto em 25/11/2026 (era distancia 70% + estacoes a 1 km 30%): a contagem de estacoes
# tratava cada parada de BRT (a cada ~600 m) como uma estacao de metro. Agora: distancia ate
# qualquer estacao + distancia ate metro ou trem (alta capacidade). A contagem fica so como informacao.
TRANSPORTE_PESOS = {"dist_estacao_m": 0.50, "dist_trilho_m": 0.50}
TRANSPORTE_MODOS_TRILHO = ["Metrô", "Trem"]

# ---------------------------------------------------------------------------
# Emprego: polos (nome da estacao na camada oficial) -- conferidos em 06_emprego.py
# ---------------------------------------------------------------------------
POLOS = {
    "centro": {"rotulo": "Centro (estação Carioca)", "camada": "metro", "nome": "Carioca"},
    "barra": {"rotulo": "Barra (Terminal Alvorada)", "camada": "brt", "nome": "Alvorada"},
    "zona_sul": {"rotulo": "Zona Sul (estação Botafogo)", "camada": "metro", "nome": "Botafogo"},
}
# Para o peso padrao Centro x Barra (RAIS 2016): quais bairros contam como cada polo
POLO_CENTRO_AP = "1"      # Area de Planejamento 1 (Centro e entorno)
POLO_BARRA_RA = 24        # Regiao Administrativa XXIV - Barra da Tijuca

# ---------------------------------------------------------------------------
# Barulho
# ---------------------------------------------------------------------------
BARULHO_PESOS = {"chamados_1746_1000hab": 0.40, "pct_via_pesada": 0.25,
                 "pct_trilho_brt": 0.20, "pct_aeroporto": 0.15}
BARULHO_1746_MESES = 24
BARULHO_1746_FILTRO = {
    "tipos": ["Perturbação do sossego", "Poluição"],
    "subtipos": ["Fiscalização de perturbação do sossego", "Fiscalização de carros de som",
                 "Fiscalização de poluição sonora"],
    "categorias": ["Serviço", "Reclamação"],
}
BARULHO_VIA_BUFFER_M = 50
# Inclui "Arterial secundária" porque a classificação oficial põe ali ruas muito movimentadas
# (ex.: Conde de Bonfim, Haddock Lobo, Boulevard 28 de Setembro). Escopo original: só as duas primeiras.
BARULHO_VIAS_PESADAS = ["Estrutural", "Arterial primária", "Arterial secundária"]
BARULHO_TRILHO_BUFFER_M = 100
BARULHO_PEZR_MIN_DB = 65

# ---------------------------------------------------------------------------
# Preco (ITBI)
# ---------------------------------------------------------------------------
ITBI_MESES = 12

# Projeto Google Cloud usado para "pagar" as consultas no BigQuery (cota gratis)
BQ_PROJETO = "imovel-rio"

# ---------------------------------------------------------------------------
# Pesos padrao por perfil (1 a 5) -- aprovados na Etapa 2. Vao para o site via bairros.json.
# ---------------------------------------------------------------------------
CRITERIOS = ["violencia", "alagamento", "escolas", "transporte", "emprego", "barulho"]
PESOS_PERFIL = {
    "familia":  {"violencia": 5, "alagamento": 4, "escolas": 5, "transporte": 3, "emprego": 3, "barulho": 3},
    "casal":    {"violencia": 4, "alagamento": 4, "escolas": 2, "transporte": 4, "emprego": 4, "barulho": 3},
    "solteiro": {"violencia": 4, "alagamento": 3, "escolas": 1, "transporte": 5, "emprego": 5, "barulho": 3},
}

# Endereco publico do site (usado nas previas de link do WhatsApp, que exigem URL completa)
SITE_URL = "https://lcsmll.github.io/onde-comprar-rio/"

# ---------------------------------------------------------------------------
# Subnotificacao (decisao de 25/11/2026, ao abrir a cidade inteira)
# Em areas de favela, boletins de ocorrencia e chamados ao 1746 sao pouco registrados, o que
# infla as notas de Seguranca e Menos barulho (ex.: Rocinha teria seguranca 9,7). Nos bairros
# com FAVELA_CORTE_PCT % ou mais dos moradores em favela (Limite de Favelas 2022, IPP), essas
# notas ficam como "dados insuficientes", o bairro nao recebe nota final nem posicao no ranking,
# e ele sai da base de comparacao desses criterios.
# ---------------------------------------------------------------------------
FAVELA_CORTE_PCT = 50
CRITERIOS_SUBNOTIFICADOS = ["violencia", "barulho"]

# ---------------------------------------------------------------------------
# Seguranca com dados insuficientes (decisao do usuario, 27/11/2026; revista no mesmo dia)
# A taxa da delegacia (CISP) e crimes / moradores da CISP inteira. Ela nao representa um bairro
# SEPARADO FISICAMENTE da area principal da sua delegacia (ilha). Nesses bairros, Seguranca fica como
# "dados insuficientes", o bairro nao recebe nota final nem posicao no ranking (mesmo caminho da
# subnotificacao em favela) e sai da base de comparacao de Seguranca. Os outros criterios continuam.
# Ser pequeno perto da delegacia NAO entra aqui: todo bairro usa a taxa da delegacia inteira, seja
# 4% ou 30% dela (ver docs/ESCOPO.md, secao 25).
# Chave = nome exato do bairro na malha oficial; valor = motivo (aparece no site).
# ---------------------------------------------------------------------------
BAIRROS_SEGURANCA_INSUFICIENTE = {
    "Paquetá": "Paquetá é uma ilha e fica na área da 5ª DP, a mesma do Centro. A taxa da delegacia reflete "
               "o movimento do Centro, não o da ilha",
    "Cidade Universitária": "a Cidade Universitária é uma ilha separada do resto da área da 37ª DP (Ilha do "
                            "Governador), e seus moradores são menos de 1% dos moradores da delegacia",
}

# ---------------------------------------------------------------------------
# Areas com muita gente de fora (decisao do usuario, 27/11/2026): SO AVISO, a nota nao muda.
# CISPs cuja taxa de roubo de rua passa de FATOR x a mediana dos bairros. O aviso vai para o
# bairro com pelo menos PCT_MORADORES_MIN dos moradores nessas CISPs.
# Hoje pega as CISPs 1, 4, 5 e 18 (Centro, Lapa, Gamboa, Santo Cristo, Saude, Maracana, Praca da Bandeira).
# ---------------------------------------------------------------------------
PUBLICO_DE_FORA = {"indicador": "roubo_rua_100k", "fator_mediana": 3, "pct_moradores_min": 0.5}
PUBLICO_DE_FORA_AVISO = ("Área com muita gente de fora (comércio e trabalho). A taxa usa só os moradores na conta, "
                         "então pode parecer maior do que o risco para quem mora ali.")
