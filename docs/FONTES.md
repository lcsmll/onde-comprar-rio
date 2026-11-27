# Fontes de dados: Etapa 1 (descoberta)

Checagem feita em **25/11/2026**. Para cada fonte foi baixada uma amostra (ou o arquivo inteiro, quando era pequeno), que está em `data_raw/`.
"Atualização" é a data que o próprio portal informa. Quando o portal não informa nada, está escrito "não informada".

Legenda de status:
- **OK**: dá para usar como está.
- **OK com ressalva**: dá para usar, mas tem um problema que precisa de uma regra (explicada).
- **DECISÃO**: preciso que você escolha antes da Etapa 2.
- **FALTA**: não consegui obter de fonte oficial.

---

## 0. Base territorial (usada por todos os critérios)

| Item | Link | Formato | Período / atualização | Detalhe | Status |
|---|---|---|---|---|---|
| Limite de bairros (IPP/Prefeitura) | https://www.data.rio/datasets/PCRJ::limite-de-bairros · API: `pgeo3.rio.rj.gov.br/arcgis/rest/services/Cartografia/Limites_administrativos/MapServer/4` | Feature Service (baixado como GeoJSON) | Item atualizado em 06/12/2023 | 167 bairros (polígonos) | OK |
| População por bairro, Censo 2022 (resultado do universo, agregado pelo IPP) | Data.Rio item `1df0079668254699b83a56dac4d8ed56` ("População residente, segundo os Bairros... Censo 2022") | CSV (zip) | Censo 2022; publicado em 21/10/2025 | Bairro | OK |
| População por setor censitário, Censo 2022 | Data.Rio "Camada Censo Demográfico 2022 - Setores" · `Hosted/Mapa_Rio_Camada_Censo_Demográfico_Setores/FeatureServer/0` | Feature Service | Censo 2022; camada editada em 21/08/2026 | 13.782 setores, com bairro e população | OK |

**Os 15 bairros do MVP existem com estes nomes exatos:** Méier, Cachambi, Tijuca, Vila Isabel, Grajaú, Madureira, Irajá, Penha, Vila da Penha, Praça Seca, Tanque, Taquara, Freguesia (Jacarepaguá), Pechincha, Vila Valqueire.
Cuidados: "Penha" é diferente de "Penha Circular", e "Freguesia (Jacarepaguá)" é diferente de "Freguesia (Ilha)". O ETL vai usar o **código do bairro** (`codbairro`), não o nome, para não confundir.

A soma da população por setor dá 6.211.223 habitantes, o que bate com o Censo 2022 do município.

**Por que a camada de setores é importante:** ela permite calcular a população de qualquer recorte (área de delegacia, mancha de inundação, faixa de ruído). Com ela não precisamos de estimativas.

---

## 1. Violência: ISP-RJ

| Item | Link | Formato | Período / atualização | Detalhe |
|---|---|---|---|---|
| Ocorrências mensais por delegacia | https://www.ispdados.rj.gov.br/Arquivos/BaseDPEvolucaoMensalCisp.csv | CSV (`;`, latin1) | jan/2003 a **out/2026** | CISP (área de delegacia), 60 indicadores |
| Limites das CISPs | https://www.ispdados.rj.gov.br/Arquivos/CISPshp.rar (página: https://www.ispdados.rj.gov.br/Conteudo.html) | Shapefile (rar) | Limites de 2026 (arquivo de out/2026) | 137 polígonos no estado, 42 na capital |
| Histórico de mudanças de CISP | https://www.ispdados.rj.gov.br/Arquivos/DesmembramentoDeCispEMudancaDeAisp.csv | CSV | Última mudança na capital: jul/2017 | |
| População por CISP (do ISP) | https://www.ispdados.rj.gov.br/Arquivos/PopulacaoEvolucaoMensalCisp.csv | CSV | **Só até jul/2022** | CISP |

Indicadores úteis no arquivo: `letalidade_violenta`, `roubo_rua` (soma de roubo a transeunte, de celular e em coletivo), `roubo_veiculo`, `total_roubos`, `total_furtos`, `roubo_residencia`.
A coluna `fase` indica se o mês ainda é provisório: de jan a jun/2026 é 3 (consolidado), de jul a out/2026 é 2 (ainda pode mudar).

### De-para delegacia x bairro (já testado)

Regra proposta: cruzar o polígono do bairro com o polígono da CISP e ver que fração do bairro cai em cada CISP.
Quando o bairro está dividido entre CISPs, a taxa do bairro é a **média ponderada pela população** que mora em cada pedaço (calculada com os setores do Censo 2022).

Resultado do cruzamento (% da área do bairro em cada CISP, só fatias de 1% ou mais):

| Bairro | CISP |
|---|---|
| Méier | 26 (66%), 23 (33%) |
| Cachambi | 23 (96%), 25 (3%), 44 (1%) |
| Tijuca | 19 (86%), 18 (12%), 20 (1%) |
| Vila Isabel | 20 (98%), 25 (2%) |
| Grajaú | 20 (99%) |
| Madureira | 29 (99%) |
| Irajá | 27 (98%), 40 (1%) |
| Penha | 22 (99%) |
| Vila da Penha | 27 (90%), 38 (10%) |
| Praça Seca | 28 (100%) |
| Tanque | 41 (67%), 28 (32%), 32 (1%) |
| Taquara | 32 (97%), 41 (2%), 28 (1%) |
| Freguesia (Jacarepaguá) | 41 (97%), 32 (3%) |
| Pechincha | 41 (100%) |
| Vila Valqueire | 28 (97%), 30 (3%) |

