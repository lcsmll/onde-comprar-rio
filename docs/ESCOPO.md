# Escopo: Etapa 2

**Aprovado em 25/11/2026, com todas as recomendações (A a H).** Baseado nas fontes de `docs/FONTES.md`.
Os marcadores **[DECIDIR]** abaixo ficaram como registro. Valem as respostas da tabela da seção 9: A retirar; B, C, D, E, F e G sim; H aprovado como está.
Pedido novo (anúncios de imóveis à venda e para alugar) está na seção 10, aguardando decisão.

---

## 1. Princípios

1. **Tudo roda no navegador.** O site é estático: lê `bairros.json` e `parametros_financiamento.json` e faz as contas no próprio aparelho. Nada do formulário é salvo ou enviado. Não há cookies, analytics nem backend.
2. **Toda nota mostra de onde veio:** número bruto, período, fonte e data de atualização.
3. **Linguagem neutra.** Nada de "bairro perigoso" ou "bairro ruim". O site diz, por exemplo, "16,6 mortes violentas por 100 mil habitantes na área da 41ª DP, nov/2025 a out/2026".
4. **Expansão sem reescrever.** O ETL já calcula os indicadores para **todos os 165 bairros** da cidade. O MVP só **exibe** os 15 bairros, que ficam numa lista (`etl/config.py`). Para abrir a cidade inteira, basta mudar essa lista.

---

## 2. Telas

Todas pensadas primeiro para o celular: uma coluna, botões grandes e nada que dependa de passar o mouse por cima.

| # | Tela | Conteúdo |
|---|---|---|
| 0 | Início | O que o app faz, em 3 linhas; aviso "nada do que você digitar sai do seu aparelho"; botão "Começar". |
| 1 | Perfil | 3 botões: Solteiro(a) / Casal sem filhos / Família com filhos. |
| 2 | Renda | Perguntas da seção 3.2. Pode pular ("só quero ver os bairros"). |
| 3 | Imóvel | Perguntas da seção 3.3. |
| 4 | Prioridades | 6 controles de 1 a 5, já preenchidos conforme o perfil, com o botão "voltar ao padrão do perfil". Uma linha explica cada critério. |
| 5 | Resultado | Lista de bairros em ordem de nota final. Cada cartão mostra a nota final, as 6 notas em barrinhas e o preço médio do m² (ITBI). Ao tocar, abre o detalhe: o motivo de cada nota, os números, a fonte e a data. Botão "Simular financiamento neste bairro". |
| 6 | Financiamento | Simulador da seção 6, já com o bairro escolhido. |
| 7 | Sobre os dados | Uma seção por fonte e por cálculo, gerada a partir do JSON (o texto fica junto do dado). Inclui as limitações conhecidas. |

O mapa (Leaflet) fica fora do MVP. O ETL já gera as geometrias simplificadas, para ele entrar depois sem mudar os dados.

Navegação: botões "voltar" e "avançar". O estado fica só na memória da página; ao fechar a aba, tudo some. **[DECIDIR]** Quer um botão "copiar link com minhas prioridades"? Ele colocaria só os pesos 1 a 5 e o perfil no link, **nunca** renda ou valores. Minha recomendação: sim, porque ajuda a compartilhar no WhatsApp sem expor nada pessoal.

---

## 3. Perguntas do formulário

### 3.1 Perfil
- Solteiro(a) / Casal sem filhos / Família com filhos

### 3.2 Renda (alimenta só o simulador)
| Pergunta | Tipo | Observação |
|---|---|---|
| A compra será com renda única ou somada? | 2 botões | Se somada, aparecem dois campos de renda. |
| Renda bruta mensal (comprador 1) | R$ | |
| Renda bruta mensal (comprador 2) | R$ | Só se for somada. |
| Tem FGTS? Quanto, somando os compradores? | Sim/Não + R$ | |
| Valor disponível para a entrada, sem contar o FGTS | R$ | |
| Algum comprador já tem imóvel no município do Rio ou financiamento ativo no SFH? | Sim/Não | Só para avisar sobre as regras do FGTS e do MCMV. Não bloqueia a simulação. |

### 3.3 Imóvel
| Pergunta | Uso |
|---|---|
| Casa ou apartamento | Só informativo (ver o problema abaixo). |
| Área mínima (m²) | Estima o preço no bairro: R$/m² do bairro x área. |
| Faixa de preço (até R$ ...) | Marca os bairros onde o preço estimado passa do seu limite. |
| Quartos, banheiros, vagas | Ver **[DECIDIR] A**. |

**Problema (dados de imóvel).** As fontes oficiais de preço (ITBI) informam valor médio e área média por bairro, mas **não separam casa de apartamento** e **não trazem quartos, banheiros nem vagas**. Por isso:

- **[DECIDIR] A: quartos, banheiros e vagas.**
  - (1) **Retirar do formulário (recomendo).** Perguntar e não usar daria a impressão de um filtro que não existe.
  - (2) Manter só como anotação, com o aviso "não afeta o resultado".
- **Casa ou apartamento:** mantenho a pergunta, mas mostro o aviso "o preço médio do bairro mistura casas e apartamentos".

### 3.4 Prioridades
Peso de 1 a 5 para cada critério. Ver os padrões na seção 5.

### 3.5 Opcional: onde você trabalha? (proposta)
**[DECIDIR] B.** O critério Emprego fica bem mais útil se a pessoa disser para onde vai todo dia. Proposta:
- Opções: Centro / Barra da Tijuca / Zona Sul (Botafogo e Copacabana) / outro bairro (lista) / home office ou não se aplica.
- Com casal, até duas respostas; o cálculo usa a média das distâncias.
- Se a pessoa não responder, vale o padrão da seção 4.5.

---

## 4. Regra de nota de cada critério

### 4.0 Regra comum (vale para os 6)

1. **Ponderado pela população.** O bairro é tratado como "a média dos seus moradores". Cada indicador é calculado em cada setor censitário (Censo 2022) e depois vira uma média ponderada pela população dos setores. Isso evita que um morro sem casas, ou um trecho de floresta, "melhore" ou "piore" o bairro.
2. **De indicador para nota 0 a 10, por posição na cidade.** Cada indicador é comparado com o dos **bairros da cidade inteira** com pelo menos 1.000 moradores (cerca de 155 bairros). A nota é o percentil:
   - `nota = 10 x (fração de bairros da cidade que estão PIOR que este)`
   - Exemplo: nota 8,0 quer dizer "melhor que 80% dos bairros do Rio neste indicador".
   - Por que percentil: é fácil de explicar, um valor extremo não distorce os demais, e a nota não muda quando o MVP ganhar mais bairros, porque a comparação já é com a cidade toda.
   - Empates (por exemplo, vários bairros com zero em ruído de aeroporto) recebem a mesma nota, pela média das posições.
