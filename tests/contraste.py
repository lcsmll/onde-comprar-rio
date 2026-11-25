"""
Auditoria de contraste (WCAG): mede cada texto visivel contra a cor de fundo real atras dele.
Minimo: 4,5:1 (texto normal) e 3:1 (texto grande: >= 24px, ou >= 18,66px em negrito).
Roda no celular (tema claro e escuro: o site deve ficar claro nos dois) e no computador.
    .venv/bin/python tests/contraste.py          (servidor local ligado; ou URL_SITE=...)
"""
import os
import sys

from playwright.sync_api import sync_playwright

URL = os.environ.get("URL_SITE", "http://127.0.0.1:8765/")
JS = r"""
() => {
  // aceita "rgb(r, g, b)", "rgba(...)" e "color(srgb r g b / a)" (este ultimo vem em fracoes de 0 a 1)
  const rgb = (c) => { const m = c.match(/[\d.]+/g); if (!m) return [0,0,0,0]; const v = m.map(Number);
    if (c.startsWith("color(")) { const [r,g,b,a=1] = v; return [r*255, g*255, b*255, a]; } return v; };
  const lum = ([r,g,b]) => { const f = (v) => { v/=255; return v <= .03928 ? v/12.92 : ((v+.055)/1.055)**2.4; };
    return .2126*f(r) + .7152*f(g) + .0722*f(b); };
  const fundo = (el) => { while (el) { const c = rgb(getComputedStyle(el).backgroundColor);
      if (c.length < 4 || c[3] > .5) return c.slice(0,3); el = el.parentElement; } return [255,255,255]; };
  const ruins = [];
  for (const el of document.querySelectorAll("body *")) {
    const temTexto = [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
    if (!temTexto) continue;
    const r = el.getBoundingClientRect(), cs = getComputedStyle(el);
    if (!r.width || !r.height || cs.visibility === "hidden" || el.closest("[hidden]") || el.closest("svg")) continue;
    const a = lum(rgb(cs.color)), b = lum(fundo(el));
    const razao = (Math.max(a,b) + .05) / (Math.min(a,b) + .05);
    const tam = parseFloat(cs.fontSize), negrito = parseInt(cs.fontWeight) >= 700;
    const minimo = (tam >= 24 || (tam >= 18.66 && negrito)) ? 3 : 4.5;
    if (razao < minimo) ruins.push(`${razao.toFixed(2)} < ${minimo} | ${el.tagName.toLowerCase()}.${el.className} | "${el.textContent.trim().slice(0,40)}" | cor ${cs.color} fundo rgb(${fundo(el)})`);
  }
  return ruins;
}
"""


def main():
    total = 0
    with sync_playwright() as p:
        nav = p.chromium.launch(channel="chrome", headless=True)
        for tema, disp, vp in (("light", "celular", {"width": 390, "height": 844}), ("dark", "celular", {"width": 390, "height": 844}),
                               ("light", "computador", {"width": 1366, "height": 900})):
            pg = nav.new_context(viewport=vp, is_mobile=disp == "celular", color_scheme=tema).new_page()
            telas = {}
            pg.goto(URL); pg.wait_for_selector("#exemplo .anel"); telas["inicio"] = pg.evaluate(JS)
            pg.click("text=Começar"); pg.click("[data-perfil=familia]"); telas["perfil"] = pg.evaluate(JS)
            pg.click("#avancar-perfil"); pg.fill("#renda1", "9500"); pg.fill("#entrada", "80000"); telas["renda"] = pg.evaluate(JS)
            pg.click("#tela-renda >> text=Avançar"); pg.fill("#area", "70"); pg.click("#tela-imovel >> text=Avançar"); telas["prioridades"] = pg.evaluate(JS)
            pg.click("text=Ver bairros"); pg.wait_for_selector("#lista-bairros li")
            pg.locator(".btn-comparar").nth(0).click(); pg.locator(".btn-comparar").nth(1).click(); telas["resultado"] = pg.evaluate(JS)
            pg.locator(".cartao-bairro").first.click(); pg.wait_for_selector(".perfil-bairro"); telas["bairro"] = pg.evaluate(JS)
            pg.click("#ir-simulador"); pg.wait_for_selector("#s-resultado .tabela"); telas["simulador"] = pg.evaluate(JS)
            pg.goto(URL + "#comparar/033,043,065"); pg.wait_for_selector("table.cmp")
            pg.locator(".cmp-det summary").first.click(); telas["comparar"] = pg.evaluate(JS)
            pg.goto(URL + "#sobre"); pg.wait_for_selector(".sobre-fonte"); telas["sobre"] = pg.evaluate(JS)
            fundo = pg.evaluate("getComputedStyle(document.body).backgroundColor")
            print(f"\n=== {disp}, tema do sistema: {tema} | fundo da pagina: {fundo}")
            for t, ruins in telas.items():
                total += len(ruins)
                print(f"  {t:12} {'OK' if not ruins else str(len(ruins)) + ' problema(s)'}")
                for r in ruins[:6]:
                    print("      ", r)
        nav.close()
    print(f"\nTotal de textos com contraste insuficiente: {total}")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