Teste de taxa por 100 mil habitantes (nov/2025 a out/2026, população do Censo 2022 somada por CISP):

| CISP | População 2022 | Letalidade violenta /100 mil | Roubos de rua /100 mil |
|---|---|---|---|
| 19 (Tijuca) | 121.310 | 8,2 | 848 |
| 20 (Grajaú/Vila Isabel) | 132.918 | 15,0 | 634 |
| 22 (Penha) | 190.319 | 18,9 | 367 |
| 23 (Méier/Cachambi) | 72.827 | 19,2 | 879 |
| 26 (Méier) | 101.289 | 11,8 | 752 |
| 27 (Irajá/Vila da Penha) | 166.631 | 33,6 | 908 |
| 28 (Praça Seca/Valqueire) | 109.335 | 18,3 | 406 |
| 29 (Madureira) | 144.441 | 43,6 | 1.230 |
| 32 (Taquara) | 445.878 | 40,4 | 409 |
| 41 (Tanque/Pechincha/Freguesia) | 138.857 | 16,6 | 325 |

### Problemas e sugestões

1. **Bairros que dividem a mesma delegacia têm a mesma nota.** Pechincha e Freguesia caem quase inteiros na CISP 41, e Praça Seca e Vila Valqueire na CISP 28. Não existe dado oficial abaixo do nível de delegacia. Sugestão: aceitar isso e **mostrar na tela** que o número é da área da delegacia X, que cobre os bairros A, B e C.
2. **A CISP 32 (Taquara) é enorme** (446 mil habitantes, incluindo Cidade de Deus, Curicica e parte de Jacarepaguá). A taxa da Taquara reflete essa área toda. Mesma sugestão: deixar isso explícito.
3. **Taxa por morador distorce áreas comerciais.** Exemplo: CISP 18 (Praça da Bandeira/parte da Tijuca) tem 2.346 roubos de rua por 100 mil, porque muita gente passa por lá sem morar. Para o MVP só afeta a ponta da Tijuca. Sugestão: dar mais peso à **letalidade violenta** e a **roubo a residência e veículo** (que acontecem onde se mora) do que a roubo de rua. Defino o peso de cada um na Etapa 2.
4. **População do ISP só vai até 2022.** Resolvido: usamos a população do Censo 2022 por setor somada dentro de cada CISP.
5. **Meses recentes são provisórios.** Sugestão: usar os últimos 12 meses fechados e mostrar o período na tela.
6. **A taxa da delegacia nem sempre representa o bairro (27/11/2026).** A taxa é crimes ÷ moradores da CISP inteira. (a) Bairro separado do resto da delegacia ou com poucos moradores perto do total dela herda a taxa dos outros bairros: Paquetá, uma ilha na CISP 5, ficava com o roubo de rua do Centro (6.850 por 100 mil). (b) Em áreas de comércio e trabalho, os crimes contra quem circula entram na conta como se fossem dos moradores: CISP 1 (Praça Mauá, 1.070 moradores, roubo de rua de 89.626 por 100 mil), CISP 5 (Centro e Lapa, 6.850), CISP 4 (Gamboa, Santo Cristo e Saúde, 2.655) e CISP 18 (Maracanã e Praça da Bandeira, 2.346), contra mediana de 605 nos bairros. Tratamento: (a) 20 bairros sem nota de Segurança (`BAIRROS_SEGURANCA_INSUFICIENTE`); (b) aviso na tela, sem mudar a nota (`PUBLICO_DE_FORA`). Ver `ESCOPO.md`, seção 24.

---

## 2. Alagamento

| Item | Link | Formato | Período / atualização | Detalhe | Status |
|---|---|---|---|---|---|
| ISMFI: Índice de Suscetibilidade do Meio Físico a Inundações (COPPE/UFRJ, Estratégia de Adaptação Climática da Prefeitura) | `pgeo3.rio.rj.gov.br/arcgis/rest/services/Estudos/ISMFI_Indice_de_Suscetibilidade_do_Meio_Fisico_a_Inundacoes/MapServer/0` (setores) e `/1` (grade de 200 m) | Feature Service | Estudo de 2016, sobre setores do Censo 2010. Atualização não informada | 10.504 setores, índice de 0 a 97 | OK com ressalva |
| Ocorrências do COR (inclui "bolsão d'água" e alagamento, com bairro) | Data.Rio item `4b21231ce02243e99b5f080b8a0ff821`. Tabela BigQuery `datario.adm_cor_comando.ocorrencias` | **Só BigQuery** | Desde 2015, atualização diária | Ocorrência com bairro | DECISÃO |
| Impacto dos Perigos Climáticos, camada Inundações (Plano de Desenvolvimento Sustentável) | `Estudos/Impacto_dos_Perigos_Climáticos_PDS/MapServer/2` | Raster (imagem) | Não informada | Pixel | Não recomendo (é imagem, difícil de converter em nota) |
| Pontos de alagamento do Alerta Rio / Rio-Águas | Não encontrei como dado aberto no Data.Rio | | | | FALTA |

O ISMFI combina 4 fatores: impermeabilização do solo, declividade, altitude e proximidade de rio ou canal. Ele mede **suscetibilidade física** (onde a água tende a acumular), não enchentes que aconteceram.