3. **Critério com mais de um indicador:** nota do critério = média ponderada das notas dos indicadores, com os pesos indicados em cada seção.
4. **Motivo.** O detalhe mostra os indicadores brutos, a posição na cidade e a comparação com a mediana da cidade. Exemplo: "Letalidade violenta: 16,6 por 100 mil (mediana da cidade: X)".
5. **Bairro com menos de 1.000 moradores** não recebe nota e aparece como "dados insuficientes". Nenhum dos 15 do MVP cai nesse caso.

### 4.1 Violência (ISP)

| Indicador | Peso no critério | Cálculo |
|---|---|---|
| Letalidade violenta (homicídio doloso, latrocínio, lesão seguida de morte, morte por intervenção de agente do Estado) | 50% | Taxa por 100 mil habitantes |
| Roubo de veículo | 20% | Taxa por 100 mil |
| Roubo a residência | 10% | Taxa por 100 mil |
| Roubo de rua (a transeunte, de celular e em coletivo) | 20% | Taxa por 100 mil |

- **Período:** últimos 12 meses publicados (hoje, nov/2025 a out/2026). Os meses marcados como provisórios pelo ISP (`fase` 2) aparecem com aviso.
- **População da CISP:** soma dos setores do Censo 2022 cujo ponto interno cai na CISP.
- **Taxa do bairro:** cada setor herda a taxa da sua CISP; o bairro é a média ponderada pela população. Assim, um bairro dividido entre duas delegacias fica com a mistura correta.
- **Por que esses pesos:** a letalidade é o dado mais confiável (quase não há subnotificação) e o mais grave. Roubo de veículo e roubo a residência acontecem onde as pessoas moram. Roubo de rua pesa menos porque infla em áreas de comércio e passagem, como mostrou a CISP 18 na Etapa 1.
- **Aviso fixo na tela:** "O ISP publica por área de delegacia (CISP), não por bairro. Os bairros A, B e C dividem a mesma área e por isso têm números iguais."

### 4.2 Alagamento

| Indicador | Peso | Cálculo |
|---|---|---|
| Suscetibilidade física (ISMFI, COPPE/UFRJ 2016) | 70% | ISMFI do setor onde mora cada pessoa, ponderado pela população |
| Ocorrências de alagamento registradas pelo COR (bolsão d'água, alagamento, lâmina d'água, enchente), fev/2015 a abr/2024 | 30% | Ocorrências por km² de área ocupada do bairro (área dos setores com moradores) |

- **Por que 70/30:** o ISMFI cobre todo o território de forma homogênea. O COR registra o que de fato aconteceu, mas é viesado para as vias de trânsito monitoradas e parou em abr/2024.
- **Avisos:** "estudo de 2016, não considera obras de drenagem posteriores" e "registros do COR só até abr/2024".
- Os setores do ISMFI são de 2010 e os de população, de 2022. O cruzamento é feito pelo ponto interno de cada setor de 2022.

### 4.3 Escolas (INEP)

Só entram escolas **em funcionamento e sem restrição de atendimento** que ofereçam educação infantil, ensino fundamental ou ensino médio regular. A localização vem das coordenadas do Catálogo de Escolas; na falta delas, do bairro escrito no endereço (seção do `FONTES.md`).

| Indicador | Peso padrão | Cálculo |
|---|---|---|
| Oferta pública | 35% | Nº de escolas públicas a até 1,5 km de cada morador (média ponderada). As escolas localizadas só pelo bairro do endereço contam para os moradores do mesmo bairro. |
| Qualidade pública | 35% | Média do IDEB 2025 das escolas públicas a até 2 km (anos iniciais, anos finais e ensino médio; cada escola entra com a média das etapas que tem). |
| Oferta particular | 30% | Nº de escolas particulares a até 1,5 km. |

- **Não existe nota oficial de qualidade para escola particular.** Só 33 das cerca de 2.000 particulares do Rio têm IDEB. Por isso a particular entra só pela quantidade, e o site diz isso com todas as letras.
- **[DECIDIR] C: pergunta extra só para "família com filhos": "Que tipo de escola você procura?"**
  - Opções: pública / particular / tanto faz.
  - Efeito nos pesos (oferta pública / qualidade pública / oferta particular): pública = 50/50/0; particular = 0/0/100; tanto faz = 35/35/30.
  - Recomendo incluir.

### 4.4 Transporte (Data.Rio)

Estações consideradas: metrô, trem (só as do município), BRT e VLT.

| Indicador | Peso | Cálculo |
|---|---|---|
| Distância até a estação mais próxima | 70% | Linha reta do ponto interno de cada setor até a estação mais próxima; média ponderada pela população (em metros) |
| Estações perto de casa | 30% | Nº de estações a até 1 km de cada morador; média ponderada |

- **Aviso:** "distância em linha reta; o caminho a pé real costuma ser de 20% a 40% maior". Esse número não entra em conta nenhuma, só no texto; se você preferir, tiro.
- Ônibus comum fica fora do MVP.

### 4.5 Emprego

| Situação | Cálculo |
|---|---|
| Usuário informou onde trabalha (3.5) | Distância em linha reta, ponderada pela população, até o polo escolhido. Com dois polos, a média dos dois. |
| Não informou (padrão) | Média ponderada das distâncias até o **Centro** e a **Barra**. Os pesos saem da participação de cada polo nos empregos formais da RAIS 2016 por bairro (Data.Rio), calculada no ETL e mostrada na tela. |

- **Pontos de referência dos polos:** Centro = estação Carioca do metrô; Barra = Terminal Alvorada; Zona Sul = estação Botafogo do metrô; outro bairro = ponto interno do bairro. **[DECIDIR] D:** concorda com esses pontos?
- **Aviso:** "linha reta, não tempo de viagem. O tempo real depende do trânsito e do transporte."
- Quando o IBGE publicar o tempo de deslocamento do Censo 2022 por área de ponderação, troco a distância pelo tempo.

### 4.6 Barulho (índice composto, não é medição em dB)

