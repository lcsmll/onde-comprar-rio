# Onde Comprar no Rio

App de navegador que ajuda a escolher um bairro para comprar imóvel no município do Rio de Janeiro e a simular o financiamento.

**Acesse:** https://lcsmll.github.io/onde-comprar-rio/

- **6 critérios com nota de 0 a 10:** segurança, menos alagamento, escolas, transporte, emprego e menos barulho. A nota é a posição do bairro entre os 163 bairros do Rio com pelo menos mil moradores.
- **Quanto cabe no bolso:** preço máximo do imóvel, área que cabe e 1ª parcela estimada em cada bairro.
- **Comparar bairros** lado a lado, **mapa**, **resumo em texto**, **radar**, **simulador** (SAC x Price, MCMV ou SBPE, renda única ou somada, ITBI) e **perguntas frequentes**.
- **Página por bairro com prévia no WhatsApp** e opção de **imprimir ou salvar em PDF**.
- **Só dados oficiais e gratuitos:** ISP-RJ, Data.Rio / Prefeitura, INEP, IBGE, Caixa, Banco Central e Ministério das Cidades.
- **Privacidade:** tudo roda no navegador. Nada do que a pessoa digita é enviado ou guardado. Não há cookies, analytics nem servidor.

*Simulação estimada. A aprovação e as condições finais dependem do banco.*

---

## Sumário