Teste da nota por bairro. A média ponderada pela área e a ponderada pela população dão resultados bem diferentes:

| Bairro | ISMFI médio por área | ISMFI médio por população |
|---|---|---|
| Praça Seca | 10,9 | 15,0 |
| Tanque | 6,9 | 17,2 |
| Pechincha | 9,1 | 17,7 |
| Freguesia (Jpa) | 13,2 | 25,4 |
| Vila Valqueire | 17,1 | 26,4 |
| Cachambi | 29,1 | 29,9 |
| Penha | 48,6 | 31,9 |
| Madureira | 34,2 | 34,1 |
| Irajá | 38,0 | 34,3 |
| Méier | 34,6 | 37,0 |
| Taquara | 29,4 | 37,9 |
| Grajaú | 11,6 | 40,4 |
| Tijuca | 22,3 | 40,8 |
| Vila da Penha | 42,0 | 44,0 |
| Vila Isabel | 38,0 | 44,3 |

### Problemas e sugestões

1. **Média por área engana.** Tijuca e Grajaú incluem pedaços do Maciço da Tijuca (morro e floresta, índice zero), o que "limpa" artificialmente a nota. Sugestão: **ponderar pela população**, o que responde "a média dos moradores deste bairro mora em área com que suscetibilidade?".
2. **O ISMFI é de 2016 e usa setores de 2010.** Obras de drenagem posteriores não aparecem. Sugestão: mostrar "estudo de 2016" na tela.
3. **Falta o dado de eventos reais.** As ocorrências de alagamento do COR seriam o complemento ideal (onde de fato alagou nos últimos anos), mas só estão no BigQuery. Ver a Decisão A no fim.

---

## 3. Escolas: INEP

| Item | Link | Formato | Período / atualização | Detalhe | Status |
|---|---|---|---|---|---|
| Censo Escolar 2025 (microdados) | https://download.inep.gov.br/dados_abertos/microdados_censo_escolar_2025_.zip (página: https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-escolar) | ZIP com CSV (537 MB) | Ano 2025, publicado em 31/07/2026 | Escola, **sem endereço** | OK com ressalva |
| IDEB 2025 por escola (anos iniciais, anos finais e ensino médio) | https://download.inep.gov.br/ideb/resultados/divulgacao_anos_iniciais_escolas_2025.zip (mais `_anos_finais_` e `_ensino_medio_`) | ZIP com XLSX | IDEB 2025, divulgado em 05/08/2026 | Escola | OK com ressalva |
| Catálogo de Escolas do INEP (tem latitude e longitude) | https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/inep-data/catalogo-de-escolas (painel Oracle BI) | Exportação manual para CSV pelo painel | Anual | Escola com coordenadas | DECISÃO |
| Escolas municipais com coordenadas (SME) | `pgeo3.rio.rj.gov.br/arcgis/rest/services/Educacao/SME/MapServer/1` | Feature Service | Item atualizado em 10/11/2026 | 1.590 pontos (inclui creches e bibliotecas) | OK (só rede municipal) |

Números do município do Rio no Censo Escolar 2025: 3.897 escolas em funcionamento, sendo 1.983 privadas, 1.577 municipais, 311 estaduais e 26 federais.
Escolas do Rio com IDEB 2025: 904 nos anos iniciais (880 municipais), 523 nos anos finais e 302 no ensino médio (257 estaduais e só 33 privadas).

### Problemas e sugestões

1. **Os microdados de 2025 não têm endereço, CEP nem bairro.** O INEP passou a publicar a versão "simplificada". Sem coordenada não dá para saber em que bairro cada escola fica. Opções:
   - (a) **Catálogo de Escolas do INEP**: é oficial e tem latitude e longitude de todas as escolas, públicas e privadas. Mas não há link direto: alguém precisa exportar o CSV do município do Rio uma vez pelo painel. Posso tentar fazer isso pelo navegador (Chrome), ou você exporta e coloca em `data_raw/inep/`. **Recomendo esta.**
   - (b) Usar só a camada da SME (rede municipal). Isso deixaria de fora particulares e estaduais.
2. **Não existe nota oficial de qualidade para escola particular.** O IDEB por escola é quase só da rede pública. No Rio, só 33 particulares têm IDEB, e só no ensino médio. O ENEM por escola deixou de ser publicado em 2015. Sugestão: para particulares, usar só **quantidade** (escolas por mil crianças e jovens). Para públicas, usar quantidade e IDEB. O site vai deixar claro que não há indicador oficial de qualidade das particulares.
3. **Certificado do servidor do INEP.** O `download.inep.gov.br` envia a cadeia de certificados incompleta, e por isso o download falha. Resolvi de forma segura: baixei o certificado intermediário que falta do endereço indicado no próprio certificado (GlobalSign/RNP) e mantive a verificação ligada. O arquivo está em `etl/ca_inep.pem`.

---

## 4. Transporte: Data.Rio

| Item | Link (API pgeo3) | Formato | Atualização | Quantidade |
|---|---|---|---|---|
| Estações de metrô | `Transporte_Trafego/Transporte_publico/MapServer/19` | Pontos | Item de 19/07/2024 | 41 (todas ativas) |
| Linhas de metrô | `.../MapServer/18` | Linhas | idem | 3 |
| Estações de trem (SuperVia) | `.../MapServer/16` | Pontos | Item de 06/09/2023 | 104 (60 no município) |
| Linhas de trem | `.../MapServer/15` | Linhas | idem | 8 ramais |
| Paradas do VLT | `.../MapServer/9` | Pontos | Item de 16/04/2026 | 31 |
| Estações de BRT | `Hosted/Estações_BRT/FeatureServer/0` | Pontos | Camada editada em 11/09/2026 | 156 (Transoeste 66, Transcarioca 49, Transbrasil 22, Transolímpica 19) |
| Trajetos de BRT | `Hosted/Trajetos_BRT/FeatureServer/1` | Linhas | 18/07/2024 | 5 |

