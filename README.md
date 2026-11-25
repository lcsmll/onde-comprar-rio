# Onde Comprar no Rio

App de navegador que ajuda a escolher um bairro para comprar imóvel no município do Rio de Janeiro e a simular o financiamento.

**Acesse:** https://lcsmll.github.io/onde-comprar-rio/

- **6 critérios com nota de 0 a 10:** segurança, menos alagamento, escolas, transporte, emprego e menos barulho. A nota é a posição do bairro entre os bairros do Rio.
- **Quanto cabe no bolso:** preço máximo do imóvel, área que cabe e 1ª parcela estimada em cada bairro.
- **Comparar bairros** lado a lado, **mapa** e **simulador** (SAC x Price, MCMV ou SBPE, renda única ou somada, ITBI).
- **Só dados oficiais e gratuitos:** ISP-RJ, Data.Rio / Prefeitura, INEP, IBGE, Caixa, Banco Central e Ministério das Cidades.
- **Privacidade:** tudo roda no navegador. Nada do que a pessoa digita é enviado ou guardado.

Versão inicial com 15 bairros. Fontes e métodos: página "Sobre os dados" do app, `docs/FONTES.md` e `docs/ESCOPO.md`.

## Estrutura

```
etl/      scripts Python que baixam e tratam os dados (rodar: bash etl/rodar_tudo.sh)
site/     o app (HTML, CSS e JavaScript puro) e os JSON gerados pelo ETL
docs/     fontes de dados e escopo
tests/    teste do site no navegador (Playwright)
```

O passo a passo completo para atualizar os dados será documentado aqui na próxima etapa.

*Simulação estimada. A aprovação e as condições finais dependem do banco.*