| Indicador | Peso | Cálculo |
|---|---|---|
| Chamados ao 1746 de perturbação do sossego, carro de som e poluição sonora (categorias Serviço e Reclamação) | 40% | Por 1.000 habitantes, últimos 24 meses completos. Localização pela coordenada do chamado; sem coordenada, pelo `id_bairro`. |
| Proximidade de vias de tráfego pesado | 25% | % dos moradores a até 50 m de via **Estrutural** ou **Arterial primária** |
| Proximidade de trilhos e BRT | 20% | % dos moradores a até 100 m de linha de trem, trecho de superfície do metrô ou corredor de BRT |
| Ruído de aeroporto (PEZR oficial) | 15% | % dos moradores dentro de faixa de 65 dB ou mais de algum aeroporto |

- **"% dos moradores a até X m"** é calculado pelos setores: considera-se exposta a população de um setor proporcional à fração da área do setor dentro da faixa.
- **Avisos:** "índice composto, não é medição de decibéis"; "o número de chamados mede reclamação, que também depende do hábito de reclamar no bairro".
- `ruido_db_oficial`: `null` até a Prefeitura publicar o mapa da Lei 7.479/2022.
- **Limite legal por zona:** o texto de referência só entra se eu achar a tabela oficial do município. Se não achar, fica fora (sem inventar números).

### 4.7 Preço (informação e filtro, não é critério)

**[DECIDIR] E.** Fonte: ITBI da Prefeitura (Data.Rio, `Fazenda/ITBI/MapServer/5`, por bairro e mês, residencial, compra e venda e promessa). É dado oficial de **transações reais**.

- **Indicador:** R$/m² médio do bairro nos últimos 12 meses = soma dos valores dos imóveis / soma das áreas construídas. Junto, o número de transações.
- **Na tela:** "R$/m² médio declarado no ITBI (últimos 12 meses, N transações). Para um imóvel de [área mínima] m², isso dá cerca de R$ X."
- **Filtro:** se o "R$ X" passa da faixa de preço do usuário, o cartão do bairro ganha a etiqueta "acima do seu orçamento". Um botão permite esconder esses bairros. O preço **não** entra na nota.
- **Limitações (aparecem no Sobre os dados):**
  1. A média mistura casas e apartamentos, novos e usados.
  2. O R$/m² é a razão das médias, não a mediana.
  3. O valor é o declarado para o ITBI.
  4. O último mês não é publicado, por limpeza da base.
- Números de 2026 para conferência (até out): Tijuca cerca de R$ 6.350/m²; Praça Seca cerca de R$ 2.430/m².

---

## 5. Pesos padrão por perfil

Escala de 1 (pouco importa) a 5 (muito importa). O usuário pode mudar tudo.

| Critério | Família com filhos | Casal sem filhos | Solteiro(a) |
|---|---|---|---|
| Violência | 5 | 4 | 4 |
| Alagamento | 4 | 4 | 3 |
| Escolas | 5 | 2 | 1 |
| Transporte | 3 | 4 | 5 |
| Emprego | 3 | 4 | 5 |
| Barulho | 3 | 3 | 3 |

Por quê:
- **Família:** escolas e violência no máximo, como você pediu. Alagamento alto, porque perder bens e ter a rotina interrompida pesa mais com crianças.
- **Solteiro:** transporte e emprego no máximo. Escolas em 1, e não 0, para que um planejamento futuro ainda conte um pouco.
- **Casal:** equilibrado em 4, com escolas em 2, porque pode haver filho no horizonte.
- **Barulho** fica em 3 para todos: é uma preferência muito pessoal, então o padrão é neutro.

**Nota final** = Σ(peso x nota do critério) / Σ(pesos). Vai de 0 a 10, com uma casa decimal. A ordem da lista segue a nota final; em caso de empate, vale a maior nota no critério de maior peso.

---

## 6. Simulador de financiamento

### 6.1 Entradas
O que veio da tela 2 (renda, FGTS, entrada), mais:
- Preço do imóvel (preenchido com a estimativa do ITBI para o bairro e a área; editável).
- Prazo em anos (padrão 30; máximo vindo do JSON, hoje 35).
- Taxa de juros (preenchida pela linha provável; editável).

### 6.2 Linha provável
1. Renda bruta familiar (somada, se for o caso) define a faixa do MCMV pela tabela do JSON (Ministério das Cidades, out/2026):
   - Faixa 1: até R$ 3.200
   - Faixa 2: até R$ 5.000
   - Faixa 3: até R$ 9.600
   - Classe Média: até R$ 13.000
2. Se a renda cabe numa faixa **e** o preço do imóvel cabe no teto dessa faixa no Rio, a linha provável é **MCMV**, com a taxa da faixa. O simulador pergunta "tem 3 anos de FGTS?" para escolher entre a taxa de cotista e a de não cotista.
3. Caso contrário: **SBPE**, com taxa padrão = média da Caixa no Banco Central (crédito habitacional a taxas de mercado, pós-fixado em TR, último mês publicado). O usuário pode editar.
4. Subsídio do MCMV (Faixas 1 e 2): o simulador **não calcula o valor**, porque ele depende de regras da Caixa que não são publicadas em tabela aberta. Mostra só "pode haver subsídio de até R$ 55 mil; o valor é definido pela Caixa".

### 6.3 Cálculos
- **Valor financiado** = preço − entrada − FGTS.
- **Price** (parcela fixa): `P = V x i / (1 − (1+i)^−n)`, com i = taxa mensal equivalente `(1+a)^(1/12) − 1`.
- **SAC** (amortização fixa): amortização = V/n; parcela k = V/n + saldo antes da parcela k x i.
- Para cada sistema: primeira parcela, última parcela, total pago e total de juros, numa tabela lado a lado.
- **Simplificações declaradas na tela:** sem TR, sem seguros obrigatórios (MIP e DFI) e sem tarifas mensais. Os valores reais ficam um pouco maiores.

### 6.4 Quanto cabe
- **Parcela máxima** = 30% da renda bruta (o percentual fica no JSON).
- **Financiamento máximo** = valor presente da parcela máxima no prazo e na taxa:
  - no **SAC**, a 1ª parcela é a maior, então o limite é calculado para que ela caiba;
  - na **Price**, pela fórmula inversa.
- **Preço máximo do imóvel** = financiamento máximo + entrada + FGTS, limitado pela **cota máxima de financiamento** e pelo teto da faixa do MCMV.
  - **Atualizado em 27/11/2026 (seção 23):** a cota foi encontrada em fonte oficial e passou a ser aplicada.
  - **[DECIDIR] F:** ainda não achei a cota máxima (% do imóvel que o banco financia) em fonte oficial aberta. Na Etapa 3 procuro na Caixa e no Ministério. Se não achar, o simulador fica **sem** esse limite e mostra o aviso "o banco pode exigir entrada maior". Tudo bem?
