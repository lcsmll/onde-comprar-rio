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
EXIBIR_TODOS = False
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
VIOLENCIA_INDICADORES = {
    # id: (colunas do ISP somadas, peso no criterio, rotulo)
    "letalidade_100k": (["letalidade_violenta"], 0.50, "Letalidade violenta"),
    "roubo_veiculo_100k": (["roubo_veiculo"], 0.20, "Roubo de veículo"),
    "roubo_rua_100k": (["roubo_rua"], 0.20, "Roubo de rua (transeunte, celular e coletivo)"),
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
TRANSPORTE_PESOS = {"dist_estacao_m": 0.70, "estacoes_1km": 0.30}

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