Regra proposta: (1) distância a pé, em linha reta, de cada setor censitário até a estação mais próxima, com média ponderada pela população do bairro; (2) número de estações dentro do bairro ou a até 1 km da borda.

### Problemas e sugestões

1. **Linha reta não é caminho real.** Para o MVP é aceitável e fácil de explicar. Pode ser melhorado depois.
2. **Ônibus comum fica de fora.** O pedido fala de metrô, trem, BRT e VLT. A Prefeitura publica o GTFS dos ônibus, mas eu deixaria para uma versão futura.
3. **Teleférico e barcas** também estão na camada, mas não afetam os 15 bairros.

---

## 5. Emprego

| Item | Link | Formato | Período | Detalhe | Status |
|---|---|---|---|---|---|
| Distância até o Centro e a Barra | Calculada com a malha de bairros e os setores (acima) | Cálculo | | | OK |
| Hierarquia de Centros e Subcentros (Plano Diretor, PLC 44/2021) | Data.Rio item `6e75e927a26345858d0dc617e0e0c3f6` (`Hosted/PLC44_2021_ANEXO_XII___Hierarquia_de_Centros_e_Subcentros`) | Feature Service | Plano Diretor de 2021 | Polígonos dos centros | OK, para definir os polos |
| Vínculos formais (RAIS) por bairro | Data.Rio item `cc9673bd14694b8f9330756f387b899b` (`services1.arcgis.com/OlP4dGNtIcnD3RYf/arcgis/rest/services/RAIS_open/FeatureServer`) | Feature Service | **Só 2013 a 2016** | Bairro x atividade | OK com ressalva |
| Tempo de deslocamento casa-trabalho, Censo 2022 (SIDRA 10331) | Data.Rio item `82c3824d7baa4c4b8244358b7abb90a4` | CSV | Censo 2022 (amostra preliminar) | **Só o total do município** | Não serve |

Sugestão para o MVP:
- **Distância em linha reta** (ponderada pela população) até dois polos: **Centro** (ponto de referência: Candelária/Av. Rio Branco) e **Barra** (centro da Barra da Tijuca). Prefiro a distância ao polo mais próximo, ou uma combinação com mais peso para o Centro. Isso fica para a Etapa 2.
- RAIS 2016 por bairro: serve para mostrar que o Centro e a Barra concentram os empregos, mas está velha. Não usaria na nota.

### Problemas
1. **A RAIS mais recente por bairro não é pública.** A RAIS identificada precisa de convênio, e a pública só chega ao nível de município. O Data.Rio parou em 2016.
2. **O tempo de deslocamento do Censo 2022** só saiu para o município inteiro. Quando o IBGE publicar os resultados por área de ponderação, dá para trocar a distância por um tempo real.

---

## 6. Barulho (índice composto)