- **Renda somada:** o simulador mostra lado a lado "só comprador 1" e "comprador 1 + 2": parcela máxima, faixa ou linha, preço máximo e a diferença.

### 6.5 Custos extras
| Item | Regra |
|---|---|
| ITBI | 3% do preço (parâmetro no JSON; fonte: Carioca Digital / Lei 6.250/2017). Nota: a base legal é o maior entre o valor da compra e o valor de referência da Prefeitura. |
| Registro e escritura (cartório) | "Consulte o cartório" (decisão D da Etapa 1). Aviso: no primeiro imóvel residencial financiado pelo SFH, os emolumentos têm 50% de desconto (Lei 6.015/1973, art. 290). |
| Avaliação do imóvel pelo banco | "Consulte o banco". |

**Dinheiro necessário na assinatura** = entrada + ITBI, mais "cartório e avaliação: consulte".

### 6.6 FGTS
- O FGTS informado abate o valor financiado.
- Avisos de regra, sem checar a elegibilidade de ninguém:
  - mínimo de 3 anos de trabalho com FGTS;
  - não ter imóvel no município onde mora ou trabalha;
  - não ter financiamento ativo no SFH;
  - imóvel residencial dentro das regras do SFH.
- Se a pessoa respondeu "sim" à pergunta de imóvel ou financiamento em 3.2, o aviso fica destacado.

### 6.7 Aviso fixo
"Simulação estimada. A aprovação e as condições finais dependem do banco."

---

## 7. Formato dos dados (contrato entre o ETL e o site)

### `site/data/bairros.json` (resumo)
```json
{
  "gerado_em": "2026-11-25",
  "bairros_exibidos": ["033", "..."],
  "bairros": [{
    "codbairro": "033", "nome": "Tijuca", "populacao_2022": 142326,
    "criterios": {
      "violencia": {
        "nota": 7.4,
        "indicadores": [{"id": "letalidade_100k", "valor": 8.9, "mediana_cidade": 21.3, "nota": 8.1, "peso": 0.5}],
        "cisps": [{"cisp": 19, "pct_pop": 0.88}, {"cisp": 18, "pct_pop": 0.11}],
        "periodo": "2025-11 a 2026-10", "fonte_id": "isp", "aviso": "..."
      },
      "alagamento": {}, "escolas": {}, "transporte": {}, "emprego": {}, "barulho": {}
    },
    "emprego_distancias_m": {"centro": 0, "barra": 0, "zona_sul": 0},
    "preco_itbi": {"rs_m2": 6354, "transacoes": 1572, "periodo": "..."},
    "ruido_db_oficial": null
  }],
  "fontes": {"isp": {"nome": "...", "url": "...", "atualizado_em": "...", "periodo": "...", "metodo": "texto do Sobre os dados"}}
}
```
O site precisa das distâncias de todos os bairros até todos os polos para a opção "outro bairro". Isso vai num arquivo à parte (`distancias.json`), em quilômetros, para não pesar a lista.

### `site/data/parametros_financiamento.json` (resumo)
Toda regra numérica do simulador fica aqui, com `fonte`, `url` e `data`: faixas do MCMV, tetos no Rio, juros (cotista e não cotista, região SE), prazo máximo, % de comprometimento da renda (30%), taxa SBPE (Banco Central), ITBI (3%) e textos de aviso. Inclui também a divergência entre o Ministério e a Caixa no campo `observacoes`. O site **não tem nenhum desses números no código**.

---

## 8. Fora do MVP (registrado para depois)
- Mapa Leaflet com os bairros coloridos pela nota.
- Tempo de viagem real (GTFS ou dados do Censo por área de ponderação).
- Ônibus comum no critério de transporte.
- Preço separando casa e apartamento (só se surgir fonte oficial).
- Mapa oficial de ruído (campo já reservado).

---

## 9. Resumo das decisões pendentes

| # | Pergunta | Minha recomendação |
|---|---|---|
| A | Quartos, banheiros e vagas: retirar ou manter só como anotação? | Retirar |
| B | Incluir "onde você trabalha?" (opcional) no critério Emprego? | Incluir |
| C | Incluir "que tipo de escola procura?" para família com filhos? | Incluir |
| D | Pontos dos polos: Carioca, Alvorada, Botafogo? | Sim |
| E | Usar o preço do ITBI como informação e filtro de orçamento (fora da nota)? | Sim |
| F | Sem cota máxima oficial: simulador sem esse limite, com aviso? | Sim |
| G | Botão "copiar link com minhas prioridades" (sem renda)? | Sim |
| H | Pesos dos indicadores dentro de cada critério e pesos por perfil (seções 4 e 5) estão bons? | Aprovar ou ajustar |

Respostas (25/11/2026): **tudo como recomendado**. A = retirar; B a G = sim; H = aprovado.

---

## 10. Imóveis à venda e para alugar

**Decisão (25/11/2026): opções 1 e 2, mais o simulador de aluguel.** O CSV da Caixa é baixado manualmente por você.

### 10.1 Imóveis da Caixa (opção 1)
- **Entrada:** `data_raw/caixa/Lista_imoveis_RJ.csv`, baixado no navegador a partir de https://venda-imoveis.caixa.gov.br (o passo a passo vai no README).
- **ETL (`etl/09_imoveis_caixa.py`):**
  - filtra o município do Rio;
  - associa cada imóvel a um bairro oficial pelo nome do bairro do anúncio, usando a mesma tabela de apelidos das escolas;
  - extrai tipo (casa ou apartamento), área, quartos (se houver), preço, desconto, modalidade de venda e link oficial;
  - grava `site/data/imoveis_caixa.json` com a data do arquivo.
  - Se o CSV não existir, o script avisa e grava uma lista vazia, sem quebrar o resto.
- **No site:** no detalhe de cada bairro, a seção "Imóveis da Caixa neste bairro". Ela é filtrada pelo tipo, pela área mínima e pelo orçamento do usuário, e os imóveis acima do orçamento ficam marcados. Cada imóvel mostra:
  - preço, área e modalidade;
  - o aviso "imóvel retomado pela Caixa: confira ocupação, estado e regras da venda no edital";
  - o link para a página oficial do imóvel.
  - Também mostra a data da lista.
- Os quartos da lista da Caixa servem só para exibir. O filtro de quartos continua fora (decisão A), porque não existe para os demais dados.