1. [Como funciona](#1-como-funciona)
2. [Estrutura de pastas](#2-estrutura-de-pastas)
3. [Preparar o computador (uma vez)](#3-preparar-o-computador-uma-vez)
4. [Atualizar os dados](#4-atualizar-os-dados)
5. [Conferir e testar](#5-conferir-e-testar)
6. [Publicar](#6-publicar)
7. [Mudar regras e configurações](#7-mudar-regras-e-configurações)
8. [Problemas comuns](#8-problemas-comuns)
9. [Licenças e créditos](#9-licenças-e-créditos)

---

## 1. Como funciona

```
fontes oficiais ──> etl/ (Python) ──> site/data/*.json ──> site/ (HTML + CSS + JS) ──> GitHub Pages
```

- O **ETL** (`etl/`) baixa e trata os dados e calcula os indicadores de **todos os bairros da cidade**, e o site exibe a cidade inteira (`EXIBIR_TODOS = True` em `etl/config.py`). Para voltar a uma lista menor, use `EXIBIR_TODOS = False` e `BAIRROS_MVP_NOMES`.
- **Bairros sem nota final:** nos bairros com 50% ou mais dos moradores em área de favela (Limite de Favelas 2022, IPP), Segurança e Menos barulho ficam como "dados insuficientes" (boletins de ocorrência e chamados ao 1746 são pouco registrados nessas áreas) e o bairro não entra no ranking. O corte fica em `FAVELA_CORTE_PCT`. Também ficam sem nota de Segurança (e sem nota final) os bairros da lista `BAIRROS_SEGURANCA_INSUFICIENTE`, em que a taxa da delegacia não representa os moradores (ex.: Paquetá, ilha na área da delegacia do Centro). Bairros em áreas com muita gente de fora (regra `PUBLICO_DE_FORA`) mantêm a nota, com um aviso.
- O resultado são arquivos **JSON** em `site/data/`, mais as páginas de prévia em `site/bairro/`.
- O **site** é estático: lê os JSON e faz as contas no aparelho de quem acessa. Nenhum número de regra fica no código do site. Pesos, faixas do MCMV, juros e ITBI vêm dos JSON.
- A **publicação** é automática: a cada `git push` na branch `main`, o GitHub publica a pasta `site/`.

Como cada nota é calculada está explicado na página "Sobre os dados" do app, em `docs/ESCOPO.md` (regras e decisões) e em `docs/FONTES.md` (cada fonte, link, formato e problemas).

---

## 2. Estrutura de pastas

```
etl/
  config.py                  TODAS as regras ajustáveis (bairros exibidos, pesos, raios, períodos, ano do Ideb...)
  comum.py, arcgis.py, bq.py funções compartilhadas (setores, médias, BigQuery, camadas da Prefeitura)
  01_bairros.py              malha de bairros e setores do Censo 2022 (população)
  02_violencia.py            ISP-RJ por delegacia -> bairro
  03_alagamento.py           ISMFI (COPPE/UFRJ) + ocorrências do COR (BigQuery)
  04_escolas.py              Catálogo de Escolas e Ideb (INEP)
  05_transporte.py           estações de metrô, trem, BRT e VLT
  06_emprego.py              distância aos polos de emprego e matriz bairro x bairro
  07_barulho.py              1746 (BigQuery), vias, trilhos, zonas de ruído de aeroporto
  08_preco_itbi.py           preço do m² (ITBI)
  09_imoveis_caixa.py        imóveis à venda da Caixa (se o CSV existir)
  10_parametros_financiamento.py  MCMV, taxa SBPE (Banco Central), ITBI
  11_mapa.py                 desenho do mapa (SVG)
  99_montar_notas.py         notas 0-10 e site/data/bairros.json
  12_paginas_bairros.py      páginas /bairro/<nome>/ e imagens de prévia do WhatsApp
  rodar_tudo.sh              roda tudo em ordem
  ferramentas/
    baixar_dados.sh          baixa limites das delegacias (ISP) e Ideb (INEP)
    gerar_ilustracao.py      gera a ilustração site/img/ilustracao-rio.svg
  ca_inep.pem                cadeia de certificados para o servidor do INEP (ver seção 8)
site/                        o app publicado (index.html, app.js, style.css, data/, fonts/, img/, bairro/)
docs/                        FONTES.md (fontes de dados) e ESCOPO.md (regras e decisões)
tests/                       teste_site.py (fluxo completo no navegador) e contraste.py (legibilidade)
data_raw/                    arquivos baixados (fora do git, ~1 GB)
data_proc/                   intermediários do ETL (fora do git)
```

---

## 3. Preparar o computador (uma vez)

Os comandos abaixo são para Linux. No Windows, use o WSL ou adapte os caminhos.

### 3.1 Programas

| Programa | Para quê | Como instalar |
|---|---|---|
| Python 3.12 | ETL e testes | já vem no Ubuntu; ou https://www.python.org |
| Google Chrome | imagens de prévia e testes | https://www.google.com/chrome |
| `unrar` | abrir o arquivo das delegacias do ISP | `sudo apt install unrar` |
| Git e GitHub CLI (`gh`) | publicar | `sudo apt install git` e https://cli.github.com |
| Google Cloud CLI (`gcloud`) | login no BigQuery (1746 e COR) | ver 3.3 |

### 3.2 Ambiente Python

Na pasta do projeto:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 3.3 BigQuery (reclamações do 1746 e alagamentos do COR)

Os chamados do 1746 e as ocorrências do COR só existem na base pública da Prefeitura no Google BigQuery (projeto `datario`). É gratuito: o uso fica dentro da cota grátis de 1 TB por mês, e a maior consulta lê cerca de 0,4 GB.

1. **Projeto Google Cloud:** em https://console.cloud.google.com, crie um projeto no modo sandbox (não precisa de cartão). Anote o **ID** do projeto e coloque em `BQ_PROJETO` no `etl/config.py` (hoje: `imovel-rio`).
2. **Instale o gcloud** na sua pasta pessoal. Não use um disco externo formatado para Windows (NTFS/exFAT), porque a extração fica incompleta:
   ```bash
   cd ~ && curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-linux-x86_64.tar.gz
   tar -xzf google-cloud-cli-linux-x86_64.tar.gz
   ```
3. **Login (uma vez):** marque **todas** as caixas de permissão na tela do Google.
   ```bash
   ~/google-cloud-sdk/bin/gcloud auth application-default login
   ```
4. **Teste:**
   ```bash
   .venv/bin/python etl/bq_teste.py imovel-rio
   ```

### 3.4 Dados que não estão no git

A pasta `data_raw/` não vai para o GitHub (tem ~1 GB). Num computador novo:
- rode `bash etl/ferramentas/baixar_dados.sh`;
- faça os dois downloads manuais da seção 4.2.

O resto os scripts baixam sozinhos.

---

## 4. Atualizar os dados

### 4.1 Com que frequência cada fonte muda

| Dado | Fonte | Atualização da fonte | O que fazer |
|---|---|---|---|
| Segurança | ISP-RJ | mensal (cerca de 2 meses de atraso; os últimos meses são provisórios) | rodar o ETL todo mês |
| Preço do m² | ITBI / Prefeitura | mensal (o último mês não é publicado) | rodar o ETL todo mês |
| Reclamações de barulho | 1746 (BigQuery) | diária | rodar com `--atualizar` |
| Taxa SBPE | Banco Central | mensal | automático ao rodar o ETL |
| Regras do MCMV | Ministério das Cidades | quando o governo muda | **conferir e editar à mão** (4.3) |
| Escolas (localização) | Catálogo de Escolas (INEP) | anual (Censo Escolar) | download manual (4.2) |
| Ideb | INEP | a cada 2 anos (próximo: 2027) | trocar `IDEB_ANO` e rodar `baixar_dados.sh` |
| Imóveis da Caixa | Caixa | frequente | download manual (4.2), se quiser |
| Alagamentos registrados | COR (BigQuery) | **parada desde abr/2024** | nada; reavaliar se voltar a ser atualizada |
| Estações, malha de bairros, zonas de ruído | Data.Rio | raramente | apagar o `.geojson` em `data_raw/datario/` para baixar de novo |
| População | Censo 2022 (IBGE) | próximo Censo | nada |

**Rotina sugerida (mensal):** seção 4.4 (rodar tudo), depois seções 5 e 6.

### 4.2 Downloads manuais (exigem navegador)

**Catálogo de Escolas do INEP** (localização das escolas; uma vez por ano)
1. Abra https://anonymousdata.inep.gov.br/analytics/saw.dll?Portal&PortalPath=%2Fshared%2FCenso%20da%20Educa%C3%A7%C3%A3o%20B%C3%A1sica%2F_portal%2FCat%C3%A1logo%20de%20Escolas
2. Em **UF**, marque **RJ**. Em **Município**, desmarque "Todos" e marque **Rio de Janeiro**. Clique em **Aplicar**.
3. Clique em **Exportar**. O arquivo "Análise - Tabela da lista das escolas - Detalhado.csv" vai para a pasta de downloads.
4. Mova e renomeie para `data_raw/inep/catalogo/catalogo_escolas_rio_AAAA-MM-DD.csv`, com a data do dia. O script usa sempre o arquivo mais recente da pasta.

**Imóveis à venda da Caixa** (opcional)
1. Abra https://venda-imoveis.caixa.gov.br, procure a opção de baixar a lista de imóveis do estado e escolha **RJ** (pode pedir CAPTCHA).
2. Salve como `data_raw/caixa/Lista_imoveis_RJ.csv`.
3. Ao rodar o ETL, o script 09 mostra quantos imóveis entraram e se algum bairro não foi reconhecido. Se aparecer um nome não reconhecido, acrescente um apelido em `APELIDOS_BAIRRO`, no `etl/comum.py`.

### 4.3 Conferir as regras do MCMV

Os valores do Minha Casa, Minha Vida (faixas de renda, tetos e juros) **não têm API**. Estão transcritos em `etl/10_parametros_financiamento.py` (bloco `MCMV`), com a fonte e a data.

1. Abra https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/habitacao/programa-minha-casa-minha-vida/mcmv-fgts e veja a data "Atualizado em".
2. Se mudou desde a data em `pagina_atualizada_em`, atualize as faixas, os tetos e os juros no bloco `MCMV` e as datas `pagina_atualizada_em` e `CONSULTA`. Confira também a cota máxima (bloco `COTA_MAX`), nas fontes citadas ali.
3. Rode o ETL. O app, o simulador e as perguntas frequentes leem tudo desse arquivo.

A taxa do SBPE é buscada sozinha na API do Banco Central a cada execução.

### 4.4 Rodar o ETL

```bash
bash etl/rodar_tudo.sh               # reaproveita as consultas já salvas do BigQuery
bash etl/rodar_tudo.sh --atualizar   # busca de novo os dados do 1746 e do COR no BigQuery
```

Leva de 4 a 6 minutos. Cada script mostra um resumo com os bairros da lista `BAIRROS_MVP_NOMES` (usada como amostra de conferência) e a mediana da cidade. O `99_montar_notas.py` mostra a **tabela final de notas** (com a cidade inteira, os 10 primeiros e os 5 últimos). Confira se nada mudou de forma estranha.

Para rodar um passo só: `.venv/bin/python etl/02_violencia.py` (com o mesmo `--atualizar`, se for de BigQuery). Depois rode o `99_montar_notas.py` e o `12_paginas_bairros.py` para refazer o JSON e as prévias.

---

## 5. Conferir e testar

1. **Ver o site no seu computador:**
   ```bash
   cd site && python3 -m http.server 8765 --bind 127.0.0.1
   ```
   Abra http://127.0.0.1:8765. Para ver como fica no celular, use o modo dispositivo do navegador (Ctrl+Shift+M no Chrome).
2. **Teste automático do fluxo completo** (celular e computador), com o servidor ligado, em outro terminal:
   ```bash
   .venv/bin/python tests/teste_site.py
   ```
   Tem que terminar com `Falhas: 0` e `Erros de JavaScript: nenhum`. As capturas de tela ficam em `tests/capturas/`.
3. **Auditoria de contraste** (legibilidade dos textos):
   ```bash
   .venv/bin/python tests/contraste.py
   ```
   Tem que terminar com `Total de textos com contraste insuficiente: 0`.

Os dois testes também rodam contra o site publicado:
```bash
URL_SITE=https://lcsmll.github.io/onde-comprar-rio/ .venv/bin/python tests/teste_site.py
```

---

## 6. Publicar

O site é publicado pelo **GitHub Pages** a cada envio para a branch `main`. O arquivo `.github/workflows/pages.yml` publica só a pasta `site/`.

```bash
git add -A
git commit -m "Atualiza dados de <mês>/<ano>"
git push
```

Acompanhe com `gh run list --limit 1`. Em cerca de 30 segundos o site está atualizado.

**Primeira vez num computador novo:**
- `gh auth login`, autorizando também a permissão `workflow`: `gh auth refresh -h github.com -s workflow`.
- `gh auth setup-git`, para o `git push` usar o login do `gh`.

**Configuração do repositório** (já feita): em Settings > Pages, a opção "Source" está em **GitHub Actions**.

**Se a publicação falhar** com erro do próprio GitHub (por exemplo, "check suite does not exist" ou "No artifacts named github-pages"), é instabilidade deles. Rode de novo:
```bash
gh run rerun $(gh run list --limit 1 --json databaseId --jq '.[0].databaseId')
```

**Se o endereço do site mudar** (domínio próprio, outro repositório):
1. Atualize `SITE_URL` em `etl/config.py` e as etiquetas `og:` e `canonical` no início de `site/index.html`.
2. Rode o ETL. As prévias do WhatsApp usam o endereço completo.

---

## 7. Mudar regras e configurações

Tudo fica em `etl/config.py`. Depois de mudar, rode o ETL (seção 4.4).

| Quero... | Onde |
|---|---|
| Exibir só alguns bairros | `EXIBIR_TODOS = False` e a lista `BAIRROS_MVP_NOMES` (nomes exatos da malha oficial) |
| Exibir a cidade inteira (atual) | `EXIBIR_TODOS = True` |
| Mudar o corte de subnotificação (favela) | `FAVELA_CORTE_PCT` e `CRITERIOS_SUBNOTIFICADOS` |
| Tirar a nota de Segurança de um bairro mal representado pela delegacia | `BAIRROS_SEGURANCA_INSUFICIENTE` (nome do bairro e motivo) |
| Mudar a regra do aviso "muita gente de fora" | `PUBLICO_DE_FORA` e `PUBLICO_DE_FORA_AVISO` |
| Mudar os pesos padrão de cada perfil | `PESOS_PERFIL` |
| Mudar os pesos dentro de segurança | `VIOLENCIA_INDICADORES` (hoje: letalidade 70%, roubos 10% cada) |
| Mudar como o transporte é medido | `TRANSPORTE_PESOS`, `TRANSPORTE_MODOS_TRILHO` |
| Mudar os pesos de alagamento ou barulho | `ALAGAMENTO_PESOS`, `BARULHO_PESOS` |
| Mudar os raios (escolas, estações) | `ESCOLA_RAIO_*`, `TRANSPORTE_RAIO_M` |
| Mudar os pesos de escola por tipo | `ESCOLAS_PESOS` |
| Mudar o período (meses) do ISP, do 1746 ou do ITBI | `VIOLENCIA_MESES`, `BARULHO_1746_MESES`, `ITBI_MESES` |
| Usar outra edição do Ideb | `IDEB_ANO` + `bash etl/ferramentas/baixar_dados.sh` |
| Mudar o comprometimento de renda (30%) ou os avisos do simulador | `etl/10_parametros_financiamento.py` |
| Mudar a cota máxima de financiamento (% do imóvel que o banco financia) | bloco `COTA_MAX` em `etl/10_parametros_financiamento.py` |
| Mudar textos e visual | `site/index.html`, `site/app.js`, `site/style.css` |

As decisões já tomadas, e por quê, estão registradas em `docs/ESCOPO.md`.

---

## 8. Problemas comuns

| Sintoma | Causa e solução |
|---|---|
| `download.inep.gov.br`: erro de certificado ("unknown CA") | O servidor do INEP envia a cadeia de certificados incompleta. Os scripts usam `etl/ca_inep.pem`, que completa a cadeia com o intermediário oficial da RNP/GlobalSign sem desligar a verificação. Se o certificado deles mudar, gere o arquivo de novo: veja o emissor com `openssl s_client -connect download.inep.gov.br:443`, baixe o intermediário pelo endereço "CA Issuers" e junte ao arquivo de certificados do sistema. |
| `download.inep.gov.br` ou `pgeo3.rio.rj.gov.br` não respondem | Instabilidade do servidor deles (acontece). Tente mais tarde. Os scripts não apagam nada que já estava baixado. |
| `DefaultCredentialsError` no BigQuery | Falta o login: `~/google-cloud-sdk/bin/gcloud auth application-default login`, marcando todas as permissões. |
| `Access Denied` ou `project not found` no BigQuery | Use o **ID** do projeto (não o nome) em `BQ_PROJETO`. |
| `Falta o shapefile das CISPs` | Rode `bash etl/ferramentas/baixar_dados.sh` (precisa do `unrar`). |
| `Falta o CSV do Catálogo de Escolas` | Faça o download manual (seção 4.2). |
| Script lista "nomes de bairro não reconhecidos" | Acrescente o apelido em `APELIDOS_BAIRRO`, no `etl/comum.py`. Exemplo: `"SAO CRISTOVAO": "Imperial de São Cristóvão"`. |
| Prévia antiga no WhatsApp | O WhatsApp guarda a prévia de cada link por alguns dias. Links novos pegam a versão atual. |
| Publicação falhou no GitHub | Ver seção 6 (rodar de novo). |

---

## 9. Licenças e créditos

- **Dados:** são de fontes públicas oficiais. Cada uma está citada no app ("Sobre os dados") e em `docs/FONTES.md`.
- **Fontes tipográficas:** Nunito e Quicksand, SIL Open Font License (`site/fonts/OFL-*.txt`), do repositório oficial `google/fonts`.
- **Ilustração e mapa:** desenho próprio (`etl/ferramentas/gerar_ilustracao.py` e `etl/11_mapa.py`, a partir da malha oficial de bairros do IPP).
- **Código:** sem licença definida até o momento. Sem licença, o código é público para leitura, mas não pode ser reaproveitado legalmente por terceiros.
