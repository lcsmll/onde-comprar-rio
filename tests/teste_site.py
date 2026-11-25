"""
Teste do site no navegador (Chrome instalado, via Playwright), em tamanho de celular e de computador.

Como rodar (com o servidor local ligado; ou contra o site publicado com URL_SITE=...):
    cd site && python3 -m http.server 8765 --bind 127.0.0.1      (em outro terminal)
    .venv/bin/python tests/teste_site.py
Capturas de tela vao para tests/capturas/.
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

import os
URL = os.environ.get("URL_SITE", "http://127.0.0.1:8765/")  # ex.: URL_SITE=https://lcsmll.github.io/onde-comprar-rio/
CAP = Path(__file__).parent / "capturas"
CAP.mkdir(exist_ok=True)
erros, falhas = [], []


def checar(cond, msg):
    print(("OK   " if cond else "FALHA") + " " + msg)
    if not cond:
        falhas.append(msg)


def fluxo(page, nome):
    page.on("console", lambda m: erros.append(f"[{nome}] console {m.type}: {m.text}") if m.type == "error" else None)
    page.on("pageerror", lambda e: erros.append(f"[{nome}] pageerror: {e}"))
    page.goto(URL)
    page.wait_for_selector("#tela-inicio:not([hidden])")
    page.screenshot(path=CAP / f"{nome}_0_inicio.png", full_page=True)
    page.click("text=Começar")

    # perfil
    page.click("[data-perfil=familia]")
    checar(page.is_visible("#bloco-escola"), "pergunta de escola aparece para familia")
    page.click("[data-escola=publica]")
    page.screenshot(path=CAP / f"{nome}_1_perfil.png", full_page=True)
    page.click("#avancar-perfil")

    # renda
    checar(not page.is_visible("#renda2"), "renda unica: campo do 2o comprador escondido")
    checar("Sua renda" in page.inner_text("#tela-renda"), "renda unica: texto fala com 'voce'")
    page.click("[data-renda-tipo=somada]")
    checar(page.is_visible("#renda2"), "renda somada: campo do 2o comprador aparece")
    page.fill("#renda1", "6000")
    page.fill("#renda2", "3500")
    page.fill("#fgts", "30000")
    page.check("#cotista")
    page.fill("#entrada", "80000")
    checar(page.input_value("#renda1") == "R$\xa06.000", f"campo de dinheiro formata ({page.input_value('#renda1')!r})")
    page.screenshot(path=CAP / f"{nome}_2_renda.png", full_page=True)
    page.click("#tela-renda >> text=Avançar")

    # imovel
    checar(page.is_visible("#trabalho2"), "familia: campo de trabalho da 2a pessoa aparece")
    page.click("[data-tipo=apartamento]")
    page.fill("#area", "70")
    page.fill("#preco-max", "350000")
    page.select_option("#trabalho1", "polo:centro")
    page.screenshot(path=CAP / f"{nome}_3_imovel.png", full_page=True)
    page.click("#tela-imovel >> text=Avançar")

    # prioridades
    checar(page.input_value("#peso-escolas") == "5", "peso padrao familia: escolas = 5")
    page.screenshot(path=CAP / f"{nome}_4_prioridades.png", full_page=True)
    page.click("text=Ver bairros")

    # resultado
    page.wait_for_selector("#lista-bairros li")
    total_bairros = page.evaluate("D.bairros.bairros.filter(b => b.tem_nota).length")
    n = page.locator(".cartao-bairro").count()
    checar(n == min(20, total_bairros), f"lista mostra os primeiros 20 de {total_bairros} ({n})")
    if total_bairros > 20:
        page.click("#ver-mais")
        checar(page.locator(".cartao-bairro").count() == min(40, total_bairros), "Ver mais acrescenta 20 bairros")
        page.fill("#filtro-bairro", "tijuca")
        nomes = page.locator(".cartao-nome").all_inner_texts()
        checar(nomes and all("tijuca" in x.lower() for x in nomes), f"busca por nome ({nomes})")
        page.fill("#filtro-bairro", "")
    n = page.locator(".cartao-bairro").count()
    notas = [float(t.replace(",", ".")) for t in page.locator("#lista-bairros .cartao-nota .anel-valor").all_inner_texts()]
    checar(notas == sorted(notas, reverse=True), "lista em ordem decrescente de nota")
    caros = page.locator(".cartao-bairro .etiqueta:not(.etiqueta-ok):not(.etiqueta-neutra)").count()
    checar(caros > 0, f"bairros acima do orcamento marcados ({caros})")
    page.screenshot(path=CAP / f"{nome}_5_resultado.png", full_page=True)
    page.check("#esconder-caros")
    n2 = page.locator(".cartao-bairro").count()
    checar(page.locator(".cartao-bairro .etiqueta:not(.etiqueta-ok):not(.etiqueta-neutra)").count() == 0,
           f"esconder caros: nenhum bairro acima do orcamento na lista ({n2} mostrados)")
    so_cabem = page.locator(".cartao-bairro .etiqueta-ok").count()
    checar(so_cabem == n2, f"filtro mostra so bairros que cabem ({so_cabem} de {n2})")
    page.uncheck("#esconder-caros")

    # quanto cabe no bolso
    painel = page.inner_text("#painel-orcamento")
    checar("Seu orçamento" in painel and "Imóvel de até" in painel, "painel de orcamento aparece com renda informada")
    checar(page.locator(".bolso-linha").count() == page.locator(".cartao-bairro").count(), "cada bairro mostra o bloco do bolso")
    page.select_option("#ordenar", "parcela")
    parcelas = [float(t.split("R$")[1].replace(".", "").replace(",", ".").strip())
                for t in page.locator(".bolso-linha > div:nth-child(3) strong").all_inner_texts()]
    checar(parcelas == sorted(parcelas), f"ordenar por menor parcela ({parcelas[:3]}...)")
    page.select_option("#ordenar", "nota")
    print("     painel:", " | ".join(painel.split("\n")[:5]))

    # comparar
    checar(page.is_hidden("#barra-comparar"), "barra de comparar escondida sem selecao")
    botoes = page.locator(".btn-comparar")
    botoes.nth(0).click()
    checar(page.is_visible("#barra-comparar") and page.is_disabled("#barra-comparar-ir"), "1 bairro: barra aparece, botao pede mais 1")
    page.locator(".btn-comparar").nth(1).click()
    page.locator(".btn-comparar").nth(2).click()
    page.locator(".btn-comparar").nth(3).click()          # 4o: deve recusar
    checar("até 3" in page.inner_text("#barra-comparar-msg"), "limite de 3 bairros avisado")
    checar(page.locator(".btn-comparar[aria-pressed=true]").count() == 3, "3 bairros marcados")
    checar(page.is_visible("#tela-resultado"), "marcar para comparar nao abre o detalhe")
    page.click("#barra-comparar-ir")
    page.wait_for_selector("#tela-comparar:not([hidden]) table.cmp")
    cols = page.locator("table.cmp thead th").count() - 1
    checar(cols == 3, f"comparacao com 3 colunas ({cols})")
    checar(page.locator("table.cmp td.melhor").count() >= 7, "melhor de cada linha destacado")
    checar(page.locator(".cmp-resumo li").count() == 3, "resumo em texto com os 3 bairros")
    page.locator(".cmp-det summary").first.click()
    checar(page.locator(".cmp-det[open] .cmp-ind tbody tr").count() == 4, "violencia aberta mostra os 4 indicadores")
    checar("comparar/" in page.url and "6000" not in page.url, f"link da comparacao so com bairros ({page.url.split('#')[1]})")
    checar(page.locator("#mapa-comparar .m-atual").count() == 3, "mapa da comparacao destaca os 3")
    checar(page.locator("#tela-comparar .rd-serie").count() == 3, "radar da comparacao com 3 bairros")
    page.screenshot(path=CAP / f"{nome}_9_comparar.png", full_page=True)
    page.click("#barra-comparar-limpar") if page.is_visible("#barra-comparar") else None
    page.goto(URL + "#resultado")
    page.wait_for_selector("#lista-bairros li")
    page.click("#barra-comparar-limpar")
    checar(page.is_hidden("#barra-comparar"), "limpar esvazia a comparacao")

    # detalhe
    primeiro = page.locator(".cartao-nome").first.inner_text()
    page.locator(".cartao-bairro").first.click()
    page.wait_for_selector("#tela-bairro:not([hidden])")
    checar(page.locator(".criterio").count() == 6, "detalhe mostra 6 criterios")
    resumo = page.inner_text(".perfil-bairro")
    checar("bairros do Rio" in resumo and page.locator(".perfil-bairro .rd-serie").count() == 1,
           "detalhe: resumo em texto e radar")
    # o texto tem que bater com as notas: cada "a frente de X%" corresponde a uma nota X/10 mostrada
    import re
    notas_txt = {round(float(x.replace(",", ".")) / 10, 1) for x in re.findall(r"frente de (\d+)%", resumo)}
    notas_crit = {round(float(t.replace(",", ".")), 1) for t in page.locator(".criterio .anel-valor").all_inner_texts()}
    checar(notas_txt <= {round(v, 1) for v in notas_crit} or not notas_txt,
           f"resumo coerente com as notas ({sorted(notas_txt)})")
    href = page.get_attribute("#whats", "href")
    checar(href.startswith("https://wa.me/?text=") and "%2Fbairro%2F" in href and "6000" not in href and "9500" not in href,
           "botao WhatsApp compartilha a pagina do bairro, sem renda")
    page.click("#add-comparar")
    checar("Na comparação" in page.inner_text("#add-comparar") and page.is_visible("#barra-comparar"),
           "detalhe: adicionar a comparacao")
    page.click("#add-comparar")
    checar(page.locator(".links-portais a").count() >= 4, "links dos portais presentes")
    hrefs = page.locator(".links-portais a").evaluate_all("els => els.map(e => e.href)")
    print("     links:", hrefs[:3])
    page.screenshot(path=CAP / f"{nome}_6_bairro.png", full_page=True)

    # simulador
    page.click("#ir-simulador")
    page.wait_for_selector("#s-resultado .tabela")
    linha = page.locator("#s-resultado h3").first.inner_text()
    print("     ", primeiro.replace("\n", " "), "->", linha)
    checar("Linha provável" in linha, "simulador mostra linha provavel")
    checar(page.locator("text=Renda única x somada").count() == 1, "comparacao renda unica x somada")
    page.fill("#s-preco", "300000")
    page.wait_for_timeout(200)
    linha2 = page.locator("#s-resultado h3").first.inner_text()
    print("      preco 300 mil ->", linha2)
    checar("MCMV" in linha2, "renda 9.500 e imovel de 300 mil -> MCMV Faixa 3")
    page.fill("#a-aluguel", "1800")
    page.fill("#a-extras", "600")
    checar(page.locator("#a-resultado .tabela").count() == 1, "comparacao com aluguel aparece")
    page.fill("#s-entrada", "90000")       # recalcular nao pode apagar o aluguel
    page.wait_for_timeout(200)
    checar(page.input_value("#a-aluguel") != "", "valor do aluguel se mantem apos recalcular")
    page.screenshot(path=CAP / f"{nome}_7_simulador.png", full_page=True)

    # sobre
    page.click("text=Sobre os dados")
    page.wait_for_selector("#tela-sobre:not([hidden])")
    checar(page.locator(".sobre-fonte").count() >= 9, "pagina Sobre os dados com todas as secoes")
    page.screenshot(path=CAP / f"{nome}_8_sobre.png", full_page=True)

    # largura: nada pode passar da tela no celular
    larg = page.evaluate("document.documentElement.scrollWidth"), page.viewport_size["width"]
    checar(larg[0] <= larg[1], f"sem rolagem horizontal ({larg[0]} <= {larg[1]})")

    # sem renda: painel convida a informar
    page.goto(URL + "?p=casal&w=444443&e=tanto_faz#resultado")
    page.wait_for_selector("#lista-bairros li")
    checar("Quer ver quanto cabe" in page.inner_text("#painel-orcamento"), "sem renda: painel convida a informar")

    # solteiro: nada de 2a pessoa
    page.goto(URL + "#perfil")
    page.click("[data-perfil=solteiro]")
    page.click("#avancar-perfil")
    page.click("[data-renda-tipo=unica]")
    checar(not page.is_visible("#renda2"), "voltar para renda unica esconde o 2o comprador")
    page.click("#tela-renda >> text=Avançar")
    checar(not page.is_visible("#trabalho2"), "solteiro: sem campo de trabalho da 2a pessoa")

    # bairro sem nota final (subnotificacao em area de favela)
    sem = page.evaluate("(D.bairros.bairros.find(b => b.sem_nota_final) || {}).codbairro")
    if sem:
        page.goto(URL + "#bairro/" + sem)
        page.wait_for_selector(".perfil-bairro")
        checar(page.locator(".detalhe-nota .anel-valor").inner_text() == "-" and page.locator("#tela-bairro .aviso").count() >= 2,
               "bairro sem nota final: sem nota e com explicacao")

    # perguntas frequentes: numeros vindos do JSON
    page.click(".nav-topo >> text=Dúvidas")
    page.wait_for_selector("#tela-perguntas:not([hidden]) .pergunta")
    checar(page.locator(".pergunta").count() == 15, f"15 perguntas frequentes ({page.locator('.pergunta').count()})")
    page.locator(".pergunta summary", has_text="Minha Casa").click()
    r = page.locator(".pergunta[open] .resposta").inner_text().replace("\xa0", " ")
    checar("Faixa 3" in r and "R$ 400.000" in r and "SBPE" in r, "resposta do MCMV com faixas e tetos do JSON")

    # impressao: botoes e cabecalho somem, cabecalho de impressao aparece, detalhes abrem
    page.goto(URL + "#comparar/033,043")
    page.wait_for_selector("table.cmp")
    page.evaluate("window.print = () => {}")          # nao abrir a janela de impressao no teste
    page.locator("#comparacao [data-imprimir]").click()
    page.emulate_media(media="print")
    page.evaluate("window.dispatchEvent(new Event('beforeprint'))")
    checar(page.is_hidden(".topo") and page.is_visible("#cabecalho-impressao") and "Comparação" in page.inner_text("#cabecalho-impressao"),
           "impressao: some o cabecalho do site, aparece o cabecalho de impressao")
    checar(page.locator(".cmp-det[open]").count() == 6, "impressao: secoes fechadas abrem")
    page.evaluate("window.dispatchEvent(new Event('afterprint'))")
    page.emulate_media(media="screen")
    checar(page.locator(".cmp-det[open]").count() == 0, "depois de imprimir, as secoes voltam a fechar")

    # pagina do bairro (previa do WhatsApp): etiquetas Open Graph e redirecionamento para o app
    page.goto(URL + "bairro/tijuca/")
    page.wait_for_selector("#tela-bairro:not([hidden])")
    checar("#bairro/033" in page.url and page.locator(".detalhe-topo h2").inner_text() == "Tijuca",
           "pagina bairro/tijuca/ abre a Tijuca no app")
    import urllib.request
    pagina = urllib.request.urlopen(URL + "bairro/tijuca/").read().decode()
    checar(all(t in pagina for t in ('og:title', 'og:image" content="https://', 'og:description', 'Tijuca: nota')),
           "pagina do bairro tem as etiquetas de previa (Open Graph)")

    # link compartilhado: abre com perfil e pesos
    page.goto(URL + "?p=solteiro&w=111155&e=tanto_faz#resultado")
    page.wait_for_selector("#lista-bairros li")
    checar(page.locator(".cartao-bairro").count() > 0, "link compartilhado abre o resultado direto")
    url_tem_renda = "6000" in page.url or "renda" in page.url
    checar(not url_tem_renda, "link nao contem renda")


def main():
    with sync_playwright() as p:
        nav = p.chromium.launch(channel="chrome", headless=True)
        cel = nav.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2,
                              is_mobile=True, has_touch=True, locale="pt-BR")
        fluxo(cel.new_page(), "celular")
        pc = nav.new_context(viewport={"width": 1280, "height": 900}, locale="pt-BR")
        fluxo(pc.new_page(), "computador")
        nav.close()
    print("\nErros de JavaScript:", erros or "nenhum")
    print(f"Falhas: {len(falhas)}")
    sys.exit(1 if falhas or erros else 0)


if __name__ == "__main__":
    main()