### 10.2 Links para portais (opção 2)
- No detalhe de cada bairro, os botões "Ver anúncios à venda" e "Ver anúncios para alugar". Eles abrem a busca do portal em outra aba, com bairro e, quando o portal permitir, tipo, área e preço.
- Os modelos de link ficam em `site/data/links_portais.json`, e não no código, para dar para corrigir quando o portal mudar. O teste da Etapa 4 confere se cada link abre a busca certa.
- Texto fixo: "Você vai sair do app. Os anúncios são dos portais, não foram verificados por este site."
- O app não lê, não copia e não guarda nada dos portais.

### 10.3 Simulador de aluguel
- Entradas: renda (já informada), valor do aluguel, condomínio e IPTU mensais (digitados pelo usuário; não há fonte oficial de preço de aluguel).
- Saídas:
  - aluguel máximo que cabe em 30% da renda bruta (mesmo parâmetro do JSON);
  - custo mensal total;
  - comparação lado a lado com a 1ª parcela do financiamento (SAC e Price) para o mesmo bairro e área;
  - "dinheiro parado" da compra (entrada + ITBI).
- Aviso: "comparação simples; não considera valorização do imóvel, reajuste do aluguel nem rendimento da entrada se ela ficasse aplicada".

### 10.4 Histórico (opções analisadas)

Pedido: mostrar opções de imóveis à venda ou para alugar que combinem com o perfil (bairro bem avaliado, área e orçamento).

| Opção | Fonte | Respeita a regra "só oficial, sem scraping"? | Limitações |
|---|---|---|---|
| 1. Imóveis da Caixa (venda direta e leilão) | Lista oficial da Caixa por estado (`venda-imoveis.caixa.gov.br`, CSV) | Sim | Só imóveis retomados pela Caixa; muitos ocupados ou para reforma; venda, não aluguel. A lista tem proteção anti-robô (CAPTCHA), então o download não pode ser automático: alguém baixa no navegador e coloca em `data_raw/caixa/`. |
| 2. Botão "ver anúncios deste bairro" | Links para a busca dos portais (ZAP, Viva Real, QuintoAndar, OLX), já com bairro, tipo, área e preço preenchidos | Sim: o app só abre um link, não lê nem copia nada dos portais | O formato dos links pode mudar sem aviso; são portais comerciais; o app não mostra os anúncios dentro dele. Cobre venda e aluguel. |
| 3. Mostrar anúncios dos portais dentro do app | Scraping ou API privada dos portais | **Não** (proibido na regra do projeto e, em geral, nos termos de uso dos portais) | Descartada. |

Aluguel: não existe fonte oficial e aberta de anúncios de aluguel. Também não há preço oficial de aluguel por bairro (o ITBI é só de compra). Para aluguel, a única opção compatível é a 2.

---

## 11. Ajustes depois do teste da Etapa 4 (25/11/2026)

- **Prioridades sem números na tela.** Cada critério é uma linha de "Pouco importante" a "Muito importante". O perfil só define o ponto de partida (os pesos 1 a 5 da seção 5 continuam valendo por trás). Motivo: mostrar "violência 4" para solteiro e "5" para família passava a ideia de que o app recomenda se preocupar menos com segurança.
- **Local de trabalho:** campos "Onde você trabalha" e "Onde a 2ª pessoa trabalha", os dois começando em "Não informar" (saiu a opção "Ninguém mais").

## 12. Revisão visual e mapa (25/11/2026)

- **Visual:** fundo levemente quente, verde-petróleo como cor principal, nota em anel, ícone por critério, etiquetas "Destaque" e "Atenção" (só a posição na cidade, sem rótulos), cartão de exemplo real e atalho "ver um bairro direto" na tela inicial (com pesos iguais), modo escuro automático. Referências consultadas: BomDeMorar, PontoCity, BairroBom, Zunoo, BairroSafe e Ondefuiroubado (só padrões de interface; nada copiado). Cores de semáforo e rótulos como "Moderado" ficaram de fora de propósito.
- **Fonte:** Geist e Geist Mono v1.9.2 (SIL Open Font License), baixadas do repositório oficial `vercel/geist-font` e hospedadas em `site/fonts/`. Nenhuma fonte vem de servidor de terceiros.
- **Mapa:** SVG gerado pelo ETL (`etl/11_mapa.py` -> `site/data/mapa.json`) a partir da malha oficial de bairros, sem mapa de fundo externo (para não enviar o IP do visitante a terceiros). Um único tom de verde: quanto mais escuro, maior a nota. Pode pintar pela nota final ou por critério, ver a cidade inteira e tocar num bairro para abrir o detalhe. No detalhe, um mapa pequeno mostra onde o bairro fica.

## 13. Quanto cabe no bolso (item 1 do plano de melhorias, 25/11/2026)