### Mapa oficial de ruído (Lei 7.479/2022)
**Não publicado.** Não achei o mapa no Data.Rio (busquei por "ruído", "sonora" e "mapa de ruído"), nem no servidor de mapas da Prefeitura, nem em notícias oficiais.
A lei dá até 3 anos para a AP1 (prazo que já passou, em torno de jul/2025), 4 anos para as AP2 e AP3 e 5 anos para o resto da cidade.
O campo `ruido_db_oficial` ficará vazio no JSON.
Fontes: [Câmara Municipal: lei sancionada](https://www.camara.rio/comunicacao/noticias/1189-agora-e-lei-municipio-tera-cinco-anos-para-elaborar-mapa-de-ruido-urbano) · [texto da Lei 7.479/2022](https://aplicnt.camara.rj.gov.br/APL/Legislativos/contlei.nsf/2ed241833abd7a5b8325787100687ecc/f43585d523e509a10325888d004b7182).

| Componente | Link | Formato | Atualização | Detalhe | Status |
|---|---|---|---|---|---|
| Reclamações ao 1746 (perturbação do sossego / poluição sonora) | Data.Rio item `52b6bd003abf4b8995ec9860e65a82c5`. Tabela BigQuery `datario.adm_central_atendimento_1746.chamado` | **Só BigQuery** (o link de CSV do catálogo dá erro 404) | Desde 2011, atualização diária | Chamado com bairro (`id_bairro`) e tipo | DECISÃO |
| Hierarquia viária | `CadLog/Trechos_Logradouros/MapServer/0` | Linhas | Item de 21/10/2025 | Campo `hierarquia`: Estrutural, Arterial primária, Arterial secundária, Coletora, Local | OK |
| Linhas de trem, metrô e BRT | Ver Transporte | Linhas | | Metrô: 2 estações de superfície marcadas | OK |
| **Zoneamento de ruído dos aeroportos (PEZR)** | `pgeo3.rio.rj.gov.br/arcgis/rest/services/Urbanismo/IU_PEZRs/MapServer/301` | Polígonos | Editado em 03/11/2025 | Galeão, Santos Dumont e Jacarepaguá, em faixas de 65-70, 70-75, 75-80, 80-85 e acima de 85 dB | OK |
| Zoneamento urbano vigente | `Urbanismo/LBB_Zoneamento_urbano_vigente/MapServer/0` | Polígonos | Editado em 2025 | Zonas (ZRM, ZCS etc.), que servem de referência para o limite legal | OK (só referência) |

Sobre a ANAC: os Planos de Zoneamento de Ruído são aprovados pela ANAC, mas o que achei aberto e em mapa foi a camada da **Prefeitura** com os PEZRs (os números na coluna `legislacao`, como 25.2017 e 25.2018, parecem ser as portarias de aprovação). É dado oficial e já vem em dB. Nenhum dos 15 bairros do MVP deve cair nas faixas dos aeroportos. O mais próximo é a área de Jacarepaguá (Taquara/Freguesia), e isso será confirmado no ETL.

Sugestão de índice (detalho na Etapa 2):
- reclamações ao 1746 de barulho por 1.000 habitantes (se a Decisão A for "sim");
- km de vias estruturais e arteriais por km² de área urbana do bairro;
- % da população a até 100 m de linha de trem, metrô de superfície ou BRT;
- % da população dentro de faixa PEZR de 65 dB ou mais.

O limite legal por zona (NBR 10.151 e lei municipal) entra só como texto de referência na tela, não na nota.

---

## 7. Financiamento (parâmetros para `parametros_financiamento.json`)

| Item | Fonte oficial | O que diz | Data |
|---|---|---|---|
| MCMV: faixas, tetos e juros | https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/habitacao/programa-minha-casa-minha-vida/mcmv-fgts | Faixas 1 e 2 até R$ 5.000; Faixa 3 até R$ 9.600; Classe Média até R$ 13.000. Teto: Faixas 1-2 de R$ 210 mil a R$ 275 mil conforme o município; Faixa 3 até R$ 400 mil; Classe Média até R$ 600 mil. Prazo máximo de 35 anos. Subsídio de até R$ 55 mil (fora do Norte). | Página atualizada em 28/10/2026 |
| MCMV: juros, Sudeste (Rio), cotista / não cotista do FGTS | mesma página | Faixa 1: até R$ 2.160: 4,25% / 4,75%; R$ 2.160,01 a 2.850: 4,50% / 5,00%; R$ 2.850,01 a 3.200: 4,75% / 5,25%. Faixa 2: R$ 3.200,01 a 3.500: 5,00% / 5,50%; R$ 3.500,01 a 4.000: 5,50% / 6,00%; R$ 4.000,01 a 5.000: 6,50% / 7,00%. Faixa 3: 7,66% / 8,16%. Classe Média: 10,00%. Pró-Cotista: 8,66%. | idem |
| MCMV: teto do município do Rio | https://www.caixa.gov.br/Downloads/fgts-tabela-municipios/TABELA_MUNICIPIOS_VIGENCIA_01JAN2026.xlsx | Rio: recorte A, grupo 1. Faixas 1-2: R$ 275.000. Faixa 3: R$ 350.000. Classe Média: R$ 500.000 (renda até R$ 12.000, Res. CCFGTS 1.116/2025). | Vigência a partir de 01/01/2026 |
| Juros de mercado por banco (para o SBPE) | API do Banco Central: https://olinda.bcb.gov.br/olinda/servico/taxaJuros/versao/v2/odata/ | Out/2026, Caixa: 11,97% a.a. (taxa de mercado, pós-fixada em TR) e 7,87% a.a. (taxas reguladas, TR). É a **média das operações contratadas**, não a taxa de balcão. | Mensal, último mês: out/2026 |
| ITBI do Rio | https://carioca.rio/servicos/itbi-simulacao-de-valor-e-pedido-de-guia/ | **3%** desde 01/01/2018 (Lei 6.250/2017). Base de cálculo: valor venal (valor de mercado). A página não cita nenhuma alíquota reduzida para a parte financiada. | Página atualizada em 05/02/2026 |
| Desconto de 50% nos emolumentos do primeiro imóvel financiado pelo SFH | Lei 6.015/1973, art. 290 (https://www.planalto.gov.br/ccivil_03/leis/l6015compilada.htm) | 50% de redução para a "primeira aquisição imobiliária para fins residenciais, financiada pelo SFH" | Lei federal |
| Cota máxima SBPE (Caixa) | CAIXA Notícias, 10/10/2025 e 09/12/2025: https://caixanoticias.caixa.gov.br/Paginas/Not%C3%ADcias/2025/12-DEZEMBRO/CAIXA-volta-a-permitir-mais-de-um-financiamento--imobiliario-pelo-SBPE.aspx | "a CAIXA voltou a financiar até 80% do valor do imóvel na modalidade SAC e até 70% na modalidade Price". Em vigor desde 13/10/2025. | Consultado em 27/11/2026 |
| Cota máxima MCMV (FGTS, pessoa física) | IN 48/2022 do Ministério das Cidades, art. 34, compilada em 09/04/2026: https://www.gov.br/cidades/pt-br/acesso-a-informacao/institucional/base-juridica/instrucoes-normativas/IN_48_de_19.12.22__compilada_em_09.04.2026_.pdf | Contrapartida mínima de 20% do valor de venda ou investimento; "poderá ter seu percentual reduzido para até 10%" no SAC | Consultado em 27/11/2026 |
| Cota de imóvel usado (FGTS, Sul e Sudeste) | IN 30/2024 compilada (orçamento do FGTS de 2025), arts. 3º, 4º e 5º-A: https://www.gov.br/cidades/pt-br/acesso-a-informacao/institucional/base-juridica/instrucoes-normativas/20251118_INSTRUO_NORMATIVA_N._30__COMPILADA.pdf | 65% (renda de R$ 4.700,01 a R$ 8.600), 50% (Pró-Cotista, renda até R$ 12 mil), 60% (Classe Média) | Orçamento de 2025; a norma de 2026 não foi encontrada |
| Cota máxima Pró-Cotista | FGTS, Financiamentos: https://www.fgts.gov.br/Paginas/subpaginas/financiamentos.aspx | Price: 80% e SAC: 90% do valor de avaliação | Página sem data; consultada em 27/11/2026 |
| Tabela de emolumentos de cartório (RJ 2026) | TJRJ / Corregedoria | **Não consegui acessar** (a página antiga dá 404 e a nova não foi localizada) | FALTA |
| Tarifa de avaliação do imóvel (Caixa) | caixa.gov.br | **Não consegui acessar** (o site da Caixa entra em loop de redirecionamento) | FALTA |

### Problemas e sugestões

1. **As duas fontes oficiais do MCMV não batem.** A página do Ministério (atualizada em out/2026) traz renda até R$ 13 mil e tetos de R$ 400 mil e R$ 600 mil. A planilha da Caixa (vigência jan/2026) ainda traz R$ 12 mil, R$ 350 mil e R$ 500 mil, citando a Res. CCFGTS 1.116/2025. Parece que houve uma alteração em 2026 que a planilha da Caixa ainda não reflete, mas **não achei o número da nova resolução**. Sugestão: usar os valores do Ministério (mais recentes) para faixa, teto e juros; usar a planilha da Caixa só para o teto das Faixas 1-2 no Rio (R$ 275 mil, que coincide com o máximo citado pelo Ministério); e registrar as duas fontes no JSON. Ver a Decisão C.
2. **Não existe "taxa de balcão" oficial do SBPE em formato aberto.** O Banco Central publica a média real por banco, que é oficial, gratuita, mensal e tem API. Sugestão: usar a taxa da Caixa nessa série como padrão e deixar o usuário editar o campo no simulador.
3. **Cartório e avaliação:** não vou inventar valores. Opções: (a) tento de novo na Etapa 3 (pelo navegador, se você autorizar); (b) você me passa o PDF da tabela do TJRJ; (c) o simulador mostra esses custos como "consulte o cartório", sem valor. Ver a Decisão D.
4. **Cota máxima de financiamento (27/11/2026).** Ver as linhas de cota na tabela acima e a seção 23 do `ESCOPO.md`. Ressalvas: (a) a cota do SBPE é a da Caixa; outros bancos podem ter outra; (b) a regra de imóvel usado do FGTS é do orçamento de 2025, e a de 2026 não foi achada; (c) notícias citavam 80% no SAC e 60% na Price para o Pró-Cotista, mas a página oficial do FGTS diz 90% e 80%, e o app segue a oficial.

---

## 8. Preço dos imóveis: ITBI (achado na Etapa 2)

| Item | Link | Formato | Período / atualização | Detalhe | Status |
|---|---|---|---|---|---|
| ITBI: transações por bairro e mês, imóveis residenciais (Secretaria de Fazenda) | Data.Rio item `0965968f12424f8792b240568616e6aa` · `pgeo3.rio.rj.gov.br/arcgis/rest/services/Fazenda/ITBI/MapServer/5` (por ano: `/1`; por logradouro: `/4` e `/8`) | Feature Service | Mensal, até 2026; o último mês não é publicado. Item atualizado em nov/2026 | Bairro x mês: nº de transações, área construída média, valor médio da transação e do imóvel | OK com ressalva |

Só entram compra e venda e promessa de compra e venda (a Prefeitura diz que isso é mais de 95% das transações).
Ressalvas:
1. Não separa casa de apartamento nem traz quartos.
2. São médias, não medianas.
3. O valor é o declarado para o ITBI.

Valores de 2026 (até out) para os 15 bairros, com R$/m² calculado como valor médio / área média:

| Bairro | Transações 2026 | Valor médio (R$) | Área média (m²) | R$/m² |
|---|---|---|---|---|
| Tijuca | 1.572 | 587.310 | 92 | 6.354 |
| Freguesia (Jpa) | 671 | 550.731 | 107 | 5.155 |
| Grajaú | 320 | 449.714 | 92 | 4.866 |
| Vila Isabel | 546 | 392.478 | 83 | 4.756 |
| Cachambi | 351 | 336.230 | 73 | 4.626 |
| Vila da Penha | 152 | 372.256 | 88 | 4.239 |
| Taquara | 515 | 367.747 | 88 | 4.162 |
| Méier | 391 | 350.544 | 85 | 4.116 |
| Pechincha | 367 | 335.369 | 84 | 4.005 |
| Vila Valqueire | 182 | 467.651 | 120 | 3.895 |
| Irajá | 326 | 248.814 | 68 | 3.652 |
| Penha | 214 | 239.307 | 69 | 3.481 |
| Tanque | 94 | 265.531 | 88 | 3.004 |
| Madureira | 124 | 199.769 | 70 | 2.866 |
| Praça Seca | 226 | 202.201 | 83 | 2.435 |

## 9. Limite de Favelas 2022 (usado para a subnotificação)

| Item | Link | Formato | Atualização | Uso |
|---|---|---|---|---|
| Limite de Favelas 2022 (IPP) | `pgeo3.rio.rj.gov.br/arcgis/rest/services/SABREN/Limites_de_Favelas/FeatureServer/13` (Data.Rio item `211856b90ba64e3fb6fc0941f5dbda47`) | Feature Service (1.072 polígonos) | 2022 | % dos moradores de cada bairro em área de favela (fração da área de cada setor do Censo dentro dos limites). Bairros com 50% ou mais ficam sem nota de Segurança e Menos barulho (ver ESCOPO, seção 21). |

## Decisões tomadas (25/11/2026)

| Decisão | Escolha | Consequência |
|---|---|---|
| A. BigQuery (1746 e COR) | **Sim** | **Feito e testado.** Ver "BigQuery: resultado do teste" abaixo. O índice de barulho inclui reclamações ao 1746 por mil habitantes, e o alagamento inclui as ocorrências do COR (que vão só até abr/2024). Os scripts salvam só o agregado em `data_raw/bigquery/`. |
| B. Coordenadas das escolas | **Exportar o Catálogo de Escolas do INEP pelo navegador** | **Feito.** Ver "Catálogo de Escolas: resultado da exportação" abaixo. |
| C. MCMV | **Valores da página do Ministério das Cidades (atualizada em 28/10/2026)** | Faixas de renda até R$ 5.000 / 9.600 / 13.000; tetos de R$ 275 mil (Faixas 1-2 no Rio), R$ 400 mil (Faixa 3) e R$ 600 mil (Classe Média). O JSON registra também a divergência com a planilha da Caixa (jan/2026). |
| D. Cartório e avaliação | **Opção (c)** | O simulador lista esses custos como "consulte o cartório / o banco", sem valor. Só o ITBI (3%) é calculado. |

### BigQuery: resultado do teste (25/11/2026)

Acesso pelo projeto Google Cloud `imovel-rio` (modo sandbox, sem cartão). O login é feito uma vez com `~/google-cloud-sdk/bin/gcloud auth application-default login`. O script de teste é `etl/bq_teste.py`.

**1746: `datario.adm_central_atendimento_1746.chamado`**
- 20,5 milhões de chamados desde 2011, **atualizada diariamente** (última modificação: 25/11/2026).
- Tem `id_bairro` **e** `latitude`/`longitude`. Cerca de 70% dos chamados de barulho têm coordenada; para os demais, usar `id_bairro`, traduzido pela tabela `datario.dados_mestres.bairro`.
- Tipos que entram no índice de barulho (chamados de 2023 em diante):

| tipo | subtipo | categoria | chamados desde 2023 |
|---|---|---|---|
| Perturbação do sossego | Fiscalização de perturbação do sossego | Serviço | 72.198 |
| Perturbação do sossego | Fiscalização de perturbação do sossego | Reclamação | 6.940 |
| Perturbação do sossego | Fiscalização de carros de som | Serviço | 6.112 |
| Poluição | Fiscalização de poluição sonora | Serviço | 1.938 |
| Poluição | Fiscalização de poluição sonora | Reclamação | 412 |
| Perturbação do sossego | Fiscalização de carros de som | Reclamação | 201 |

- Ficam **de fora** as categorias Crítica, Sugestão, Elogio e Informações e o subtipo "Informações sobre Perturbação do Sossego". Esses chamados são sobre o serviço do 1746, não um pedido de fiscalização num endereço.
- Ressalva: o número de chamados mede **reclamação**, não decibéis. Bairros onde a população reclama mais (ou conhece mais o 1746) aparecem mais barulhentos. A tela vai dizer isso.
- Custo: a consulta por tipo lê cerca de 1,5 GB (a cota grátis é de 1 TB por mês).

**COR: `datario.adm_cor_comando.ocorrencias`**
- 91.406 ocorrências, **de fev/2015 a 02/04/2024**. A tabela não é atualizada desde 03/04/2024, ou seja, está parada há mais de 2 anos e meio.
- Tipos de evento (tabela `procedimento_operacional_padrao`) que entram em alagamento:

| id_pop | Evento | Ocorrências | Período |
|---|---|---|---|
| 5 | Bolsão d'água em via | 4.231 | 2015 a mar/2024 |
| 31 | Alagamento | 289 | 2018 a mar/2024 |
| 33 | Lâmina d'água | 185 | 2017 a mar/2024 |
| 6 | Alagamentos e enchentes | 172 | 2015 a out/2021 |
| 32 | Enchente | 5 | 2019 a 2020 |

- Quase todas têm coordenada (99,9%).
- Ressalvas:
  1. O COR monitora principalmente **vias de trânsito**, então o dado mostra onde a rua alagou e atrapalhou o tráfego, não necessariamente onde as casas alagam.
  2. Termina em abr/2024.
- Sugestão: usar como **complemento** do ISMFI (eventos de 2015 a 2024 por km² de área urbana do bairro), com o período mostrado na tela. O peso de cada parte fica para a Etapa 2.

### Catálogo de Escolas: resultado da exportação (25/11/2026)

- Arquivo: `data_raw/inep/catalogo/catalogo_escolas_rio_2026-11-25.csv` (UTF-8 com BOM, separado por vírgula, 3.999 linhas).
- Como foi obtido: painel https://anonymousdata.inep.gov.br/analytics/saw.dll?Portal&PortalPath=%2Fshared%2FCenso%20da%20Educa%C3%A7%C3%A3o%20B%C3%A1sica%2F_portal%2FCat%C3%A1logo%20de%20Escolas, com os filtros UF = RJ e Município = Rio de Janeiro, depois "Aplicar" e "Exportar". Não há link direto, então para atualizar é preciso repetir esses passos (vai para o README na Etapa 5).
- Colunas úteis: Código INEP, Restrição de Atendimento (situação), Dependência Administrativa, Categoria Escola Privada, Porte, Etapas e Modalidade, Endereço, **Latitude, Longitude**.
- Situação: 3.866 "em funcionamento e sem restrição", 102 paralisadas e 31 em outras situações (atividade complementar, atendimento especializado etc.). O ETL usa só as que estão em funcionamento.
- **3.075 têm coordenada** (todas caem dentro do município). **924 não têm**, sendo 801 privadas.
- Para as que não têm coordenada, o bairro sai do texto do endereço, que termina em "BAIRRO. CEP Rio de Janeiro - RJ.". Isso funcionou para 905 das 924. As 19 restantes são grafias diferentes ("FREGUESIA JACAREPAGUA" sem parênteses, "IRAJ.") e serão resolvidas com uma pequena tabela de apelidos no ETL.
- Ressalva: o bairro escrito no endereço é o bairro "popular" (postal), que nem sempre coincide com o limite oficial. Isso afeta só as escolas sem coordenada, e o ETL vai contar quantas foram localizadas por cada método.
- Ligação com o IDEB: pelo Código INEP (o mesmo `ID_ESCOLA` das planilhas do IDEB).

Escolas em funcionamento nos 15 bairros, só com coordenada (antes da recuperação pelo endereço):

| Bairro | Estadual | Federal | Municipal | Privada | Total |
|---|---|---|---|---|---|
| Cachambi | 2 | 0 | 8 | 8 | 18 |
| Freguesia (Jacarepaguá) | 4 | 0 | 8 | 23 | 35 |
| Grajaú | 1 | 0 | 8 | 12 | 21 |
| Irajá | 7 | 0 | 26 | 12 | 45 |
| Madureira | 6 | 0 | 13 | 11 | 30 |
| Méier | 5 | 0 | 7 | 30 | 42 |
| Pechincha | 2 | 0 | 3 | 10 | 15 |
| Penha | 6 | 0 | 17 | 11 | 34 |
| Praça Seca | 3 | 0 | 14 | 14 | 31 |
| Tanque | 2 | 0 | 6 | 8 | 16 |
| Taquara | 7 | 0 | 20 | 29 | 56 |
| Tijuca | 4 | 1 | 25 | 56 | 86 |
| Vila Isabel | 2 | 1 | 12 | 25 | 40 |
| Vila Valqueire | 1 | 0 | 7 | 9 | 17 |
| Vila da Penha | 0 | 0 | 2 | 13 | 15 |

A recuperação pelo endereço acrescenta principalmente particulares. Exemplos: Vila da Penha +19, Taquara +22, Tijuca +19, Madureira +18.

## Decisões que estavam pendentes (registro)

**A. BigQuery (1746 e COR).** As reclamações de barulho (1746) e as ocorrências de alagamento (COR) só existem na base pública da Prefeitura no Google BigQuery. É oficial e gratuito (cota grátis de 1 TB por mês, muito acima do que vamos usar), mas exige uma conta Google com um projeto no Google Cloud, e a primeira configuração é feita por você (`! gcloud auth login`). Os scripts rodariam uma consulta pequena e salvariam um CSV agregado por bairro em `data_raw/`.
- Sim: o índice de barulho ganha o componente "reclamações por habitante" e o alagamento ganha "ocorrências reais".
- Não: o barulho fica só com vias, trilhos e aeroportos, e o alagamento só com o ISMFI.

**B. Coordenadas das escolas.** Posso (1) tentar exportar o CSV do Catálogo de Escolas do INEP pelo navegador, (2) você exporta manualmente (passo a passo na Etapa 3), ou (3) usar só as escolas municipais da SME.

**C. Parâmetros do MCMV.** Uso os valores da página do Ministério (out/2026), com a ressalva de que a planilha da Caixa está diferente? Ou prefere que eu continue procurando a resolução do Conselho Curador do FGTS de 2026 antes de seguir?

**D. Custos de cartório e avaliação.** Qual das opções (a), (b) ou (c) acima?

---

## Arquivos baixados nesta etapa

```
data_raw/datario/   bairros, bairros_censo2022, setores_censo2022, metro/trem/vlt/brt,
                    aeroportos, ismfi_setores, pezr, escolas_municipais, zoneamento (amostra de 2.000),
                    censo/ (população 2022 por bairro e tempo de deslocamento)
data_raw/isp/       BaseDPEvolucaoMensalCisp.csv, PopulacaoEvolucaoMensalCisp.csv, CISP shapefile,
                    DesmembramentoDeCispEMudancaDeAisp.csv
data_raw/inep/      microdados Censo Escolar 2025, IDEB 2025 por escola (3 etapas), nota informativa
data_raw/caixa/     tabela de municípios MCMV (vigência jan/2026)
data_raw/bcb/       taxas de juros por banco, out/2026
```
Total de cerca de 1,1 GB, quase todo do INEP. A pasta `data_raw/` fica fora do git (`.gitignore`).