- **Painel "Seu orçamento"** no topo do resultado: preço máximo do imóvel, parcela máxima e linha provável. Sem renda informada, mostra um convite para informar.
- **Regra do preço máximo:** parcela de até 30% da renda bruta, SAC (1ª parcela é a maior, conta conservadora), prazo padrão do JSON (30 anos), entrada + FGTS somados. Calcula duas opções e usa a maior: MCMV da faixa da renda (limitado ao teto da faixa) e SBPE (taxa do Banco Central). Se o usuário digitou um preço máximo, vale o menor dos dois.
- **Em cada bairro:** preço do m² (ITBI), área máxima que cabe (preço máximo ÷ R$/m²) e 1ª parcela estimada para a área pedida (ou, se não informada, a área média vendida no bairro, avisando na tela), com a linha provável para aquele preço.
- Etiquetas "Cabe no seu bolso" / "Acima do que cabe"; filtro "Mostrar só os que cabem"; ordenação por nota, menor parcela, maior área que cabe ou menor preço do m² (a posição #1, #2... continua sendo pela nota).
- Conferido contra cálculo independente em Python (renda R$ 9.500, cotista, entrada R$ 80 mil, FGTS R$ 30 mil: MCMV Faixa 3 limitado ao teto de R$ 400 mil; SBPE R$ 342.766).

## 14. Comparar bairros (item 2 do plano de melhorias, 25/11/2026)

- Botão "+ Comparar" em cada cartão da lista e "Adicionar à comparação" no detalhe; de 2 a 3 bairros; barra fixa no rodapé com os escolhidos, "Comparar" e "Limpar".
- Tela `#comparar/COD1,COD2,COD3` (o link leva só os códigos dos bairros, nunca renda): nota final e as 6 notas com barras (melhor de cada linha em destaque), "Preço e o seu bolso" (m² ITBI, quanto cabe, 1ª parcela, cabe ou não), "Os números por trás das notas" (cada critério expansível com todos os indicadores lado a lado), resumo em texto ("X fica na frente em ..."), mapa com os bairros comparados e botões de detalhe/simular por bairro.
- Decisão de leitura: a tabela principal mostra só notas. Mostrar um único indicador ao lado da nota induzia a erro (ex.: Penha melhor em violência com letalidade maior que a da Tijuca, porque a nota também pesa roubos). Por isso os indicadores aparecem todos juntos, na seção expansível.

## 15. Resumo em texto e radar (itens 3 e 5 do plano de melhorias, 25/11/2026)

- **Resumo em texto** no detalhe do bairro, montado por regras a partir dos números (sem opinião): critérios com nota ≥ 6,5 ("se destaca em X, à frente de N% dos bairros do Rio"), critérios com nota ≤ 3,5 ("pontos de atenção: Y, atrás de N%"), preço do m² (ITBI) comparado com a mediana dos bairros de referência (novo campo `preco_mediana_rs_m2` no `bairros.json`, hoje R$ 3.009) e, com renda informada, quanto cabe no bairro. Usa as mesmas notas da tela (escola por tipo, emprego pelo local de trabalho).
- **Radar** (teia com os 6 critérios) em SVG: no detalhe, o bairro com a linha tracejada da mediana do Rio (nota 5); na comparação, os 2 ou 3 bairros sobrepostos com cores e legenda. Tem descrição em texto para leitores de tela.

## 16. Nomes dos critérios no sentido positivo (25/11/2026)

- Problema apontado: "Destaque: Alagamento 7,1" (Praça Seca) parecia dizer que o bairro alaga muito, quando a nota 7,1 significa que alaga **menos** que 71% dos bairros do Rio (ISMFI 15 contra mediana 31).
- Na tela, os critérios passam a se chamar **Segurança, Menos alagamento, Escolas, Transporte, Emprego, Menos barulho** (nota alta = melhor em todos). Nos destaques e no resumo usa-se o sentido positivo ("pouco alagamento", "pouco barulho", "segurança", "acesso ao emprego"); nos pontos de atenção, o nome do problema ("Alagamento", "Violência", "Barulho", "Distância do emprego", "Poucas escolas"). Os dados e os códigos internos (`violencia`, `alagamento`...) não mudaram.

## 17. Revisão dos pesos de segurança e transporte (25/11/2026)

Motivo: a Tijuca aparecia com segurança pior que a Penha (5,7 x 6,5) e transporte pior (6,6 x 7,4), o que não batia com a realidade percebida.

- **Segurança:** letalidade violenta passa de 50% para **70%**; roubo de veículo, de rua e a residência ficam com **10% cada** (eram 20/20/10). Diagnóstico: roubo por morador infla em áreas de passagem (20% da Tijuca está na 18ª DP, entorno do Maracanã e Praça da Bandeira) e é subnotificado onde se denuncia menos (a 22ª DP, da Penha, cobre 190 mil pessoas, incluindo o Complexo do Alemão). A letalidade é o dado mais confiável. Resultado: Tijuca 7,0, Penha 6,4.
- **Transporte:** sai a contagem de "estações a até 1 km" (contava cada parada de BRT, a cada ~600 m, como uma estação de metrô). Agora: **50% distância até qualquer estação** (metrô, trem, BRT, VLT) **+ 50% distância até metrô ou trem**. Resultado: Tijuca 7,4, Penha 6,4. Efeito colateral aceito: bairros servidos só por BRT (Jacarepaguá) caem (Praça Seca 7,1 → 4,8).

## 18. Página por bairro e compartilhar no WhatsApp (item 4 do plano de melhorias, 25/11/2026)

- `etl/12_paginas_bairros.py` gera, para cada bairro exibido, `site/bairro/<slug>/index.html` (ex.: `/bairro/tijuca/`) com etiquetas Open Graph (título "Tijuca: nota 6,3 de 10", descrição gerada pelos números e imagem) e `previa.png` (1200x630, desenhada com o visual do app e fotografada pelo Chrome). Quem abre o link é levado ao bairro no app (`#bairro/COD`). Também gera `site/img/previa.png` para a página inicial, que ganhou as mesmas etiquetas.
- Na prévia, a nota final usa os 6 critérios com o mesmo peso (a prévia não conhece as prioridades de quem abre), e a imagem diz isso.
- No detalhe do bairro: "Compartilhar no WhatsApp" (link `wa.me` com texto e o endereço da página do bairro), "Compartilhar" (menu nativo do celular, quando existe) e "Copiar link". Nada digitado pela pessoa vai no link.
- `config.SITE_URL` guarda o endereço público (a prévia exige URL completa da imagem). Se o site mudar de endereço, altere ali e rode o ETL.

## 19. Perguntas frequentes e imprimir/PDF (itens 6 e 7 do plano de melhorias, 25/11/2026)

- **Tela "Dúvidas"** (`#perguntas`, link no cabeçalho e na tela inicial): 14 perguntas em blocos que abrem e fecham (como a nota é calculada, nomes no sentido positivo, o que entra em segurança, delegacias, preço do m², MCMV, SAC x Price, comprometimento da renda, FGTS, custos extras, validade da simulação, privacidade, bairros da versão e datas dos dados). Os números das respostas (faixas, tetos e juros do MCMV, taxa SBPE, ITBI, 30% da renda, períodos de cada fonte) são lidos dos JSON, não ficam fixos no texto.
- **Imprimir ou salvar em PDF** no detalhe do bairro, no simulador e na comparação, usando a impressão do navegador (sem servidor). Na impressão: somem cabeçalho, rodapé, ilustrações e botões; os blocos fechados abrem; entra um cabeçalho com data, endereço do app, data dos dados e o aviso de simulação estimada; os cartões não são cortados entre páginas.

## 20. Etapa 5: documentação e rotina de atualização (25/11/2026)

- `README.md` completo: como funciona, estrutura, preparar o computador (Python, Chrome, unrar, gh, gcloud/BigQuery), frequência de atualização de cada fonte, downloads manuais (Catálogo de Escolas e Caixa), conferência das regras do MCMV, rodar o ETL, testar (fluxo e contraste), publicar no GitHub Pages, mudar regras no `config.py`, problemas comuns e licenças.
- `requirements.txt` com as versões das bibliotecas.
- `etl/ferramentas/baixar_dados.sh`: baixa os limites das delegacias (ISP) e o Ideb (INEP); tenta de novo em caso de falha e nunca substitui um arquivo bom por um download incompleto.
- Ano do Ideb passou para `config.IDEB_ANO` (antes estava no código do script de escolas).
- Validação: ETL completo rodado do zero conforme o README (4 min 35 s, sem erros), teste do site e auditoria de contraste sem falhas.

## 21. Cidade inteira e subnotificação (25/11/2026)

- O site passa a exibir **todos os bairros** (`EXIBIR_TODOS = True`): 163 com dados (Joá, Grumari, Argentino e Ingleses ficam de fora por terem menos de mil moradores ou nenhum setor no Censo 2022).
- **Problema encontrado ao abrir a cidade:** bairros que são majoritariamente favela apareciam no topo (Rocinha em 1º, segurança 9,7; Mangueira 2º; Complexo do Alemão 5º). Causa: nessas áreas, boletins de ocorrência e chamados ao 1746 são pouco registrados (Rocinha: 10 roubos de rua por 100 mil e 0,6 chamado de barulho por mil moradores, contra 405 e 24 em Copacabana), e o método lia "pouco registro" como "pouco problema".
- **Decisão (usuário):** nos bairros com **50% ou mais dos moradores em área de favela** (camada oficial Limite de Favelas 2022, IPP; 15 bairros: Rocinha, Jacarezinho, Acari, Vidigal, Complexo do Alemão, Mangueira, Caju, Costa Barros, Galeão, Pitangueiras, Itanhangá, Maré, Vasco da Gama, Tauá, Manguinhos), Segurança e Menos barulho ficam como "dados insuficientes", com texto neutro e a fonte; o bairro não recebe nota final nem posição no ranking, mas continua com os outros 4 critérios, preço, mapa (listrado), comparação e simulador; e esses bairros saem da base de comparação dessas duas notas.
- **Interface para 163 bairros:** lista com 20 por vez ("Ver mais"), busca por nome, bairros sem nota final no fim com explicação; mapa sem nomes na cidade inteira (destaques de maior e menor nota continuam; tocar mostra o nome); prévias em JPG para as 163 páginas; textos e perguntas frequentes calculados.
- Topo do ranking (perfil família): Cosme Velho, Glória, Catete, Copacabana, Laranjeiras; fim: Barra Olímpica, Vargem Grande, Gardênia Azul, Paquetá, Jardim América.

## 22. Lista e mapa no celular (25/11/2026)

- **Cartão compacto** na lista: de 547 px para 330 px de altura no celular (cerca de 2,5 cartões por tela). Nome, zona, etiqueta de orçamento e nota no topo; faixa fina com m², quanto cabe e 1ª parcela; as 6 notas numa grade 3x2 (ícone, valor e barrinha). Destaque e atenção saíram do cartão (continuam no detalhe). No computador, a lista vira duas colunas. Quando entrada + FGTS pagam o imóvel inteiro, a parcela aparece como "sem financiar".
- **Mapa com regiões:** botões Cidade toda, Centro, Zona Sul, Zona Norte, Barra e Jacarepaguá, Zona Oeste (agrupamento das Regiões de Planejamento do IPP). Na cidade toda, 107 dos 163 bairros tinham menos de 12 px na tela; com a região, o tamanho típico passa de ~10 px para ~22 px. Na região, aparecem os nomes que cabem dentro do bairro (sem sobreposição, letra de ~14 px), e os destaques "maior nota / menor nota" passam a ser os da região. O enquadramento ignora ilhas pequenas (ex.: Cagarras).
- **Tocar num bairro do mapa** mostra um cartão logo abaixo (nome, nota, "Ver detalhes" e "Comparar") em vez de sair da tela; o bairro escolhido fica contornado.

## 23. Cota máxima de financiamento (27/11/2026)

- **Problema:** o preço máximo era "financiamento que cabe em 30% da renda + entrada + FGTS", sem a cota (parte do imóvel que o banco financia). Com entrada zero, o app mostrava preços que nenhum banco aprova (renda de R$ 10 mil e nenhuma entrada: R$ 279 mil). A decisão F (seção 6.4) dizia que não havia fonte oficial; havia.
- **Fontes encontradas** (detalhes em `FONTES.md`, seção 7):
  - SBPE (Caixa): 80% no SAC e 70% na Price, CAIXA Notícias de 10/10/2025 e 09/12/2025 (em vigor desde 13/10/2025).
  - MCMV (FGTS): entrada mínima de 20% (cota de 80%), que o banco pode reduzir a 10% no SAC. IN 48/2022 do Ministério das Cidades, art. 34, compilada em 09/04/2026.
  - Pró-Cotista: 90% no SAC e 80% na Price (página Financiamentos do FGTS); 50% no usado (IN 30/2024). As notícias que falavam em 80% e 60% não têm fonte oficial e não foram usadas.
- **Decisões (usuário, 27/11/2026):**
  - MCMV usa **80% no SAC e na Price** (a regra geral do art. 34, que vale em qualquer caso). O texto avisa que no SAC o banco pode aceitar 10% de entrada e que no usado do Sul e Sudeste a cota é menor (65% na faixa de renda de R$ 4.700,01 a R$ 8.600 e 60% na Classe Média). O app não pergunta se o imóvel é novo ou usado.
  - Pró-Cotista fica registrado no JSON com os números do FGTS, só para o texto (o app não simula essa linha).
- **Regra no app:** preço máximo = o **menor** entre (a) financiamento que cabe em 30% da renda + entrada + FGTS, (b) (entrada + FGTS) ÷ (1 − cota) e (c) o teto do MCMV, quando for o caso. A tela diz qual dos três travou o valor. O simulador avisa quando a entrada fica abaixo da mínima (com o valor em reais e quanto falta) e mostra a linha "Entrada mínima" nos custos. Vale para o painel "Seu orçamento", o "Quanto cabe" de cada bairro, a tabela "Renda única x somada" e o simulador.
- **Dados:** bloco `cota_max` em `parametros_financiamento.json` (por linha e sistema, com fonte, link e data), gerado por `etl/10_parametros_financiamento.py`. Nova pergunta frequente "Preciso dar entrada? De quanto?" e fontes da cota em "Sobre os dados".

## 24. Segurança em bairros mal representados pela delegacia (27/11/2026)

- **Problema:** a taxa do ISP é crimes ÷ moradores da área da delegacia (CISP) inteira. Paquetá está na CISP 5, a mesma do Centro: ficava com roubo de rua de 6.850 por 100 mil e segurança 2,1, numa ilha sem carros, e aparecia entre os últimos do ranking só por isso. Centro, Lapa, Gamboa, Santo Cristo e Saúde também têm roubo de rua muito acima do resto da cidade, porque os crimes acontecem com quem circula por lá e a conta usa só os moradores.
- **Levantamento dos candidatos** (bairro separado fisicamente da área principal da sua CISP, ou com menos de 5% dos moradores dela): Paquetá (ilha, 11% da CISP 5), Cidade Universitária (ilha, 0,7% da CISP 37) e 18 bairros contíguos à sua CISP com menos de 5% dos moradores (Grumari, Camorim, Argentino, Joá, Campo dos Afonsos, Zumbi, Jabour, Ribeira, Barra de Guaratiba, Ilha de Guaratiba, Cocotá, Praia da Bandeira, Moneró, Engenheiro Leal, Parque Colúmbia, Deodoro, Gardênia Azul, Gericinó).
- **Decisão (usuário):** os 20 entram em `BAIRROS_SEGURANCA_INSUFICIENTE` (`etl/config.py`, com o motivo de cada um). Segurança fica como "dados insuficientes", o bairro fica sem nota final e sem posição no ranking (mesmo caminho da seção 21) e sai da base de comparação de Segurança. Os outros critérios, o preço, o mapa, a comparação e o simulador continuam. Efeito: 17 bairros saem do ranking (Grumari, Argentino e Joá já não tinham nota, por terem menos de mil moradores), que passa de 148 para 131 bairros; as notas de segurança dos demais mudam pouco, porque a base de comparação mudou.
- **Áreas com muita gente de fora (só aviso, a nota não muda):** regra aprovada: CISPs com roubo de rua acima de 3 vezes a mediana dos bairros (`PUBLICO_DE_FORA` no `config.py`). Hoje: mediana de 605 por 100 mil, limite de 1.815, CISPs 1, 4, 5 e 18. O aviso vai para o bairro com 50% ou mais dos moradores nessas CISPs: Centro, Lapa, Gamboa, Santo Cristo, Saúde, Maracanã e Praça da Bandeira (Paquetá já está sem nota). Texto: "Área com muita gente de fora (comércio e trabalho). A taxa usa só os moradores na conta, então pode parecer maior do que o risco para quem mora ali." Aparece no bloco de Segurança do detalhe, no resumo em texto, na comparação ("Avisos sobre os dados") e numa nova pergunta frequente. A alternativa com densidade baixa (que deixaria de fora a CISP 18) não foi escolhida.
- **Dados:** `02_violencia.py` grava as taxas por CISP em `meta_violencia.json` (`taxas_cisp`). `bairros.json` ganha `seguranca_insuficiente`, `publico_de_fora`, `sem_nota_final_motivo` por bairro e `aviso_publico_de_fora` no bloco de violência.

## 25. Revisão da seção 24: sai a regra dos "menos de 5% da delegacia" (27/11/2026)

- **Motivo (usuário):** todo bairro usa a taxa da delegacia inteira, seja ele 4% ou 30% dela, então ser pequeno não piora o dado. A regra também criava incoerência: Engenheiro Leal saía do ranking, mas Cascadura, Quintino, Turiaçú e Vaz Lobo, com a mesma taxa da CISP 29, ficavam; Zumbi, Ribeira, Cocotá, Praia da Bandeira, Moneró e Jabour saíam, mas o resto da Ilha do Governador (CISP 37) ficava.
- **Decisão:** `BAIRROS_SEGURANCA_INSUFICIENTE` fica só com os casos de separação física: **Paquetá e Cidade Universitária** (ilhas). Os outros 18 voltam a ter nota de Segurança e nota final. O ranking passa de 131 para 146 bairros (os 148 de antes da seção 24, menos as duas ilhas).
- **Bairros que dividem a delegacia:** o detalhe de Segurança mostra "Área de delegacia" e "Mesma delegacia principal de: ...". Na conferência, a delegacia principal era tirada do primeiro item da lista, que vem em ordem de número da CISP (no Centro, saía a 1ª DP, com 4,5% dos moradores, em vez da 5ª DP, com 76%). Corrigido: a principal agora é a de mais moradores.
- A pergunta frequente "Por que alguns bairros não têm nota final?" deixou de citar "poucos moradores perto do total da delegacia".

## 26. Imóvel novo ou usado e a cota do MCMV (27/11/2026)

- **Problema:** o app usava 80% para todo o MCMV, mas o JSON dizia que no imóvel usado do Sul e Sudeste a cota era menor (65% para renda de R$ 4.700,01 a R$ 8.600 e 60% na Classe Média, pela IN 30/2024). No Rio a maioria das compras é de imóvel usado.
- **Conferência da fonte:** a IN 30/2024 era o orçamento do FGTS de **2025**. O de **2026** é a **IN MCID 45, de 26/12/2025** (compilada em 14/10/2026, alterada pelas IN 3 e 22 de 2026). Ela **revoga a IN 30/2024** (art. 12) e **não repete** a cota de 65% por faixa de renda. Ficaram só: Classe Média, imóvel usado no Sul e Sudeste, até 60% (art. 6º); Pró-Cotista, imóvel usado, até 50% com renda até R$ 12 mil (art. 5º). A IN 48/2022 (Carta de Crédito Individual, compilada em 09/04/2026) não tem cota própria para usado (só muda desconto e taxa de administração). Para o SBPE, a Caixa não publica cota diferente para usado.
- **Regra no app (pela norma em vigor):** Faixas 1, 2 e 3: 80% no novo e no usado. Classe Média: 80% no novo e 60% no usado. SBPE: igual no novo e no usado. A cota de usado fica em `cota_max.<linha>.usado` (por faixa ou por intervalo de renda), gerado por `etl/10_parametros_financiamento.py`.
- **Interface:** pergunta "O imóvel é novo ou usado?" na etapa do imóvel e no simulador, começando em **usado** (caso mais comum e mais conservador), guardada em `estado.imovelUsado`. A cota vem da renda de cada cálculo (a tabela "Renda única x somada" usa a cota da renda de cada coluna). O texto do limite diz qual cota foi usada e por quê (ex.: "Imóvel usado no MCMV (Classe Média) com renda de R$ 12.000: o banco financia até 60% (IN MCID 45/2025...)"). O link de compartilhar leva "novo/usado" (`u=1` ou `u=0`), nunca valores. A pergunta frequente sobre entrada lista as regras de usado.
- **Diferença em relação ao pedido:** o pedido citava 65% para renda de R$ 4.700,01 a R$ 8.600. Essa regra foi revogada para 2026, então o caso "renda R$ 6.000, usado, entrada R$ 70 mil" fica com cota de 80% (preço máximo de R$ 271 mil, limitado pela renda), e não 65%.
- Observação: o art. 13 da IN 45 diz "entra em vigor em 1° de janeiro de 2025", o que parece erro de digitação (o título e o art. 1º falam do exercício de 2026).
