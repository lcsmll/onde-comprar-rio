/*
 * Onde Comprar no Rio - app do navegador (JavaScript puro, sem framework).
 *
 * Como funciona:
 *  - Carrega os JSON gerados pelo ETL (site/data/). Nenhum numero de regra fica neste arquivo:
 *    pesos, faixas do MCMV, juros, ITBI etc. vem dos JSON.
 *  - Tudo o que o usuario digita fica so na memoria desta pagina (variavel `estado`).
 *    Nao ha envio, cookie nem armazenamento. Ao fechar a aba, tudo some.
 *  - Navegacao por "#tela" no endereco (botao voltar do celular funciona).
 */
"use strict";

// Nomes no sentido positivo: em todos os criterios, nota alta = melhor
// (ex.: "Menos alagamento" 8 = alaga menos que 80% dos bairros do Rio).
const ROTULOS = {
  violencia: "Segurança", alagamento: "Menos alagamento", escolas: "Escolas",
  transporte: "Transporte", emprego: "Emprego", barulho: "Menos barulho",
};
// Como cada criterio aparece no texto quando e ponto forte...
const TXT_FORTE = {
  violencia: "segurança", alagamento: "pouco alagamento", escolas: "escolas",
  transporte: "transporte", emprego: "acesso ao emprego", barulho: "pouco barulho",
};
// ...e quando e ponto de atencao (ai o nome do problema e o que faz sentido)
const TXT_ATENCAO = {
  violencia: "Violência", alagamento: "Alagamento", escolas: "Poucas escolas",
  transporte: "Transporte", emprego: "Distância do emprego", barulho: "Barulho",
};
const EXPLICA = {
  violencia: "Mortes violentas e roubos por 100 mil habitantes (ISP). Nota alta = menos ocorrências.",
  alagamento: "Suscetibilidade a inundação e alagamentos registrados. Nota alta = alaga menos.",
  escolas: "Quantidade de escolas perto de casa e Ideb das públicas.",
  transporte: "Distância até a estação mais próxima (metrô, trem, BRT ou VLT); metrô e trem contam mais.",
  emprego: "Distância até os polos de emprego (ou até onde você trabalha).",
  barulho: "Reclamações de barulho, vias movimentadas, trilhos e aeroportos. Nota alta = menos barulho.",
};

// Icones simples (linhas), desenhados para este app
const ICONES = {
  violencia: '<path d="M12 3l8 3v6c0 4.5-3.4 8.3-8 9-4.6-.7-8-4.5-8-9V6z"/>',
  alagamento: '<path d="M12 3c3.5 4.2 6 7.6 6 10.5a6 6 0 0 1-12 0C6 10.6 8.5 7.2 12 3z"/>',
  escolas: '<path d="M3 9l9-5 9 5-9 5z"/><path d="M7 11.5V16c1.5 1.4 3.2 2 5 2s3.5-.6 5-2v-4.5"/>',
  transporte: '<rect x="5" y="3" width="14" height="14" rx="3"/><path d="M5 10h14M8 21l2-4M16 21l-2-4"/>',
  emprego: '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M9 7V4h6v3M3 13h18"/>',
  barulho: '<path d="M4 10v4h4l5 4V6L8 10z"/><path d="M16.5 8.5a5 5 0 0 1 0 7M19 6a8.5 8.5 0 0 1 0 12"/>',
  preco: '<path d="M3 12V4h8l10 10-8 8z"/><circle cx="7.5" cy="7.5" r="1.5"/>',
  local: '<path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
  whats: '<path d="M4 20l1.3-3.9A8 8 0 1 1 8 19z"/><path d="M9 9.5c0 3 2.5 5.5 5.5 5.5l1.2-1.4-2-1-1 .8a4 4 0 0 1-2.1-2.1l.8-1-1-2z"/>',
};
const icone = (k, cls = "icone") => `<svg class="${cls}" viewBox="0 0 24 24" aria-hidden="true">${ICONES[k]}</svg>`;

// Anel com a nota (0 a 10): o arco preenchido e proporcional a nota
function anel(nota, tam = 64) {
  const r = 26, c = 2 * Math.PI * r, f = nota == null ? 0 : Math.max(0, Math.min(10, nota)) / 10;
  return `<div class="anel" style="width:${tam}px;height:${tam}px">
    <svg viewBox="0 0 64 64" aria-hidden="true"><circle class="anel-fundo" cx="32" cy="32" r="${r}"/>
      ${nota == null ? "" : `<circle class="anel-cheio" cx="32" cy="32" r="${r}" stroke-dasharray="${c * f} ${c}" transform="rotate(-90 32 32)"/>`}</svg>
    <span class="anel-valor">${nota == null ? "-" : fmtN(nota)}</span></div>`;
}

// Criterio com maior e menor nota (texto neutro: e posicao na cidade, nao rotulo)
function destaques(n) {
  const cs = D.bairros.criterios.filter((c) => n[c] != null);
  if (!cs.length) return "";
  const melhor = cs.reduce((a, c) => (n[c] > n[a] ? c : a)), pior = cs.reduce((a, c) => (n[c] < n[a] ? c : a));
  const forte = TXT_FORTE[melhor][0].toUpperCase() + TXT_FORTE[melhor].slice(1);
  return `<div class="chips"><span class="chip chip-bom">${icone(melhor)}Destaque: ${forte} ${fmtN(n[melhor])}</span>
    <span class="chip chip-atencao">${icone(pior)}Atenção: ${TXT_ATENCAO[pior]} ${fmtN(n[pior])}</span></div>`;
}

// "Zona Norte · região Madureira" (a regiao so aparece quando e diferente do nome do bairro)
function localTexto(b) {
  const z = { "zona-norte": "Zona Norte", "zona-oeste": "Zona Oeste", "zona-sul": "Zona Sul", centro: "Centro" }[D.portais.zona_por_regiao[b.regiao]];
  return [z, b.regiao !== b.nome && b.regiao !== z ? "região " + b.regiao : null].filter(Boolean).join(" · ");
}

let D = {};            // dados carregados (bairros, parametros, caixa, portais)
let distancias = null; // carregado sob demanda (opcao "outro bairro")
const estado = {
  perfil: null, escola: "tanto_faz",
  rendaTipo: "unica", renda1: 0, renda2: 0, fgts: 0, entrada: 0, cotista: false, jaTemImovel: false,
  tipo: "", area: null, precoMax: null,
  trabalho: ["", ""],
  pesos: null, esconderCaros: false,
  bairroAtual: null, telaAnterior: "resultado",
  aluguel: 0, extras: 0, mapaCidade: false, mapaRegiao: "cidade", mapaSel: null, ordem: "nota", comparar: [], limite: 20, filtro: "",
};

/* ---------------- utilidades ---------------- */
const $ = (s) => document.querySelector(s);
const $$ = (s) => Array.from(document.querySelectorAll(s));
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fmtR = (v) => v == null || isNaN(v) ? "-" :
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });
const fmtN = (v, casas = 1) => v == null || isNaN(v) ? "-" :
  Number(v).toLocaleString("pt-BR", { minimumFractionDigits: casas, maximumFractionDigits: casas });
const MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"];
const mesAno = (iso) => { const [a, m] = iso.split("-"); return `${MESES[Number(m) - 1]} de ${a}`; };
const fmtData = (iso) => iso ? iso.split("-").reverse().join("/") : "-";
const lerDinheiro = (s) => Number(String(s).replace(/\D/g, "")) || 0;
// texto para busca: minusculo e sem acento
const norm = (s) => String(s || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();
const slug = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase()
  .replace(/[()]/g, "").trim().replace(/\s+/g, "-");

/* ---------------- carregamento ---------------- */
async function carregar() {
  const pegar = (a) => fetch("data/" + a).then((r) => { if (!r.ok) throw new Error(a); return r.json(); });
  const [bairros, params, caixa, portais, mapa] = await Promise.all([
    pegar("bairros.json"), pegar("parametros_financiamento.json"),
    pegar("imoveis_caixa.json").catch(() => ({ imoveis: [] })), pegar("links_portais.json"),
    pegar("mapa.json").catch(() => null),
  ]);
  D = { bairros, params, caixa, portais, mapa };
}

async function carregarDistancias() {
  if (!distancias) distancias = await fetch("data/distancias.json").then((r) => r.json());
  return distancias;
}

/* ---------------- notas ---------------- */
// Mesma regra do ETL: 10 x (fracao dos outros bairros de referencia que estao pior + metade dos empates).
function notaPercentil(valor, refValores, maiorEPior, incluiProprio) {
  if (valor == null) return null;
  const outros = refValores.slice();
  if (incluiProprio) { const i = outros.indexOf(valor); if (i >= 0) outros.splice(i, 1); }
  let pior = 0, empate = 0;
  for (const v of outros) {
    if (v === valor) empate++;
    else if (maiorEPior ? v > valor : v < valor) pior++;
  }
  return 10 * (pior + 0.5 * empate) / outros.length;
}

// Distancia (km) do bairro "origem" ate um local de trabalho escolhido.
function distTrabalho(cod, local, bairroObj) {
  if (local.startsWith("polo:")) {
    const k = local.slice(5);
    return bairroObj ? bairroObj.criterios.emprego.dist_km[k] : D.bairros.emprego.referencia_km[k][cod];
  }
  const dest = local.slice(7); // "bairro:XYZ"
  const i = distancias.origens.indexOf(cod), j = distancias.destinos.indexOf(dest);
  return i < 0 || j < 0 ? null : distancias.km[i][j];
}

function notaEmprego(b) {
  const locais = estado.trabalho.filter(Boolean);
  if (!locais.length) return b.criterios.emprego.nota;
  const ref = D.bairros.referencia_codigos;
  const media = (cod, obj) => {
    const ds = locais.map((l) => distTrabalho(cod, l, obj)).filter((x) => x != null);
    return ds.length ? ds.reduce((a, c) => a + c, 0) / ds.length : null;
  };
  const refVals = ref.map((c) => media(c, null)).filter((x) => x != null).map((x) => Math.round(x * 100) / 100);
  const v = media(b.codbairro, null) ?? media(b.codbairro, b);
  return notaPercentil(v == null ? null : Math.round(v * 100) / 100, refVals, true, ref.includes(b.codbairro));
}

function notasDoBairro(b) {
  const n = {};
  for (const c of D.bairros.criterios) {
    const cr = b.criterios[c];
    if (c === "escolas") n[c] = cr.nota_por_tipo ? cr.nota_por_tipo[estado.escola] : cr.nota;
    else if (c === "emprego") n[c] = notaEmprego(b);
    else n[c] = cr.nota;
  }
  const P = estado.pesos || Object.fromEntries(D.bairros.criterios.map((c) => [c, 3]));
  let soma = 0, pesos = 0;
  for (const c of D.bairros.criterios) {
    if (n[c] == null) continue;
    soma += n[c] * P[c]; pesos += P[c];
  }
  n.final = pesos && !b.sem_nota_final ? soma / pesos : null;
  return n;
}

/* ---------------- quanto cabe no bolso ---------------- */
// Premissas (as mesmas do simulador): parcela ate X% da renda bruta (JSON), sistema SAC
// (1a parcela e a maior: conta conservadora), prazo padrao do JSON, juros da linha provavel.
const rendaTotal = () => estado.renda1 + (estado.rendaTipo === "somada" ? estado.renda2 : 0);

// Preco maximo do imovel que cabe na renda. Se o preco passa do teto do MCMV, vale o SBPE:
// o maximo e o maior entre "o que cabe no MCMV (limitado ao teto)" e "o que cabe no SBPE".
function orcamento() {
  const renda = rendaTotal();
  if (!renda) return null;
  const anos = D.params.prazo_padrao_anos;
  const f = faixaMCMV(renda);
  const opcoes = [];
  if (f) {
    const j = estado.cotista ? f.juros_cotista : f.juros_nao_cotista;
    const c = capacidade(renda, j, anos, f.teto_imovel, "mcmv").sac;
    opcoes.push({ linha: "MCMV - " + f.faixa, juros: j, preco: c.preco, lim: c, teto: f.teto_imovel });
  }
  const js = D.params.sbpe.juros_ano;
  const c = capacidade(renda, js, anos, null, "sbpe").sac;
  opcoes.push({ linha: "SBPE", juros: js, preco: c.preco, lim: c, teto: null });
  const melhor = opcoes.reduce((a, o) => (o.preco > a.preco ? o : a));
  const limiteUsuario = estado.precoMax || null;
  return { renda, anos, pmax: renda * D.params.comprometimento_renda_max, opcoes, melhor,
           precoMax: limiteUsuario ? Math.min(melhor.preco, limiteUsuario) : melhor.preco, limiteUsuario };
}

// Para um bairro: preco estimado da area pedida, 1a parcela (SAC) e area maxima que cabe.
function custoNoBairro(b, orc) {
  if (!b.preco_itbi) return null;
  const rs = b.preco_itbi.rs_m2;
  const areaUsada = estado.area || b.preco_itbi.area_media_m2;
  const preco = rs * areaUsada;
  const out = { rs, areaUsada, areaInformada: !!estado.area, preco };
  if (!orc) return out;
  const lin = linha(orc.renda, preco);
  const V = Math.max(preco - estado.entrada - estado.fgts, 0);
  out.linha = lin.nome;
  out.parcela = sac(V, taxaMensal(lin.juros), orc.anos * 12).primeira;
  out.areaMax = Math.floor(orc.precoMax / rs);
  out.cabe = preco <= orc.precoMax;
  return out;
}

const precoEstimado = (b) => custoNoBairro(b, null)?.preco ?? null;
// "acima do orcamento": com renda informada, pelo que cabe; sem renda, pelo preco maximo digitado
function acimaOrcamento(b) {
  const orc = orcamento(), c = custoNoBairro(b, orc);
  if (!c) return false;
  if (orc) return !c.cabe;
  return !!estado.precoMax && c.preco > estado.precoMax;
}

// faixa fina com os numeros do bolso (cartao da lista)
function blocoBolsoCompacto(c) {
  if (!c) return `<p class="bolso-fino pequeno">Sem vendas registradas no ITBI no período.</p>`;
  return `<dl class="bolso-fino">
      <div><dt>m² (ITBI)</dt><dd>${fmtR(c.rs)}</dd></div>
      ${c.areaMax != null ? `<div><dt>Cabe até</dt><dd>${c.areaMax > 0 ? "~" + c.areaMax + " m²" : "–"}</dd></div>` : ""}
      ${c.parcela != null ? `<div><dt>1ª parcela${c.areaInformada ? ` (${c.areaUsada} m²)` : ""}</dt><dd>${c.parcela > 0 ? fmtR(c.parcela) : "sem financiar"}</dd></div>`
        : `<div><dt>${c.areaInformada ? c.areaUsada + " m²" : "Área média"}</dt><dd>${fmtR(c.preco)}</dd></div>`}
    </dl>`;
}

function painelOrcamento(orc) {
  if (!orc) {
    return `<div class="bolso-painel vazio">${icone("preco")}<div><strong>Quer ver quanto cabe no seu bolso em cada bairro?</strong>
      <span>Informe a renda (e, se tiver, entrada e FGTS) e o app calcula o preço máximo e a parcela em cada bairro.</span>
      <a href="#renda">Informar renda</a></div></div>`;
  }
  const P = D.params, recursos = estado.entrada + estado.fgts;
  return `<div class="bolso-painel">
    <div class="bolso-titulo">${icone("preco")}<strong>Seu orçamento</strong><a href="#renda" class="pequeno">ajustar</a></div>
    <div class="bolso-numeros">
      <div><span>Imóvel de até</span><strong>${fmtR(orc.precoMax)}</strong></div>
      <div><span>Parcela máxima</span><strong>${fmtR(orc.pmax)}</strong></div>
      <div><span>Linha provável</span><strong>${esc(orc.melhor.linha)}</strong></div>
    </div>
    <p class="pequeno">Renda de ${fmtR(orc.renda)} · entrada + FGTS de ${fmtR(recursos)} · SAC em ${orc.anos} anos a
      ${fmtN(orc.melhor.juros, 2)}% ao ano · parcela de até ${P.comprometimento_renda_max * 100}% da renda.
      ${orc.limiteUsuario && orc.limiteUsuario < orc.melhor.preco ? `Limitado ao preço máximo que você definiu (${fmtR(orc.limiteUsuario)}).` : esc(textoLimite(orc.melhor.lim, orc.melhor.teto))}
      ${P.simplificacoes}</p>
  </div>`;
}

function blocoBolso(b, c) {
  if (!c) return `<div class="bolso-linha"><span class="pequeno">Sem vendas registradas no ITBI no período.</span></div>`;
  const ref = c.areaInformada ? `${c.areaUsada} m²` : `${fmtN(c.areaUsada, 0)} m² (área média vendida)`;
  return `<div class="bolso-linha">
      <div><span>m² (ITBI)</span><strong>${fmtR(c.rs)}</strong></div>
      ${c.areaMax != null ? `<div><span>Cabe até</span><strong>${c.areaMax > 0 ? "~" + c.areaMax + " m²" : "-"}</strong></div>` : ""}
      ${c.parcela != null ? `<div><span>1ª parcela</span><strong>${c.parcela > 0 ? fmtR(c.parcela) : "sem financiar"}</strong></div>` : `<div><span>Imóvel</span><strong>${fmtR(c.preco)}</strong></div>`}
    </div>
    <p class="bolso-ref">${c.parcela != null ? `Parcela de um imóvel de ${ref} ≈ ${fmtR(c.preco)} (${esc(c.linha)}).` : `Para ${ref}.`}</p>`;
}

/* ---------------- navegacao ---------------- */
function ir(tela) { location.hash = tela; }

async function mostrar() {
  const h = location.hash.slice(1) || "inicio";
  const [tela, arg] = h.split("/");
  if (["renda", "imovel", "prioridades", "resultado"].includes(tela) && !estado.perfil) return ir("perfil");
  $$(".tela").forEach((s) => (s.hidden = true));
  const alvo = $("#tela-" + tela) || $("#tela-inicio");
  if (tela === "prioridades") desenharPesos();
  if (tela === "resultado") { if (estado.trabalho.some((t) => t.startsWith("bairro:"))) await carregarDistancias(); desenharResultado(); }
  if (tela === "bairro") { estado.bairroAtual = arg; desenharBairro(arg); }
  if (tela === "financiamento") { estado.bairroAtual = arg || estado.bairroAtual; desenharSimulador(); }
  if (tela === "sobre") desenharSobre();
  if (tela === "perguntas") desenharPerguntas();
  if (tela === "comparar") desenharComparacao(arg || "");
  if (!["sobre", "financiamento"].includes(tela)) estado.telaAnterior = h;
  atualizarBarraComparar(tela);
  alvo.hidden = false;
  window.scrollTo(0, 0);
  const t = alvo.querySelector("h1, h2"); if (t) { t.tabIndex = -1; t.focus({ preventScroll: true }); }
}

/* ---------------- formulario ---------------- */
function marcar(grupoSel, attr, valor) {
  $$(grupoSel + " [" + attr + "]").forEach((b) => b.setAttribute("aria-pressed", String(b.getAttribute(attr) === valor)));
}

function escolherPerfil(p, manterPesos) {
  estado.perfil = p;
  if (!manterPesos) estado.pesos = { ...D.bairros.pesos_perfil[p] };
  marcar("#opcoes-perfil", "data-perfil", p);
  $("#bloco-escola").hidden = p !== "familia";
  if (p !== "familia") estado.escola = "tanto_faz";
  marcar("#opcoes-escola", "data-escola", estado.escola);
  $("#avancar-perfil").disabled = false;
  $("#rotulo-trabalho2").hidden = p === "solteiro";
}

function montarSelectTrabalho() {
  const polos = D.bairros.emprego.polos;
  const nomes = Object.entries(D.bairros.todos_bairros).sort((a, b) => a[1].localeCompare(b[1], "pt-BR"));
  const ops = ['<option value="">Não informar</option>']
    .concat(Object.entries(polos).map(([k, p]) => `<option value="polo:${k}">${esc(p.rotulo)}</option>`))
    .concat(['<optgroup label="Outro bairro">'], nomes.map(([c, n]) => `<option value="bairro:${c}">${esc(n)}</option>`), ["</optgroup>"]);
  $("#trabalho1").innerHTML = ops.join("");
  $("#trabalho2").innerHTML = ops.join("");
}

/* ---------------- imprimir / salvar PDF (impressao do navegador, sem servidor) ---------------- */
function imprimir() {
  const tela = location.hash.slice(1).split("/")[0] || "inicio";
  const titulo = { bairro: "Resumo do bairro", financiamento: "Simulação de financiamento", comparar: "Comparação de bairros" }[tela] || "Onde Comprar no Rio";
  $("#cabecalho-impressao").innerHTML = `<strong>Onde Comprar no Rio · ${esc(titulo)}</strong>
    <span>Gerado em ${new Date().toLocaleDateString("pt-BR")} · ${esc(D.bairros.site_url)} · dados de ${fmtData(D.bairros.gerado_em)}</span>
    <span>${esc(D.params.aviso_geral)} Notas de 0 a 10: posição entre os bairros do Rio.</span>`;
  window.print();
}
let detalhesFechados = [];
window.addEventListener("beforeprint", () => {
  detalhesFechados = $$("details:not([open])");
  detalhesFechados.forEach((d) => (d.open = true));
});
window.addEventListener("afterprint", () => detalhesFechados.forEach((d) => (d.open = false)));
document.addEventListener("click", (e) => { if (e.target.closest("[data-imprimir]")) imprimir(); });

function ligarFormulario() {
  document.addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    if (b.dataset.ir) ir(b.dataset.ir);
    if (b.dataset.perfil) escolherPerfil(b.dataset.perfil);
    if (b.dataset.escola) { estado.escola = b.dataset.escola; marcar("#opcoes-escola", "data-escola", estado.escola); }
    if (b.dataset.rendaTipo) {
      estado.rendaTipo = b.dataset.rendaTipo; marcar("#tela-renda", "data-renda-tipo", estado.rendaTipo);
      ajustarTextosRenda();
    }
    if (b.dataset.tipo !== undefined && b.classList.contains("opcao")) {
      estado.tipo = b.dataset.tipo; marcar("#tela-imovel", "data-tipo", estado.tipo);
    }
  });
  // campos de dinheiro: mostram "R$ 1.234" enquanto digita
  $$(".dinheiro").forEach((inp) => inp.addEventListener("input", () => {
    const v = lerDinheiro(inp.value);
    inp.value = v ? fmtR(v) : "";
  }));
  const ler = (e) => {
    // so os campos das telas do formulario (o simulador tem os proprios campos)
    if (e && !e.target.closest("#tela-renda, #tela-imovel")) return;
    estado.renda1 = lerDinheiro($("#renda1").value);
    estado.renda2 = estado.rendaTipo === "somada" ? lerDinheiro($("#renda2").value) : 0;
    estado.fgts = lerDinheiro($("#fgts").value);
    estado.entrada = lerDinheiro($("#entrada").value);
    estado.cotista = $("#cotista").checked;
    estado.jaTemImovel = $("#ja-tem-imovel").checked;
    estado.area = Number($("#area").value) || null;
    estado.precoMax = lerDinheiro($("#preco-max").value) || null;
    estado.trabalho = [$("#trabalho1").value, $("#rotulo-trabalho2").hidden ? "" : $("#trabalho2").value];
  };
  $("#app").addEventListener("input", ler);
  $("#app").addEventListener("change", ler);
  $("#restaurar-pesos").addEventListener("click", () => { estado.pesos = { ...D.bairros.pesos_perfil[estado.perfil] }; desenharPesos(); });
  $("#esconder-caros").addEventListener("change", (e) => { estado.esconderCaros = e.target.checked; desenharResultado(); });
  $("#copiar-link").addEventListener("click", copiarLink);
  $("#barra-comparar-ir").addEventListener("click", () => ir("comparar/" + estado.comparar.join(",")));
  $("#barra-comparar-limpar").addEventListener("click", () => {
    estado.comparar = []; $("#barra-comparar-msg").textContent = "";
    if (location.hash.startsWith("#resultado")) desenharResultado();
    if (location.hash.startsWith("#bairro/")) desenharBairro(estado.bairroAtual);
    atualizarBarraComparar();
  });
  $("#mapa-modo").innerHTML = '<option value="final">Nota final</option>' +
    D.bairros.criterios.map((c) => `<option value="${c}">${ROTULOS[c]}</option>`).join("");
  $("#mapa-modo").addEventListener("change", desenharMapaResultado);
  $("#regioes-mapa").innerHTML = REGIOES_MAPA.map((r) => `<button type="button" class="regiao" data-regiao="${r.id}">${r.rotulo}</button>`).join("");
  $$("#regioes-mapa [data-regiao]").forEach((bt) => bt.addEventListener("click", () => {
    estado.mapaRegiao = bt.dataset.regiao; estado.mapaSel = null; desenharMapaResultado();
  }));
  $$(".nesta-pagina [data-rolar]").forEach((bt) => bt.addEventListener("click", () => {
    const alvo = document.getElementById(bt.dataset.rolar);
    const topo = alvo.getBoundingClientRect().top + window.scrollY - 120;   // desconta cabecalho + indice fixos
    window.scrollTo({ top: topo, behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
  }));
  window.addEventListener("scroll", () => {
    if ($("#tela-resultado").hidden) return;
    let atual = null;
    $$(".nesta-pagina [data-rolar]").forEach((bt) => {
      if (document.getElementById(bt.dataset.rolar).getBoundingClientRect().top < 150) atual = bt;
    });
    $$(".nesta-pagina [data-rolar]").forEach((bt) => bt.classList.toggle("ativo", bt === atual));
  }, { passive: true });
  $("#filtro-bairro").addEventListener("input", (e) => { estado.filtro = e.target.value; estado.limite = 20; desenharResultado(); });
  $("#ver-mais").addEventListener("click", () => { estado.limite += 20; desenharResultado(); });
  $("#ordenar").addEventListener("change", (e) => { estado.ordem = e.target.value; desenharResultado(); });
  $("#mapa-cidade").addEventListener("click", () => { estado.mapaCidade = !estado.mapaCidade; desenharMapaResultado(); });
  $("#voltar-do-simulador").addEventListener("click", () => ir(estado.telaAnterior || "resultado"));
  $("#voltar-do-sobre").addEventListener("click", () => ir(estado.telaAnterior || "inicio"));
  marcar("#tela-renda", "data-renda-tipo", "unica");
  marcar("#tela-imovel", "data-tipo", "");
}

// Nivel em texto (so para leitores de tela). Na tela nao aparece numero: a escolha e visual,
// numa linha de "pouco" a "muito importante", para o perfil nao parecer um julgamento.
const NIVEIS = ["pouco importante", "algo importante", "importante", "bem importante", "muito importante"];

// Textos da tela de renda: "voce" na renda unica, "compradores" na somada
function ajustarTextosRenda() {
  const dois = estado.rendaTipo === "somada";
  $("#rotulo-renda2").hidden = !dois;
  if (!dois) { $("#renda2").value = ""; estado.renda2 = 0; }
  $("#txt-renda1").textContent = dois ? "Renda bruta mensal (comprador 1)" : "Sua renda bruta mensal";
  $("#txt-fgts").textContent = dois ? "Saldo de FGTS para usar (somando os dois)" : "Saldo de FGTS para usar";
  $("#txt-cotista").textContent = dois ? "Algum dos dois tem 3 anos ou mais de trabalho com FGTS"
    : "Você tem 3 anos ou mais de trabalho com FGTS";
  $("#txt-imovel").textContent = dois ? "Algum dos dois já tem imóvel no Rio ou financiamento ativo no SFH"
    : "Você já tem imóvel no Rio ou financiamento ativo no SFH";
}

function desenharPesos() {
  $("#lista-pesos").innerHTML = D.bairros.criterios.map((c) => `
    <div class="peso">
      <label for="peso-${c}" class="peso-nome">${ROTULOS[c]}</label>
      <p class="pequeno">${EXPLICA[c]}</p>
      <input type="range" id="peso-${c}" min="1" max="5" step="1" value="${estado.pesos[c]}"
        aria-valuetext="${NIVEIS[estado.pesos[c] - 1]}">
      <div class="escala" aria-hidden="true"><span>Pouco importante</span><span>Muito importante</span></div>
    </div>`).join("");
  D.bairros.criterios.forEach((c) => $("#peso-" + c).addEventListener("input", (e) => {
    estado.pesos[c] = Number(e.target.value);
    e.target.setAttribute("aria-valuetext", NIVEIS[estado.pesos[c] - 1]);
  }));
}

/* ---------------- link de compartilhamento (so perfil e pesos, nunca renda) ---------------- */
function copiarLink() {
  const p = new URLSearchParams({ p: estado.perfil, w: D.bairros.criterios.map((c) => estado.pesos[c]).join(""), e: estado.escola });
  const url = location.origin + location.pathname + "?" + p.toString() + "#resultado";
  const ok = () => ($("#msg-link").textContent = "Link copiado. Ele leva só o perfil e as prioridades, nunca renda ou valores.");
  if (navigator.clipboard) navigator.clipboard.writeText(url).then(ok, () => ($("#msg-link").textContent = url));
  else $("#msg-link").textContent = url;
}

function lerLinkCompartilhado() {
  const q = new URLSearchParams(location.search);
  const p = q.get("p"), w = q.get("w");
  if (!p || !D.bairros.pesos_perfil[p]) return;
  escolherPerfil(p);
  if (w && /^[1-5]{6}$/.test(w)) D.bairros.criterios.forEach((c, i) => (estado.pesos[c] = Number(w[i])));
  if (["publica", "particular", "tanto_faz"].includes(q.get("e"))) estado.escola = q.get("e");
  marcar("#opcoes-escola", "data-escola", estado.escola);
}

/* ---------------- mapa (SVG gerado pelo ETL, sem servidores externos) ---------------- */
// Escala de calor "YlGnBu" (amarelo -> verde -> azul): varias cores, legivel para daltonicos
// e sem vermelho (nao soa como alarme). Nota 0 = amarelo claro, nota 10 = azul escuro.
const ESCALA_CALOR = ["#ffffd9", "#edf8b1", "#c7e9b4", "#7fcdbb", "#41b6c4", "#1d91c0", "#225ea8", "#253494", "#081d58"];
function corCalor(nota) {
  if (nota == null) return null;
  const t = Math.max(0, Math.min(10, nota)) / 10 * (ESCALA_CALOR.length - 1);
  const i = Math.min(Math.floor(t), ESCALA_CALOR.length - 2), f = t - i;
  const hex = (h) => [1, 3, 5].map((k) => parseInt(h.slice(k, k + 2), 16));
  const a = hex(ESCALA_CALOR[i]), b = hex(ESCALA_CALOR[i + 1]);
  return "rgb(" + a.map((x, k) => Math.round(x + (b[k] - x) * f)).join(",") + ")";
}
// rotulo legivel: decide pelo brilho da cor de fundo (texto escuro sobre cor clara)
function corClara(rgb) {
  const [r, g, b] = rgb.match(/\d+/g).map(Number);
  return 0.299 * r + 0.587 * g + 0.114 * b > 150;
}
// opts.modo: "final" ou um criterio; opts.destaque: codigo de um bairro para realcar (mapa do detalhe)
function svgMapa(opts) {
  const M = D.mapa;
  if (!M) return "";
  const exibidos = new Map(D.bairros.bairros.filter((b) => b.tem_nota).map((b) => [b.codbairro, b]));
  const vbArr = opts.vb || (opts.cidade ? M.viewbox_cidade : M.viewbox_inicial);
  const vb = vbArr.join(" ");
  const fonte = Math.max(14, Math.round(vbArr[2] / (opts.vb ? 32 : 50)));   // letra proporcional a area mostrada
  const poucos = exibidos.size <= 30;                            // com a cidade inteira, sem nomes (sobrepoem)
  // escala relativa: do menor ao maior valor entre os bairros mostrados (como num mapa de calor)
  const valor = (b) => { const n = notasDoBairro(b); return opts.modo === "final" ? n.final : n[opts.modo]; };
  const vals = opts.destaque ? [] : [...exibidos.values()].map(valor).filter((v) => v != null);
  const vmin = Math.min(...vals), vmax = Math.max(...vals);
  const pos = (v) => (vmax > vmin ? (v - vmin) / (vmax - vmin) * 10 : 5);
  svgMapa.faixa = vals.length ? [vmin, vmax] : null;
  svgMapa.valores = opts.destaque ? [] : [...exibidos.values()].map((b) => ({ nome: b.nome, v: valor(b) })).filter((x) => x.v != null);
  svgMapa.cor = (v) => corCalor(pos(v));
  // bairros que ganham destaque flutuante (maior e menor valor): o nome ja vai na caixa
  // com zoom numa regiao, os destaques (maior e menor nota) sao os da propria regiao
  const comValor = opts.destaque ? [] : [...exibidos.values()].map((b) => ({ b, v: valor(b) }))
    .filter((x) => x.v != null && (!opts.rotulosDe || opts.rotulosDe.includes(x.b.codbairro)));
  const extremos = comValor.length > 1 ? [comValor.reduce((a, x) => (x.v > a.v ? x : a)), comValor.reduce((a, x) => (x.v < a.v ? x : a))] : [];
  const codsExtremos = extremos.map((x) => x.b.codbairro);
  let formas = "", rotulos = "";
  for (const [cod, g] of Object.entries(M.bairros)) {
    const b = exibidos.get(cod);
    if (!b) { formas += `<path class="m-fora" d="${g.d}"><title>${esc(g.nome)} (fora desta versão)</title></path>`; continue; }
    let classe = "m-bairro", estilo = "", titulo;
    if (opts.destaque) {
      classe += [].concat(opts.destaque).includes(cod) ? " m-atual" : " m-outro";
      titulo = b.nome;
    } else {
      const v = valor(b), cor = corCalor(v == null ? null : pos(v));
      estilo = cor ? `fill:${cor}` : "";
      if (!cor) classe += " m-sem";
      g.claro = cor ? !corClara(cor) : false;
      if (opts.selecionado === cod) classe += " m-sel";
      titulo = `${b.nome}: ${v == null ? "sem nota" : fmtN(v)}`;
    }
    formas += `<path class="${classe}" d="${g.d}" style="${estilo}" data-bairro="${cod}" tabindex="0" role="link"
      aria-label="${esc(titulo)}"><title>${esc(titulo)}</title></path>`;
    if (codsExtremos.includes(cod)) continue;
    const nomeCurto = b.nome.replace(" (Jacarepaguá)", "");
    const cx = caixaBairro(cod);
    const cabe = nomeCurto.length * fonte * 0.56 <= (cx[2] - cx[0]) * 0.95 && fonte * 1.3 <= (cx[3] - cx[1]);
    const naRegiao = opts.rotulosDe && opts.rotulosDe.includes(cod) && cabe;
    if (!poucos && !naRegiao && !(opts.destaque && [].concat(opts.destaque).includes(cod))) continue;
    rotulos += `<text x="${g.rotulo[0]}" y="${g.rotulo[1]}" font-size="${fonte}"${g.claro && !opts.destaque ? ' class="claro"' : ""}>${esc(b.nome.replace(" (Jacarepaguá)", ""))}</text>`;
  }
  // destaques flutuantes: bairro com maior e com menor valor (so no mapa do resultado)
  let chamadas = "";
  if (extremos.length) {
    const [maior, menor] = extremos;
    const [vx, vy, vw] = vbArr;
    const f = fonte * 1.05, alt = f * 2.9;
    chamadas = [[maior, "Maior nota"], [menor, "Menor nota"]].map(([x, rot]) => {
      const g = M.bairros[x.b.codbairro], nome = x.b.nome.replace(" (Jacarepaguá)", "");
      const larg = Math.max(nome.length, rot.length + 2) * f * 0.62 + f * 3.6;
      const dir = g.rotulo[0] < vx + vw / 2;                       // caixa para o lado de dentro do mapa
      const [, vy0, , vh] = vbArr;
      // caixa sempre dentro da area visivel (nao corta no topo nem nas laterais)
      const bx = Math.min(Math.max(dir ? g.rotulo[0] + f * 2.2 : g.rotulo[0] - f * 2.2 - larg, vx + f * 0.3), vx + vw - larg - f * 0.3);
      let by = g.rotulo[1] - alt - f * 0.8;
      if (by < vy0 + f * 0.3) by = g.rotulo[1] + f * 0.8;
      by = Math.min(by, vy0 + vh - alt - f * 0.3);
      const cor = corCalor(pos(x.v));
      return `<g class="m-chamada"><line x1="${g.rotulo[0]}" y1="${g.rotulo[1]}" x2="${dir ? bx : bx + larg}" y2="${by + alt / 2}"/>
        <circle cx="${g.rotulo[0]}" cy="${g.rotulo[1]}" r="${f * 0.32}"/>
        <rect x="${bx}" y="${by}" width="${larg}" height="${alt}" rx="${f * 0.5}"/>
        <text x="${bx + f * 0.6}" y="${by + f * 1.05}" class="m-chamada-rot" font-size="${f * 0.62}">${rot.toUpperCase()}</text>
        <text x="${bx + f * 0.6}" y="${by + f * 2.15}" class="m-chamada-nome" font-size="${f}">${esc(nome)}</text>
        <rect x="${bx + larg - f * 2.9}" y="${by + f * 0.55}" width="${f * 2.4}" height="${f * 1.8}" rx="${f * 0.35}" style="fill:${cor}"/>
        <text x="${bx + larg - f * 1.7}" y="${by + f * 1.82}" class="m-chamada-nota${corClara(cor) ? "" : " claro"}" font-size="${f * 0.85}">${fmtN(x.v)}</text></g>`;
    }).join("");
  }
  const defs = `<defs><pattern id="hachura" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
    <rect width="8" height="8" fill="#ece5d6"/><line x1="0" y1="0" x2="0" y2="8" stroke="#b9ae97" stroke-width="3"/></pattern></defs>`;
  return `<svg class="mapa-svg" viewBox="${vb}" role="group" aria-label="Mapa dos bairros">${defs}${formas}<g class="m-rotulos" aria-hidden="true">${rotulos}</g><g aria-hidden="true">${chamadas}</g></svg>`;
}

// aoEscolher: o que fazer ao tocar num bairro (padrao: abrir o detalhe)
function ligarMapa(el, aoEscolher = (cod) => ir("bairro/" + cod)) {
  el.querySelectorAll("[data-bairro]").forEach((p) => {
    p.addEventListener("click", () => aoEscolher(p.dataset.bairro));
    p.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); aoEscolher(p.dataset.bairro); } });
  });
}

// Regioes para zoom no mapa (agrupamento das Regioes de Planejamento do IPP)
const REGIOES_MAPA = [
  { id: "cidade", rotulo: "Cidade toda" },
  { id: "centro", rotulo: "Centro", rps: ["Centro"] },
  { id: "sul", rotulo: "Zona Sul", rps: ["Zona Sul"] },
  { id: "norte", rotulo: "Zona Norte", rps: ["Tijuca", "Méier", "Madureira", "Inhaúma", "Penha", "Pavuna", "Ramos", "Ilha do Governador"] },
  { id: "jpa", rotulo: "Barra e Jacarepaguá", rps: ["Jacarepaguá", "Barra da Tijuca"] },
  { id: "oeste", rotulo: "Zona Oeste", rps: ["Bangu", "Campo Grande", "Santa Cruz", "Guaratiba"] },
];
const _caixas = {};
// retangulo do pedaco principal do bairro (ignora ilhas pequenas, ex.: Cagarras), em unidades do SVG
function caixaBairro(cod) {
  if (!_caixas[cod]) {
    let melhor = null, area = -1;
    for (const parte of D.mapa.bairros[cod].d.split("M").filter(Boolean)) {
      const nums = parte.match(/-?\d+(\.\d+)?/g).map(Number);
      const xs = nums.filter((_, i) => i % 2 === 0), ys = nums.filter((_, i) => i % 2 === 1);
      const cx = [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)];
      const a = (cx[2] - cx[0]) * (cx[3] - cx[1]);
      if (a > area) { area = a; melhor = cx; }
    }
    _caixas[cod] = melhor;
  }
  return _caixas[cod];
}
function regiaoDoMapa() {
  const r = REGIOES_MAPA.find((x) => x.id === estado.mapaRegiao) || REGIOES_MAPA[0];
  if (!r.rps) return { vb: null, cods: null };
  const cods = D.bairros.bairros.filter((b) => r.rps.includes(b.regiao) && D.mapa.bairros[b.codbairro]).map((b) => b.codbairro);
  const cx = cods.map(caixaBairro);
  const x0 = Math.min(...cx.map((c) => c[0])), y0 = Math.min(...cx.map((c) => c[1]));
  const x1 = Math.max(...cx.map((c) => c[2])), y1 = Math.max(...cx.map((c) => c[3]));
  const m = Math.max(x1 - x0, y1 - y0) * 0.04;
  return { vb: [x0 - m, y0 - m, x1 - x0 + 2 * m, y1 - y0 + 2 * m].map(Math.round), cods };
}

function cartaoDoMapa(cod) {
  const b = D.bairros.bairros.find((x) => x.codbairro === cod);
  if (!b || !b.tem_nota) return "";
  const n = notasDoBairro(b), modo = $("#mapa-modo").value || "final";
  const v = modo === "final" ? n.final : n[modo];
  const marcado = estado.comparar.includes(cod);
  return `<div class="mapa-info-conteudo">
      ${anel(v, 48)}
      <div class="mapa-info-texto"><strong>${esc(b.nome)}</strong>
        <span class="pequeno">${esc(localTexto(b))} · ${modo === "final" ? "nota final" : esc(ROTULOS[modo])}${v == null ? " (sem nota)" : ""}</span></div>
      <div class="mapa-info-botoes"><button class="btn-principal" type="button" data-ir="bairro/${cod}">Ver detalhes</button>
        <button class="btn" type="button" id="mapa-info-comparar" aria-pressed="${marcado}">${marcado ? "✓ Comparando" : "+ Comparar"}</button></div>
    </div>`;
}

function desenharMapaResultado() {
  if (!D.mapa) { $("#bloco-mapa").hidden = true; return; }
  const modo = $("#mapa-modo").value || "final";
  const reg = regiaoDoMapa();
  $("#mapa").innerHTML = svgMapa({ modo, cidade: estado.mapaCidade, vb: reg.vb, rotulosDe: reg.cods, selecionado: estado.mapaSel });
  $$("#regioes-mapa [data-regiao]").forEach((bt) => bt.setAttribute("aria-pressed", String(bt.dataset.regiao === (estado.mapaRegiao || "cidade"))));
  $("#mapa-info").hidden = !estado.mapaSel;
  if (estado.mapaSel) {
    $("#mapa-info").innerHTML = cartaoDoMapa(estado.mapaSel);
    $("#mapa-info-comparar")?.addEventListener("click", () => { alternarComparar(estado.mapaSel); desenharResultado(); atualizarBarraComparar("resultado"); });
  }
  // regua 0-10: faixa colorida ocupada pelos bairros, um traco por bairro e a mediana do Rio (5)
  if (svgMapa.faixa) {
    const [a, b] = svgMapa.faixa;
    $("#regua-faixa").textContent = `· os bairros mostrados vão de ${fmtN(a)} a ${fmtN(b)}`;
    $("#regua").innerHTML = `<span class="regua-faixa" style="left:${a * 10}%;width:${(b - a) * 10}%;background:linear-gradient(90deg, ${ESCALA_CALOR.join(", ")})"></span>
      <span class="regua-mediana" style="left:50%"></span>` +
      svgMapa.valores.map((x) => `<span class="regua-traco" style="left:${x.v * 10}%;background:${svgMapa.cor(x.v)}" title="${esc(x.nome)}: ${fmtN(x.v)}"></span>`).join("");
  }
  $("#mapa-cidade").textContent = estado.mapaCidade ? "Aproximar dos bairros" : "Ver cidade inteira";
  // com a cidade inteira exibida, o enquadramento inicial ja e a cidade: o botao nao faz sentido
  $("#mapa-cidade").hidden = D.mapa.viewbox_inicial.join() === D.mapa.viewbox_cidade.join();
  // tocar num bairro do mapa do resultado: mostra o cartao embaixo (nao sai da tela)
  ligarMapa($("#mapa"), (cod) => { estado.mapaSel = cod; desenharMapaResultado(); $("#mapa-info").scrollIntoView({ block: "nearest", behavior: "smooth" }); });
}

/* ---------------- resultado ---------------- */
// Grade 3x2 com as 6 notas (cartao compacto da lista)
function miniNotas(n) {
  return `<div class="mini-notas">${D.bairros.criterios.map((c) => {
    const v = n[c];
    return `<div class="mini-nota" title="${esc(ROTULOS[c])}">
      <span class="mini-topo">${icone(c)}<strong>${v == null ? "–" : fmtN(v)}</strong></span>
      <span class="mini-rotulo">${esc(ROTULOS[c])}</span>
      <span class="barra-fundo" aria-hidden="true"><span class="barra-cheia" style="width:${v == null ? 0 : v * 10}%"></span></span></div>`;
  }).join("")}</div>`;
}

function barras(n) {
  return `<div class="barras">${D.bairros.criterios.map((c) => {
    const v = n[c];
    return `<div class="barra"><span class="barra-rotulo">${icone(c)}${ROTULOS[c]}</span>
      <span class="barra-fundo" aria-hidden="true"><span class="barra-cheia" style="width:${v == null ? 0 : v * 10}%"></span></span>
      <span class="barra-valor">${v == null ? "-" : fmtN(v)}</span></div>`;
  }).join("")}</div>`;
}

function desenharResultado() {
  const orc = orcamento();
  const todos = D.bairros.bairros.filter((b) => b.tem_nota)
    .map((b) => ({ b, n: notasDoBairro(b), c: custoNoBairro(b, orc) }));
  const lista = todos.filter((x) => x.n.final != null).sort((x, y) => y.n.final - x.n.final);
  lista.forEach((x, i) => (x.pos = i + 1));          // posicao sempre pela nota
  const semFinal = todos.filter((x) => x.n.final == null).sort((x, y) => x.b.nome.localeCompare(y.b.nome, "pt-BR"));
  const ordens = {
    nota: () => 0,
    parcela: (x, y) => (x.c?.parcela ?? 1e12) - (y.c?.parcela ?? 1e12),
    area: (x, y) => (y.c?.areaMax ?? -1) - (x.c?.areaMax ?? -1),
    preco_m2: (x, y) => (x.c?.rs ?? 1e12) - (y.c?.rs ?? 1e12),
  };
  if (estado.ordem !== "nota") lista.sort(ordens[estado.ordem] || ordens.nota);
  // bairros sem nota final vao para o fim (sem posicao), com um titulo explicando
  const busca = norm(estado.filtro);
  const visiveis = [...lista, ...semFinal]
    .filter((x) => !busca || norm(x.b.nome).includes(busca))
    .filter((x) => !(estado.esconderCaros && acimaOrcamento(x.b)));
  const mostrados = visiveis.slice(0, estado.limite);

  $("#sobretitulo-resultado").textContent = "Ranking · " + mesAno(D.bairros.gerado_em);
  $("#explica-nota").textContent = D.bairros.metodo_nota + " A nota final é a média das 6 notas, pesada pelas suas prioridades.";
  $("#painel-orcamento").innerHTML = painelOrcamento(orc);
  $("#esconder-caros").checked = estado.esconderCaros;
  $("#rotulo-esconder").textContent = orc ? "Mostrar só os que cabem no meu bolso" : "Esconder bairros acima do meu preço máximo";
  $$("#ordenar option[data-precisa-renda]").forEach((o) => (o.disabled = !orc));
  if (!orc && ["parcela", "area"].includes(estado.ordem)) estado.ordem = "nota";
  $("#ordenar").value = estado.ordem;
  $("#titulo-resultado").textContent = { nota: "Bairros em ordem de nota", parcela: "Bairros pela menor parcela",
    area: "Bairros pela maior área que cabe", preco_m2: "Bairros pelo menor preço do m²" }[estado.ordem];

  let jaTitulo = false;
  $("#lista-bairros").innerHTML = mostrados.map(({ b, n, c, pos }) => {
    const caro = acimaOrcamento(b);
    let titulo = "";
    if (!pos && !jaTitulo) {
      jaTitulo = true;
      titulo = `<li class="titulo-sem-nota"><strong>Bairros sem nota final</strong>
        <span>Os registros oficiais não representam bem quem mora nestes bairros: em áreas de favela, ocorrências e chamados ao 1746
        são pouco registrados; em outros, a taxa da delegacia reflete sobretudo outros bairros. Algumas notas ficam sem valor
        (veja o motivo no detalhe); os outros critérios, o preço e o simulador continuam valendo.</span></li>`;
    }
    const tag = !c ? "" : caro ? `<span class="etiqueta">${orc ? "Acima do que cabe" : "Acima do seu preço máximo"}</span>`
      : orc ? '<span class="etiqueta etiqueta-ok">Cabe no seu bolso</span>' : "";
    const marcado = estado.comparar.includes(b.codbairro);
    return `${titulo}<li class="item-bairro"><button class="btn-comparar" data-comparar="${b.codbairro}" aria-pressed="${marcado}"
        aria-label="${marcado ? "Tirar da comparação" : "Comparar"}: ${esc(b.nome)}">${marcado ? "✓ Comparando" : "+ Comparar"}</button>
      <button class="cartao-bairro" data-bairro="${b.codbairro}" aria-label="Ver detalhes de ${esc(b.nome)}">
      <div class="cartao-topo">
        <div class="cartao-id"><span class="posicao">${pos ? "#" + pos : "–"}</span>
          <div><span class="cartao-nome">${esc(b.nome)}</span><span class="cartao-regiao">${icone("local")}${esc(localTexto(b))}</span>
            <div class="etiquetas">${tag}${pos ? "" : '<span class="etiqueta etiqueta-neutra">Sem nota final</span>'}</div></div></div>
        <div class="cartao-nota">${anel(n.final, 58)}</div>
      </div>
      ${blocoBolsoCompacto(c)}
      ${miniNotas(n)}
      <span class="ver-mais">Ver detalhes →</span>
    </button></li>`;
  }).join("") || `<li class="vazio-lista">${busca ? "Nenhum bairro com esse nome." : "Nenhum bairro cabe no orçamento com esses números. Desmarque o filtro ou ajuste a renda, a entrada ou a área."}</li>`;
  const resto = visiveis.length - mostrados.length;
  $("#ver-mais").hidden = resto <= 0;
  $("#ver-mais").textContent = `Ver mais ${Math.min(20, resto)} bairros (de ${resto} restantes)`;
  $("#contagem-lista").textContent = `${mostrados.length} de ${visiveis.length} bairros${busca ? " encontrados" : ""}`;
  $$("#lista-bairros [data-bairro]").forEach((el) => el.addEventListener("click", () => ir("bairro/" + el.dataset.bairro)));
  $$("#lista-bairros [data-comparar]").forEach((el) => el.addEventListener("click", () => { alternarComparar(el.dataset.comparar); desenharResultado(); atualizarBarraComparar("resultado"); }));
  desenharMapaResultado();
}

/* ---------------- resumo em texto e radar ---------------- */
const juntar = (xs) => xs.length <= 1 ? xs.join("") : xs.slice(0, -1).join(", ") + " e " + xs[xs.length - 1];

// Resumo montado so com os numeros (posicao na cidade), sem opiniao nem rotulos.
function resumoTexto(b, n) {
  const N = D.bairros.referencia_codigos.length;
  const cs = D.bairros.criterios.filter((c) => n[c] != null);
  const fortes = cs.filter((c) => n[c] >= 6.5).sort((x, y) => n[y] - n[x]).slice(0, 3);
  const atencao = cs.filter((c) => n[c] <= 3.5).sort((x, y) => n[x] - n[y]).slice(0, 3);
  const pct = (v) => fmtN(v * 10, 0) + "%";
  const frases = [];
  if (fortes.length) {
    frases.push(`Na comparação com os ${N} bairros do Rio, se destaca em ${juntar(fortes.map((c) =>
      `${TXT_FORTE[c]} (à frente de ${pct(n[c])})`))}.`);
  } else {
    const m = cs.reduce((a, c) => (n[c] > n[a] ? c : a));
    frases.push(`Na comparação com os ${N} bairros do Rio, não fica entre os mais bem colocados em nenhum critério; o melhor resultado é em ${TXT_FORTE[m]} (à frente de ${pct(n[m])}).`);
  }
  if (atencao.length) {
    frases.push(`Pontos de atenção: ${juntar(atencao.map((c) => `${TXT_ATENCAO[c].toLowerCase()} (atrás de ${pct(10 - n[c])})`))}.`);
  } else {
    frases.push("Não fica entre os 35% de resultado mais baixo da cidade em nenhum critério.");
  }
  if (b.sem_nota_final) frases.push(b.sem_nota_final_motivo);
  if (b.criterios.violencia.aviso_publico_de_fora) frases.push(b.criterios.violencia.aviso_publico_de_fora);
  const med = D.bairros.preco_mediana_rs_m2;
  if (b.preco_itbi && med) {
    const dif = (b.preco_itbi.rs_m2 / med - 1) * 100;
    frases.push(`O m² médio vendido (${fmtR(b.preco_itbi.rs_m2)}) está ${Math.abs(dif) < 5 ? "perto da" : `${fmtN(Math.abs(dif), 0)}% ${dif > 0 ? "acima" : "abaixo"} da`} mediana da cidade (${fmtR(med)}).`);
  }
  const orc = orcamento(), c = custoNoBairro(b, orc);
  if (orc && c) frases.push(c.cabe ? `Com o seu orçamento, cabe aqui um imóvel de até ~${c.areaMax} m².`
    : `Com o seu orçamento, cabe aqui um imóvel de até ~${c.areaMax} m², menos que os ${c.areaInformada ? c.areaUsada + " m² que você pediu" : fmtN(c.areaUsada, 0) + " m² da área média vendida"}.`);
  return frases;
}

// Radar (teia) com os 6 criterios. series: [{nome, notas, cor}]. Anel tracejado em 5 = mediana do Rio.
const CORES_SERIE = ["var(--principal)", "#2563eb", "#9333ea"];
function radar(series, tam = 300) {
  const cs = D.bairros.criterios, cx = 150, cy = 140, R = 92;
  const pt = (i, v) => {
    const a = -Math.PI / 2 + i * 2 * Math.PI / cs.length, r = R * v / 10;
    return [cx + r * Math.cos(a), cy + r * Math.sin(a)];
  };
  const poli = (v) => cs.map((_, i) => pt(i, v).map((x) => x.toFixed(1)).join(",")).join(" ");
  const grade = [2.5, 5, 7.5, 10].map((v) => `<polygon class="rd-grade${v === 5 ? " rd-mediana" : ""}" points="${poli(v)}"/>`).join("");
  const eixos = cs.map((_, i) => { const [x, y] = pt(i, 10); return `<line class="rd-eixo" x1="${cx}" y1="${cy}" x2="${x}" y2="${y}"/>`; }).join("");
  const rotulos = cs.map((c, i) => {
    const [x, y] = pt(i, 12.2), anc = Math.abs(x - cx) < 5 ? "middle" : x > cx ? "start" : "end";
    // rotulos longos ("Menos alagamento") em duas linhas, para caber em celular estreito
    const semDado = series.every((s) => s.notas[c] == null);
    const partes = (ROTULOS[c].length > 10 && ROTULOS[c].includes(" ") ? ROTULOS[c].split(" ") : [ROTULOS[c]]).concat(semDado ? ["(sem dado)"] : []);
    const y0 = y - (partes.length - 1) * 6.5;
    return `<text class="rd-rotulo" x="${x.toFixed(1)}" y="${y0.toFixed(1)}" text-anchor="${anc}">${partes.map((t, k) =>
      `<tspan x="${x.toFixed(1)}" dy="${k ? 13 : 0}">${t}</tspan>`).join("")}</text>`;
  }).join("");
  const formas = series.map((s, k) => {
    const pts = cs.map((c, i) => (s.notas[c] == null ? null : pt(i, s.notas[c]))).filter(Boolean);   // sem dado: fora do desenho
    return `<polygon class="rd-serie" style="fill:${s.cor};stroke:${s.cor}" points="${pts.map((p) => p.map((x) => x.toFixed(1)).join(",")).join(" ")}"/>` +
      pts.map((p) => `<circle cx="${p[0].toFixed(1)}" cy="${p[1].toFixed(1)}" r="3.2" style="fill:${s.cor}"/>`).join("");
  }).join("");
  const desc = series.map((s) => `${s.nome}: ` + cs.map((c) => `${ROTULOS[c]} ${s.notas[c] == null ? "sem dado" : fmtN(s.notas[c])}`).join(", ")).join(". ");
  return `<figure class="radar"><svg viewBox="0 0 300 290" style="max-width:${tam}px" role="img" aria-label="Gráfico de radar. ${esc(desc)}">
      ${grade}${eixos}${formas}${rotulos}<text class="rd-legenda5" x="${cx + 4}" y="${cy - R / 2 - 4}">5</text></svg>
    <figcaption class="pequeno">${series.length > 1 ? series.map((s) => `<span class="rd-item"><span class="rd-cor" style="background:${s.cor}"></span>${esc(s.nome)}</span>`).join("") : ""}
      <span class="rd-item"><span class="rd-traco"></span>mediana do Rio (nota 5)</span></figcaption></figure>`;
}

/* ---------------- compartilhar ---------------- */
// O link compartilhado e o da pagina do bairro (com previa no WhatsApp). Nunca leva renda,
// prioridades ou qualquer dado digitado.
const linkBairro = (b) => `${D.bairros.site_url}bairro/${b.slug}/`;
const textoCompartilhar = (b) => `Veja ${b.nome} no Onde Comprar no Rio (notas com dados oficiais, preço do m² e simulação de financiamento): ${linkBairro(b)}`;

/* ---------------- comparar bairros ---------------- */
const MAX_COMPARAR = 3;
const nomeDe = (cod) => D.bairros.bairros.find((b) => b.codbairro === cod)?.nome || cod;

function alternarComparar(cod) {
  const i = estado.comparar.indexOf(cod);
  if (i >= 0) estado.comparar.splice(i, 1);
  else if (estado.comparar.length >= MAX_COMPARAR) {
    $("#barra-comparar-msg").textContent = `Dá para comparar até ${MAX_COMPARAR} bairros. Tire um para incluir outro.`;
    return;
  } else estado.comparar.push(cod);
  $("#barra-comparar-msg").textContent = "";
}

function atualizarBarraComparar(tela) {
  const n = estado.comparar.length, barra = $("#barra-comparar");
  barra.hidden = !(n > 0 && ["resultado", "bairro"].includes(tela || location.hash.slice(1).split("/")[0]));
  document.body.classList.toggle("com-barra", !barra.hidden);
  if (barra.hidden) return;
  $("#barra-comparar-texto").innerHTML = `<strong>${n} de ${MAX_COMPARAR}</strong> · ${esc(estado.comparar.map(nomeDe).join(", "))}`;
  $("#barra-comparar-ir").disabled = n < 2;
  $("#barra-comparar-ir").textContent = n < 2 ? "Escolha mais 1" : `Comparar ${n} bairros`;
}

function desenharComparacao(arg) {
  const cods = arg.split(",").filter((c) => D.bairros.bairros.some((b) => b.codbairro === c && b.tem_nota)).slice(0, MAX_COMPARAR);
  const alvo = $("#comparacao");
  if (cods.length < 2) {
    alvo.innerHTML = `<p class="destaque">Escolha pelo menos 2 bairros na lista (botão "+ Comparar") para ver lado a lado.</p>
      <button class="btn-principal" data-ir="resultado">Ir para a lista</button>`;
    return;
  }
  estado.comparar = cods.slice();
  const orc = orcamento();
  const cols = cods.map((c) => { const b = D.bairros.bairros.find((x) => x.codbairro === c); return { b, n: notasDoBairro(b), c: custoNoBairro(b, orc) }; });
  // marca o melhor de cada linha (so se houver diferenca)
  const melhor = (vals, maiorMelhor = true) => {
    const ok = vals.filter((v) => v != null);
    if (ok.length < 2 || Math.max(...ok) === Math.min(...ok)) return vals.map(() => false);
    const alvoV = maiorMelhor ? Math.max(...ok) : Math.min(...ok);
    return vals.map((v) => v === alvoV);
  };
  const linhaNota = (rotulo, vals, ic, sub, brutos) => {
    const m = melhor(vals.map((v) => (v == null ? null : Math.round(v * 10) / 10)));
    return `<tr><th scope="row">${ic ? icone(ic) : ""}${rotulo}${sub ? `<span class="sub">${sub}</span>` : ""}</th>${vals.map((v, i) =>
      `<td class="${m[i] ? "melhor" : ""}"><span class="cmp-nota">${v == null ? "-" : fmtN(v)}</span>
        <span class="barra-fundo" aria-hidden="true"><span class="barra-cheia" style="width:${v == null ? 0 : v * 10}%"></span></span>
        ${brutos ? `<span class="cmp-bruto">${esc(brutos[i])}</span>` : ""}</td>`).join("")}</tr>`;
  };
  const linhaValor = (rotulo, vals, fmt, maiorMelhor) => {
    const m = maiorMelhor == null ? vals.map(() => false) : melhor(vals, maiorMelhor);
    return `<tr><th scope="row">${rotulo}</th>${vals.map((v, i) => `<td class="${m[i] ? "melhor" : ""}">${v == null ? "-" : fmt(v)}</td>`).join("")}</tr>`;
  };

  const criterios = D.bairros.criterios.map((cr) => {
    const ind = cols[0].b.criterios[cr].indicadores[0];
    return linhaNota(ROTULOS[cr], cols.map((x) => x.n[cr]), cr);
  }).join("");

  const bolso = cols.every((x) => x.c) ? `
    <tr class="grupo"><th colspan="${cols.length + 1}">${icone("preco")}Preço e o seu bolso</th></tr>
    ${linhaValor("m² médio (ITBI)", cols.map((x) => x.c.rs), fmtR, false)}
    ${orc ? linhaValor("Cabe até", cols.map((x) => x.c.areaMax), (v) => `~${v} m²`, true) : ""}
    ${orc ? linhaValor(`1ª parcela (${cols[0].c.areaInformada ? cols[0].c.areaUsada + " m²" : "área média"})`, cols.map((x) => x.c.parcela), fmtR, false) : ""}
    ${orc ? linhaValor("Cabe no bolso?", cols.map((x) => (x.c.cabe ? "Sim" : "Não")), (v) => v, null) : ""}` : "";

  // resumo em texto: em que criterios cada bairro fica na frente
  const lideres = cols.map((x) => D.bairros.criterios.filter((cr) => {
    const vals = cols.map((y) => (y.n[cr] == null ? null : Math.round(y.n[cr] * 10) / 10));
    return melhor(vals)[cols.indexOf(x)];
  }));
  const resumo = cols.map((x, i) => lideres[i].length
    ? `<li><strong>${esc(x.b.nome)}</strong> fica na frente em ${lideres[i].map((c) => TXT_FORTE[c]).join(", ").replace(/, ([^,]*)$/, " e $1")}.</li>`
    : `<li><strong>${esc(x.b.nome)}</strong> não fica na frente em nenhum critério desta comparação.</li>`).join("");

  // avisos que mudam a leitura das notas (sem nota final; muita gente de fora na area da delegacia)
  const avisosCmp = cols.flatMap((x) => [
    x.b.sem_nota_final ? `<p class="aviso"><strong>${esc(x.b.nome)}:</strong> sem nota final. ${esc(x.b.sem_nota_final_motivo)}</p>` : "",
    x.b.criterios.violencia.aviso_publico_de_fora ? `<p class="aviso"><strong>${esc(x.b.nome)}, Segurança:</strong> ${esc(x.b.criterios.violencia.aviso_publico_de_fora)}</p>` : "",
  ]).join("");

  alvo.innerHTML = `
    <div class="secao-cab"><p class="sobretitulo">Comparação · ${cols.length} bairros</p><h2>Comparar bairros</h2></div>
    <p class="pequeno">Notas de 0 a 10 (posição entre os bairros do Rio). Em destaque, o melhor de cada linha.</p>
    <div class="bloco cmp-bloco"><div class="rolagem"><table class="cmp">
      <thead><tr><th></th>${cols.map((x) => `<th scope="col"><div class="cmp-cab">${anel(x.n.final, 56)}
        <strong>${esc(x.b.nome)}</strong><span class="cartao-regiao">${esc(localTexto(x.b))}</span></div></th>`).join("")}</tr></thead>
      <tbody>
        ${linhaNota("<strong>Nota final</strong>", cols.map((x) => x.n.final))}
        ${criterios}
        ${bolso}
      </tbody></table></div>
      <div class="cmp-acoes" style="grid-template-columns: var(--cmp-rotulo) repeat(${cols.length}, 1fr)"><span></span>${cols.map((x) => `<div><button class="btn" data-ir="bairro/${x.b.codbairro}">Detalhes</button>
        <button class="btn" data-ir="financiamento/${x.b.codbairro}">Simular</button></div>`).join("")}</div>
    </div>
    ${avisosCmp ? `<div class="bloco cmp-avisos"><h3>Avisos sobre os dados</h3>${avisosCmp}</div>` : ""}
    <div class="bloco"><h3>Formato de cada bairro</h3>
      <p class="pequeno">Quanto mais longe do centro, melhor a nota naquele critério.</p>
      ${radar(cols.map((x, i) => ({ nome: x.b.nome, notas: x.n, cor: CORES_SERIE[i] })), 340)}</div>
    <div class="bloco"><h3>Os números por trás das notas</h3>
      <p class="pequeno">Cada nota junta vários indicadores. Abra um critério para ver todos, lado a lado (em destaque, o melhor de cada um).</p>
      ${D.bairros.criterios.map((cr) => {
        const inds = cols[0].b.criterios[cr].indicadores;
        const linhas = inds.map((ind, k) => {
          const vals = cols.map((x) => x.b.criterios[cr].indicadores[k].valor);
          const m = melhor(vals, !ind.maior_e_pior);
          // unidade uma vez so, junto do nome; nas celulas, so o numero (cabe no celular)
          const un = ind.unidade === "metros" ? "km" : ind.unidade;
          const num = (v) => v == null ? "-" : ind.unidade === "metros" ? fmtN(v / 1000, 1) : fmtN(v, 1);
          return `<tr><td>${esc(ind.rotulo)} <span class="pequeno">(${esc(un)}${ind.peso != null ? `; peso ${fmtN(ind.peso * 100, 0)}%` : ""})</span></td>${cols.map((x, i) =>
            `<td class="${m[i] ? "melhor" : ""}">${num(x.b.criterios[cr].indicadores[k].valor)}</td>`).join("")}</tr>`;
        }).join("");
        return `<details class="cmp-det"><summary>${icone(cr)}${ROTULOS[cr]}</summary><div class="rolagem"><table class="tabela cmp-ind">
          <thead><tr><th>Indicador</th>${cols.map((x) => `<th>${esc(x.b.nome)}</th>`).join("")}</tr></thead><tbody>${linhas}</tbody></table></div></details>`;
      }).join("")}
    </div>
    <div class="bloco"><h3>Em resumo</h3><ul class="cmp-resumo">${resumo}</ul>
      <p class="pequeno">A nota final usa as suas prioridades${estado.perfil ? "" : " (aqui, todos os critérios com o mesmo peso)"}.</p></div>
    ${D.mapa ? `<div class="bloco"><h3>No mapa</h3><div id="mapa-comparar">${svgMapa({ destaque: cods })}</div></div>` : ""}
    <div class="navegacao"><button class="btn" data-ir="resultado">Voltar à lista</button>
      <button class="btn" id="copiar-comparacao">Copiar link desta comparação</button></div>
    <button class="btn nao-imprimir" type="button" data-imprimir>Imprimir ou salvar em PDF</button>
    <p id="msg-comparacao" class="pequeno" role="status"></p>`;
  if ($("#mapa-comparar")) ligarMapa($("#mapa-comparar"));
  $("#copiar-comparacao").addEventListener("click", () => {
    const url = location.origin + location.pathname + "#comparar/" + cods.join(",");
    const ok = () => ($("#msg-comparacao").textContent = "Link copiado. Ele leva só os bairros escolhidos, nunca renda ou valores.");
    if (navigator.clipboard) navigator.clipboard.writeText(url).then(ok, () => ($("#msg-comparacao").textContent = url));
    else $("#msg-comparacao").textContent = url;
  });
}

/* ---------------- detalhe do bairro ---------------- */
function textoFonte(c) {
  const f = D.bairros.fontes[c];
  const periodo = f.periodo || (f.fontes || []).map((x) => x.periodo).filter(Boolean).join("; ");
  const nome = f.fonte || (f.fontes || []).map((x) => x.nome).join("; ");
  const avisos = [].concat(f.aviso || [], f.avisos || []);
  return `<div class="fonte">Fonte: ${esc(nome)}${periodo ? ` · Período: ${esc(periodo)}` : ""} · Processado em ${fmtData(f.processado_em)}
    ${avisos.length ? `<ul>${avisos.map((a) => `<li>${esc(a)}</li>`).join("")}</ul>` : ""}</div>`;
}

function fmtValor(i) {
  if (i.valor == null) return "-";
  if (i.unidade === "metros") return fmtN(i.valor / 1000, 1) + " km";
  if (i.unidade === "%") return fmtN(i.valor, 1) + "%";
  return fmtN(i.valor, 1) + (i.unidade.startsWith("por") ? " " + i.unidade : "");
}
function fmtMediana(i) {
  if (i.mediana_cidade == null) return "-";
  return fmtValor({ ...i, valor: i.mediana_cidade });
}

// delegacia onde mora a maior parte do bairro (a lista do JSON vem em ordem de numero da CISP)
function cispPrincipal(b) {
  const l = b.criterios.violencia.cisps || [];
  return l.length ? l.reduce((a, x) => (x.pct_pop > a.pct_pop ? x : a)).cisp : null;
}

function blocoCriterio(b, c, n) {
  const cr = b.criterios[c];
  let extra = "";
  if (c === "violencia" && cr.cisps?.length) {
    const lista = cr.cisps.map((x) => `${x.cisp}ª DP (${fmtN(x.pct_pop * 100, 0)}% dos moradores)`).join(", ");
    const principal = cispPrincipal(b);
    const vizinhos = D.bairros.bairros.filter((o) => o.codbairro !== b.codbairro && cispPrincipal(o) === principal).map((o) => o.nome);
    extra = `<p class="pequeno">Área de delegacia: ${lista}.${vizinhos.length ? ` Mesma delegacia principal de: ${esc(vizinhos.join(", "))}.` : ""}</p>`;
  }
  if (c === "escolas") {
    const k = cr.contagem_no_bairro;
    extra = `<p class="pequeno">Dentro do bairro: ${k.n_publicas_no_bairro} públicas e ${k.n_privadas_no_bairro} particulares (${k.n_com_ideb_no_bairro} com Ideb 2025).
      Tipo de escola considerado: ${esc({ tanto_faz: "tanto faz", publica: "pública", particular: "particular" }[estado.escola])}.</p>`;
  }
  if (c === "transporte" && cr.estacao_mais_comum) extra = `<p class="pequeno">Estação mais próxima para a maioria dos moradores: ${esc(cr.estacao_mais_comum)}.</p>`;
  if (c === "emprego") {
    const d = cr.dist_km, polos = D.bairros.emprego.polos;
    extra = `<p class="pequeno">Distância média dos moradores, em linha reta: ${Object.keys(d).map((k) => `${esc(polos[k].rotulo)} ${fmtN(d[k])} km`).join(" · ")}.
      ${estado.trabalho.some(Boolean) ? "A nota usa o local de trabalho que você informou." : ""}</p>`;
  }
  if (c === "barulho") extra = `<p class="pequeno">Mapa oficial de ruído em decibéis: ainda não publicado pela Prefeitura.</p>`;
  const linhas = cr.indicadores.map((i) => `<tr><td>${esc(i.rotulo)}${i.peso != null ? ` <span class="pequeno">(peso ${fmtN(i.peso * 100, 0)}%)</span>` : ""}</td>
    <td class="num">${fmtValor(i)}<br><span class="pequeno">cidade: ${fmtMediana(i)}</span></td>
    <td class="num">${i.nota == null ? "-" : fmtN(i.nota)}</td></tr>`).join("");
  const pct = cr.dados_insuficientes ? "Sem nota: dados insuficientes." : n[c] == null ? "" : `Melhor que ${fmtN(n[c] * 10, 0)}% dos bairros do Rio neste critério.`;
  if (cr.dados_insuficientes) extra = `<p class="aviso">${esc(cr.dados_insuficientes)}</p>` + extra;
  if (cr.aviso_publico_de_fora) extra = `<p class="aviso">${esc(cr.aviso_publico_de_fora)}</p>` + extra;
  return `<div class="criterio"><div class="criterio-topo"><span class="criterio-icone">${icone(c)}</span>
      <div><h3>${ROTULOS[c]}</h3><p class="pequeno">${pct}</p></div>${anel(n[c], 52)}</div>
    <div class="rolagem"><table class="indicadores"><tbody><tr class="pequeno"><td>Indicador</td><td class="num">Valor<br>(mediana da cidade)</td><td class="num">Nota</td></tr>${linhas}</tbody></table></div>
    ${extra}${textoFonte(c)}</div>`;
}

function linkPortal(modelo, portal, b) {
  const zona = D.portais.zona_por_regiao[b.regiao] || "";
  const tipoChave = estado.tipo || "";
  return modelo.replace("{bairro}", slug(b.nome)).replace("{zona}", zona)
    .replace(/\{tipo_[a-z]+\}/, portal.tipos[tipoChave] ?? "");
}

function blocoImoveisCaixa(b) {
  const lista = (D.caixa.imoveis || []).filter((i) => i.codbairro === b.codbairro)
    .filter((i) => !estado.tipo || (i.tipo || "").toLowerCase().includes(estado.tipo))
    .filter((i) => !estado.area || i.area_m2 == null || i.area_m2 >= estado.area)
    .sort((x, y) => (x.preco ?? 0) - (y.preco ?? 0));
  if (!D.caixa.data_lista) return `<p class="pequeno">Lista de imóveis da Caixa ainda não carregada nesta versão.</p>`;
  const cab = `<p class="pequeno">Lista oficial da Caixa de ${fmtData(D.caixa.data_lista)}. Imóveis retomados pela Caixa:
    confira ocupação, estado e regras da venda no edital antes de qualquer decisão.</p>`;
  if (!lista.length) return cab + "<p>Nenhum imóvel da Caixa neste bairro com os filtros escolhidos.</p>";
  return cab + lista.slice(0, 20).map((i) => `<div class="imovel">
      <strong>${fmtR(i.preco)}</strong> · ${esc(i.tipo || "Imóvel")}${i.area_m2 ? ` · ${fmtN(i.area_m2, 0)} m²` : ""}${i.quartos ? ` · ${i.quartos} quarto(s)` : ""}
      ${estado.precoMax && i.preco > estado.precoMax ? ' <span class="etiqueta">Acima do seu orçamento</span>' : ""}
      <br>${esc(i.endereco || "")}<br><span class="pequeno">${esc(i.modalidade || "")}${i.desconto_pct ? ` · desconto de ${fmtN(i.desconto_pct, 0)}% sobre a avaliação` : ""}</span>
      ${i.link && /^https:\/\/[a-z0-9.-]*caixa\.gov\.br\//i.test(i.link) ? `<br><a href="${esc(i.link)}" target="_blank" rel="noopener noreferrer">Ver na Caixa</a>` : ""}
    </div>`).join("") + (lista.length > 20 ? `<p class="pequeno">Mostrando 20 de ${lista.length}.</p>` : "");
}

function desenharBairro(cod) {
  const b = D.bairros.bairros.find((x) => x.codbairro === cod);
  if (!b) return ir("resultado");
  const n = notasDoBairro(b);
  const p = b.preco_itbi, fp = D.bairros.fontes.preco;
  const orc = orcamento(), c = custoNoBairro(b, orc);
  const preco = p ? `<div class="bloco"><h3>Preço e o seu bolso</h3>
      <p><strong>${fmtR(p.rs_m2)} por m²</strong> em média, em ${p.transacoes.toLocaleString("pt-BR")} vendas declaradas
      (${esc(fp.periodo)}). Área média: ${fmtN(p.area_media_m2, 0)} m²; valor médio: ${fmtR(p.valor_medio)}.</p>
      ${blocoBolso(b, c)}
      ${orc ? (c.cabe ? '<span class="etiqueta etiqueta-ok">Cabe no seu bolso</span>'
        : `<span class="etiqueta">Acima do que cabe</span><p class="pequeno">Com o seu orçamento, aqui cabe um imóvel de até ~${c.areaMax} m².</p>`)
        : `<p class="pequeno"><a href="#renda">Informe a renda</a> para ver quanto cabe no seu bolso neste bairro.</p>`}
      <div class="fonte">Fonte: ${esc(fp.fonte)}. ${fp.avisos.map(esc).join(" ")}</div></div>` : "";
  const portais = (modo) => D.portais.portais.filter((x) => x[modo]).map((x) =>
    `<a href="${esc(linkPortal(x[modo], x, b))}" target="_blank" rel="noopener noreferrer">${esc(x.nome)}</a>`).join("");
  $("#detalhe-bairro").innerHTML = `
    <div class="ilustracao ilustracao-fina" aria-hidden="true"></div>
    <div class="detalhe-topo">
      <div><p class="sobretitulo">Bairro · ${esc(localTexto(b).split(" · ")[0])}</p><h2>${esc(b.nome)}</h2>
        <p class="cartao-regiao">${icone("local")}${esc(localTexto(b))} · ${b.populacao_2022.toLocaleString("pt-BR")} moradores (Censo 2022)</p>
        ${destaques(n)}</div>
      <div class="detalhe-nota">${anel(n.final, 84)}<span class="pequeno">nota final</span></div>
    </div>
    <div class="bloco perfil-bairro">
      <div><h3>Em resumo</h3>${resumoTexto(b, n).map((f) => `<p>${esc(f)}</p>`).join("")}
        <p class="pequeno">Texto gerado a partir das notas e do ITBI; cada número tem a fonte nos blocos abaixo.</p></div>
      ${radar([{ nome: b.nome, notas: n, cor: CORES_SERIE[0] }], 300)}
    </div>
    ${b.sem_nota_final ? `<p class="aviso">Este bairro não tem nota final nem posição no ranking. ${esc(b.sem_nota_final_motivo)} Os outros critérios, o preço e o simulador continuam valendo.</p>` : ""}
    ${!estado.perfil && !b.sem_nota_final ? '<p class="destaque">Nota final com todos os critérios com o mesmo peso. <a href="#perfil">Responda as perguntas</a> para ajustar às suas prioridades.</p>' : ""}
    <div class="compartilhar">
      <a class="btn btn-whats" id="whats" target="_blank" rel="noopener noreferrer"
         href="https://wa.me/?text=${encodeURIComponent(textoCompartilhar(b))}">${icone("whats", "icone")}Compartilhar no WhatsApp</a>
      ${navigator.share ? '<button class="btn" id="compartilhar-nativo" type="button">Compartilhar</button>' : ""}
      <button class="btn" id="copiar-bairro" type="button">Copiar link</button>
      <button class="btn" type="button" data-imprimir>Imprimir ou PDF</button>
      <span id="msg-compartilhar" class="pequeno" role="status"></span>
    </div>
    <div class="acoes-detalhe">
      <button class="btn-principal" id="ir-simulador">Simular financiamento</button>
      <button class="btn" id="add-comparar" aria-pressed="${estado.comparar.includes(b.codbairro)}">${estado.comparar.includes(b.codbairro) ? "✓ Na comparação" : "+ Adicionar à comparação"}</button>
    </div>
    ${D.mapa ? `<div class="bloco mapa-mini"><h3>Onde fica</h3><div id="mapa-detalhe">${svgMapa({ destaque: b.codbairro })}</div>
      <p class="pequeno">Toque em outro bairro para comparar. Fonte: ${esc(D.mapa.fonte)}.</p></div>` : ""}
    ${preco}
    ${D.bairros.criterios.map((c) => blocoCriterio(b, c, n)).join("")}
    <div class="bloco"><h3>Imóveis da Caixa à venda neste bairro</h3>${blocoImoveisCaixa(b)}</div>
    <div class="bloco"><h3>Anúncios nos portais</h3>
      <p class="pequeno">Você vai sair do app. Os anúncios são dos portais e não foram verificados por este site.</p>
      <p><strong>À venda:</strong></p><div class="links-portais">${portais("venda")}</div>
      <p><strong>Para alugar:</strong></p><div class="links-portais">${portais("aluguel")}</div>
    </div>`;
  $("#ir-simulador").addEventListener("click", () => ir("financiamento/" + cod));
  $("#copiar-bairro").addEventListener("click", () => {
    const ok = () => ($("#msg-compartilhar").textContent = "Link copiado.");
    if (navigator.clipboard) navigator.clipboard.writeText(linkBairro(b)).then(ok, () => ($("#msg-compartilhar").textContent = linkBairro(b)));
    else $("#msg-compartilhar").textContent = linkBairro(b);
  });
  if ($("#compartilhar-nativo")) $("#compartilhar-nativo").addEventListener("click", () =>
    navigator.share({ title: `${b.nome} · Onde Comprar no Rio`, text: `Veja ${b.nome} no Onde Comprar no Rio`, url: linkBairro(b) }).catch(() => {}));
  $("#add-comparar").addEventListener("click", () => { alternarComparar(cod); desenharBairro(cod); atualizarBarraComparar("bairro"); });
  if ($("#mapa-detalhe")) ligarMapa($("#mapa-detalhe"));
}

/* ---------------- simulador ---------------- */
const taxaMensal = (aa) => Math.pow(1 + aa / 100, 1 / 12) - 1;

// Price: parcela fixa P = V * i / (1 - (1+i)^-n)
function price(V, i, n) {
  const P = i ? V * i / (1 - Math.pow(1 + i, -n)) : V / n;
  return { primeira: P, ultima: P, total: P * n, juros: P * n - V };
}
// SAC: amortizacao fixa A = V/n; parcela k = A + saldo antes da parcela k * i.
// Soma dos juros = i * A * (n + (n-1) + ... + 1) = i * A * n(n+1)/2
function sac(V, i, n) {
  const A = V / n, juros = i * A * n * (n + 1) / 2;
  return { primeira: A + V * i, ultima: A + A * i, total: V + juros, juros };
}
// Maior valor financiado cuja (primeira) parcela cabe em pmax
const maxPrice = (pmax, i, n) => i ? pmax * (1 - Math.pow(1 + i, -n)) / i : pmax * n;
const maxSac = (pmax, i, n) => pmax / (1 / n + i);

function faixaMCMV(renda) {
  return D.params.mcmv.faixas.find((f) => renda > 0 && renda <= f.renda_ate) || null;
}

// Linha provavel para uma renda e um preco: MCMV se renda e preco cabem; senao SBPE.
function linha(renda, preco) {
  const f = faixaMCMV(renda);
  if (f && (preco == null || preco <= f.teto_imovel)) {
    return { nome: "MCMV - " + f.faixa, chave: "mcmv", juros: estado.cotista ? f.juros_cotista : f.juros_nao_cotista, teto: f.teto_imovel, faixa: f };
  }
  return { nome: "SBPE", chave: "sbpe", juros: D.params.sbpe.juros_ano, teto: null, faixa: f };
}

// Cota maxima de financiamento (parte do imovel que o banco financia), por linha ("sbpe", "mcmv")
// e sistema ("sac", "price"). Vem do JSON, com a fonte.
const cotaDe = (chave, sistema) => D.params.cota_max[chave][sistema];
const pctTxt = (x) => fmtN(x * 100, 0) + "%";

// Preco maximo = o MENOR entre:
//  - "renda":   financiamento cuja parcela cabe na renda + entrada + FGTS
//  - "entrada": (entrada + FGTS) / (1 - cota), porque o banco so financia a cota do imovel
//  - "teto":    teto do MCMV, quando houver
function limitePreco(financiavel, recursos, cota, teto) {
  const op = [["renda", financiavel + recursos], ["entrada", recursos / (1 - cota)]];
  if (teto) op.push(["teto", teto]);
  const [limite, preco] = op.reduce((a, o) => (o[1] < a[1] ? o : a));
  return { preco, limite, cota };
}

function capacidade(renda, juros, anos, teto, chave) {
  const pmax = renda * D.params.comprometimento_renda_max, i = taxaMensal(juros), n = anos * 12;
  const recursos = estado.entrada + estado.fgts;
  const sacL = limitePreco(maxSac(pmax, i, n), recursos, cotaDe(chave, "sac"), teto);
  const priceL = limitePreco(maxPrice(pmax, i, n), recursos, cotaDe(chave, "price"), teto);
  return { pmax, recursos, sac: sacL, price: priceL, precoSac: sacL.preco, precoPrice: priceL.preco };
}

// Frase que diz qual limite travou o preco maximo
function textoLimite(l, teto) {
  if (l.limite === "entrada") {
    return l.preco > 0
      ? `Limitado pela sua entrada: com cota de ${pctTxt(l.cota)}, a entrada (dinheiro + FGTS) precisa ser de pelo menos ${pctTxt(1 - l.cota)} do imóvel.`
      : `Sem entrada não dá para financiar: o banco financia até ${pctTxt(l.cota)} do imóvel, então a entrada (dinheiro + FGTS) precisa ser de pelo menos ${pctTxt(1 - l.cota)}.`;
  }
  if (l.limite === "teto") return `Limitado ao teto do MCMV (${fmtR(teto)}).`;
  return `Limitado pela sua renda: a parcela cabe em até ${pctTxt(D.params.comprometimento_renda_max)} da renda.`;
}

function desenharSimulador() {
  const P = D.params;
  $("#aviso-geral").textContent = P.aviso_geral;
  const b = D.bairros.bairros.find((x) => x.codbairro === estado.bairroAtual);
  const precoSug = b ? Math.round((precoEstimado(b) || 0) / 1000) * 1000 : 0;
  const rendaTotal = estado.renda1 + estado.renda2;
  const lin0 = linha(rendaTotal, precoSug || null);
  $("#simulador").innerHTML = `
    <div class="bloco">
      <h3>${b ? "Imóvel em " + esc(b.nome) : "Imóvel"}</h3>
      <div class="grade-2">
        <label>Preço do imóvel<input type="text" inputmode="numeric" id="s-preco" class="dinheiro" value="${precoSug ? fmtR(precoSug) : ""}"></label>
        <label>Renda bruta total<input type="text" inputmode="numeric" id="s-renda" class="dinheiro" value="${rendaTotal ? fmtR(rendaTotal) : ""}"></label>
        <label>Entrada (dinheiro)<input type="text" inputmode="numeric" id="s-entrada" class="dinheiro" value="${estado.entrada ? fmtR(estado.entrada) : ""}"></label>
        <label>FGTS<input type="text" inputmode="numeric" id="s-fgts" class="dinheiro" value="${estado.fgts ? fmtR(estado.fgts) : ""}"></label>
        <label>Prazo (anos)<input type="number" id="s-prazo" min="5" max="${P.mcmv.prazo_max_anos}" value="${P.prazo_padrao_anos}"></label>
        <label>Juros ao ano (%)<input type="number" id="s-juros" step="0.01" min="0" max="30" value="${lin0.juros}"></label>
      </div>
      ${b && b.preco_itbi ? `<p class="pequeno">Preço sugerido: R$/m² médio do ITBI do bairro × ${estado.area ? estado.area + " m²" : "área média"}. Edite à vontade.</p>` : ""}
    </div>
    <div id="s-resultado"></div>`;
  $$("#simulador .dinheiro").forEach((inp) => inp.addEventListener("input", () => {
    const v = lerDinheiro(inp.value); inp.value = v ? fmtR(v) : "";
  }));
  let jurosEditado = false;
  $("#s-juros").addEventListener("input", () => (jurosEditado = true));
  const recalcular = () => {
    estado.entrada = lerDinheiro($("#s-entrada").value);
    estado.fgts = lerDinheiro($("#s-fgts").value);
    const preco = lerDinheiro($("#s-preco").value), renda = lerDinheiro($("#s-renda").value);
    const lin = linha(renda, preco || null);
    if (!jurosEditado) $("#s-juros").value = lin.juros;
    calcular(preco, renda, Number($("#s-prazo").value) || P.prazo_padrao_anos, Number($("#s-juros").value), lin, b);
  };
  // oninput (e nao addEventListener) para nao acumular ouvintes a cada visita ao simulador
  $("#simulador").oninput = (e) => { if (!e.target.closest("#s-resultado")) recalcular(); };
  recalcular();
}

function calcular(preco, renda, anos, juros, lin, b) {
  const P = D.params, n = anos * 12, i = taxaMensal(juros);
  const V = Math.max(preco - estado.entrada - estado.fgts, 0);
  const s = sac(V, i, n), pr = price(V, i, n);
  const itbi = preco * P.itbi.aliquota;
  const pmax = renda * P.comprometimento_renda_max;
  const alertas = [];
  if (lin.faixa && lin.nome === "SBPE") alertas.push(`Sua renda está na ${lin.faixa.faixa} do MCMV, mas o preço passa do teto de ${fmtR(lin.faixa.teto_imovel)}. Por isso a linha provável é o SBPE.`);
  if (lin.faixa && ["Faixa 1", "Faixa 2"].includes(lin.faixa.faixa) && lin.nome !== "SBPE") alertas.push(P.mcmv.subsidio_texto);
  if (pmax && s.primeira > pmax) alertas.push(`A 1ª parcela no SAC (${fmtR(s.primeira)}) passa de ${P.comprometimento_renda_max * 100}% da renda (${fmtR(pmax)}).`);
  if (pmax && pr.primeira > pmax) alertas.push(`A parcela na Price (${fmtR(pr.primeira)}) passa de ${P.comprometimento_renda_max * 100}% da renda.`);
  // cota: o banco so financia uma parte do imovel; o resto e a entrada minima (dinheiro + FGTS)
  const recursos = estado.entrada + estado.fgts;
  const cotas = { sac: cotaDe(lin.chave, "sac"), price: cotaDe(lin.chave, "price") };
  const entMin = { sac: preco * (1 - cotas.sac), price: preco * (1 - cotas.price) };
  const passa = ["sac", "price"].filter((k) => preco && recursos < entMin[k] - 0.5);
  const nomeSis = { sac: "no SAC", price: "na Price" };
  const grupos = cotas.sac === cotas.price ? (passa.length ? [passa] : []) : passa.map((k) => [k]);
  for (const g of grupos) {
    const k = g[0], onde = g.map((x) => nomeSis[x]).join(" e ");
    alertas.push(`O banco financia até ${pctTxt(cotas[k])} do imóvel ${onde} (${fmtR(preco * cotas[k])}). ` +
      `A entrada mínima (dinheiro + FGTS) é de ${fmtR(entMin[k])}; você tem ${fmtR(recursos)}, faltam ${fmtR(entMin[k] - recursos)}.`);
  }

  // renda unica x somada
  let comparaRenda = "";
  if (estado.rendaTipo === "somada" && estado.renda1 && estado.renda2) {
    const linhaPara = (r) => { const l = linha(r, null); return { l, c: capacidade(r, l.juros, anos, l.teto, l.chave) }; };
    const a = linhaPara(estado.renda1), t = linhaPara(estado.renda1 + estado.renda2);
    comparaRenda = `<div class="bloco"><h3>Renda única x somada</h3>
      <div class="rolagem"><table class="tabela"><thead><tr><th></th><th>Só comprador 1</th><th>Os dois</th></tr></thead><tbody>
      ${[["Renda bruta", estado.renda1, estado.renda1 + estado.renda2],
         ["Parcela máxima", a.c.pmax, t.c.pmax],
         ["Preço máximo (SAC)", a.c.precoSac, t.c.precoSac],
         ["Preço máximo (Price)", a.c.precoPrice, t.c.precoPrice]].map(([r, x, y]) =>
        `<tr><td>${r}</td><td>${fmtR(x)}</td><td>${fmtR(y)}<br><span class="pequeno">+${fmtR(y - x)}</span></td></tr>`).join("")}
      <tr><td>Linha provável</td><td style="white-space:normal">${esc(a.l.nome)}</td><td style="white-space:normal">${esc(t.l.nome)}</td></tr>
      </tbody></table></div><p class="pequeno">Cada coluna usa a linha provável daquela renda; o preço máximo respeita a cota de financiamento e o teto do MCMV quando for o caso.</p></div>`;
  }
  const cap = renda ? capacidade(renda, juros, anos, lin.teto, lin.chave) : null;
  const fonteCota = P.cota_max[lin.chave];

  $("#s-resultado").innerHTML = `
    <div class="bloco"><h3>Linha provável: ${esc(lin.nome)} · ${fmtN(juros, 2)}% ao ano</h3>
      ${lin.nome === "SBPE" ? `<p class="pequeno">Taxa padrão: ${esc(P.sbpe.banco)}, ${esc(P.sbpe.modalidade)}, ${esc(P.sbpe.mes)}. ${esc(P.sbpe.aviso)}</p>`
        : `<p class="pequeno">${esc(P.mcmv.fonte)} (página atualizada em ${fmtData(P.mcmv.pagina_atualizada_em)}). Taxa de ${estado.cotista ? "cotista" : "não cotista"} do FGTS; marque a opção de 3 anos de FGTS na etapa de renda se for o seu caso.</p>`}
      ${alertas.map((a) => `<p class="aviso">${esc(a)}</p>`).join("")}
      <p>Valor financiado: <strong>${fmtR(V)}</strong> (preço − entrada − FGTS) em ${n} parcelas.</p>
      <div class="rolagem"><table class="tabela"><thead><tr><th></th><th>SAC</th><th>Price</th></tr></thead><tbody>
        <tr><td>1ª parcela</td><td>${fmtR(s.primeira)}</td><td>${fmtR(pr.primeira)}</td></tr>
        <tr><td>Última parcela</td><td>${fmtR(s.ultima)}</td><td>${fmtR(pr.ultima)}</td></tr>
        <tr><td>Total pago</td><td>${fmtR(s.total)}</td><td>${fmtR(pr.total)}</td></tr>
        <tr><td>Total de juros</td><td>${fmtR(s.juros)}</td><td>${fmtR(pr.juros)}</td></tr>
      </tbody></table></div>
      <p class="pequeno">SAC: parcelas começam maiores e caem; paga menos juros no total. Price: parcela fixa; começa menor e paga mais juros. ${esc(P.simplificacoes)}</p>
    </div>
    ${cap ? `<div class="bloco"><h3>Quanto cabe na sua renda</h3>
      <p>Parcela máxima (${P.comprometimento_renda_max * 100}% da renda): <strong>${fmtR(cap.pmax)}</strong></p>
      <p>Preço máximo do imóvel: <strong>${fmtR(cap.precoSac)}</strong> no SAC · <strong>${fmtR(cap.precoPrice)}</strong> na Price.</p>
      ${cap.sac.limite === cap.price.limite && cap.sac.cota === cap.price.cota
        ? `<p class="pequeno">${esc(textoLimite(cap.sac, lin.teto))}</p>`
        : `<p class="pequeno">SAC: ${esc(textoLimite(cap.sac, lin.teto))}</p><p class="pequeno">Price: ${esc(textoLimite(cap.price, lin.teto))}</p>`}
      <p class="pequeno">${esc(P.comprometimento_renda_texto)} ${esc(fonteCota.texto)} Fonte: ${esc(fonteCota.fonte)}.</p></div>` : ""}
    ${comparaRenda}
    <div class="bloco"><h3>Custos para fechar a compra</h3>
      <div class="rolagem"><table class="tabela"><tbody>
        ${(cotas.sac === cotas.price ? [["", "sac"]] : [[" no SAC", "sac"], [" na Price", "price"]]).map(([onde, k]) =>
          `<tr><td>Entrada mínima${onde} (${pctTxt(1 - cotas[k])})</td><td>${fmtR(entMin[k])}</td></tr>`).join("")}
        <tr><td>Entrada (dinheiro)</td><td>${fmtR(estado.entrada)}</td></tr>
        <tr><td>ITBI (${fmtN(P.itbi.aliquota * 100, 0)}%)</td><td>${fmtR(itbi)}</td></tr>
        ${P.custos_sem_valor.map((c) => `<tr><td>${esc(c.item)}</td><td>consulte</td></tr>`).join("")}
        <tr><th>Dinheiro necessário (sem cartório e avaliação)</th><th>${fmtR(estado.entrada + itbi)}</th></tr>
      </tbody></table></div>
      <p class="pequeno">A entrada mínima pode ser paga com dinheiro e FGTS (${esc(lin.nome)}: o banco financia até ${pctTxt(cotas.sac)} no SAC e ${pctTxt(cotas.price)} na Price).</p>
      <p class="pequeno">ITBI: ${esc(P.itbi.nota)} Fonte: ${esc(P.itbi.fonte)}.</p>
      ${P.custos_sem_valor.map((c) => `<p class="pequeno">${esc(c.item)}: ${esc(c.texto)}</p>`).join("")}
    </div>
    <div class="bloco"><h3>Uso do FGTS</h3>
      ${estado.jaTemImovel ? '<p class="aviso">Você indicou que algum comprador já tem imóvel ou financiamento no SFH. Isso pode impedir o uso do FGTS e o MCMV.</p>' : ""}
      <ul>${P.fgts_avisos.map((a) => `<li>${esc(a)}</li>`).join("")}</ul></div>
    <div class="bloco"><h3>Comparar com aluguel</h3>
      <div class="grade-2">
        <label>Aluguel mensal<input type="text" inputmode="numeric" id="a-aluguel" class="dinheiro" value="${estado.aluguel ? fmtR(estado.aluguel) : ""}"></label>
        <label>Condomínio + IPTU por mês<input type="text" inputmode="numeric" id="a-extras" class="dinheiro" value="${estado.extras ? fmtR(estado.extras) : ""}"></label>
      </div>
      <div id="a-resultado"></div>
      <p class="pequeno">${esc(P.aluguel_aviso)}</p></div>
    <p class="aviso">${esc(P.aviso_geral)}</p>`;

  const aluguel = () => {
    const al = lerDinheiro($("#a-aluguel").value), ex = lerDinheiro($("#a-extras").value);
    estado.aluguel = al; estado.extras = ex;
    if (!al) { $("#a-resultado").innerHTML = renda ? `<p>Aluguel que cabe em ${P.comprometimento_renda_max * 100}% da renda: <strong>${fmtR(pmax)}</strong> (incluindo condomínio e IPTU).</p>` : ""; return; }
    $("#a-resultado").innerHTML = `<div class="rolagem"><table class="tabela"><thead><tr><th>Por mês</th><th>Alugar</th><th>Comprar SAC</th><th>Comprar Price</th></tr></thead><tbody>
      <tr><td>Aluguel ou 1ª parcela</td><td>${fmtR(al)}</td><td>${fmtR(s.primeira)}</td><td>${fmtR(pr.primeira)}</td></tr>
      <tr><td>Condomínio + IPTU</td><td>${fmtR(ex)}</td><td>${fmtR(ex)}</td><td>${fmtR(ex)}</td></tr>
      <tr><th>Total</th><th>${fmtR(al + ex)}</th><th>${fmtR(s.primeira + ex)}</th><th>${fmtR(pr.primeira + ex)}</th></tr></tbody></table></div>
      ${renda ? `<p>Cabe em ${P.comprometimento_renda_max * 100}% da renda (${fmtR(pmax)})? Alugar: <strong>${al + ex <= pmax ? "sim" : "não"}</strong>.</p>` : ""}
      <p>Para comprar, você imobiliza <strong>${fmtR(estado.entrada + estado.fgts + itbi)}</strong> (entrada + FGTS + ITBI).</p>`;
  };
  $$("#s-resultado .dinheiro").forEach((inp) => inp.addEventListener("input", () => {
    const v = lerDinheiro(inp.value); inp.value = v ? fmtR(v) : "";
    aluguel();
  }));
  aluguel();
}

/* ---------------- perguntas frequentes (numeros lidos dos JSON) ---------------- */
function desenharPerguntas() {
  const P = D.params, F = D.bairros.fontes, M = P.mcmv, N = D.bairros.referencia_codigos.length;
  const pct = (x) => fmtN(x * 100, 0) + "%";
  const faixas = [];
  for (const f of M.faixas) {
    const ult = faixas[faixas.length - 1];
    if (ult && ult.faixa === f.faixa) { ult.ate = f.renda_ate; ult.jmax = Math.max(ult.jmax, f.juros_nao_cotista); }
    else faixas.push({ faixa: f.faixa, ate: f.renda_ate, teto: f.teto_imovel, jmin: f.juros_cotista, jmax: f.juros_nao_cotista });
  }
  const perguntas = [
    ["Como a nota de 0 a 10 é calculada?",
     `Cada nota é a posição do bairro entre os ${N} bairros do Rio com pelo menos mil moradores. Nota 8, por exemplo, quer dizer que o bairro está melhor que 80% deles naquele critério.
      Cada indicador é calculado para os setores do Censo 2022 e vira a média dos moradores do bairro. A nota final é a média das 6 notas, pesada pelas prioridades que você escolhe.`],
    ["Por que nota alta em \"Menos alagamento\" e \"Menos barulho\" é bom?",
     `Em todos os critérios, nota alta = melhor. "Menos alagamento" 8 quer dizer que o bairro alaga menos que 80% dos bairros do Rio. Por isso os nomes estão no sentido positivo; nos pontos de atenção aparece o nome do problema (ex.: "Atenção: Alagamento").`],
    ["O que entra na nota de segurança?",
     `Dados do ISP-RJ (${esc(F.violencia.periodo)}), por 100 mil habitantes: letalidade violenta (${pct(F.violencia.indicadores.letalidade_100k.peso)}), roubo de veículo, roubo de rua e roubo a residência (${pct(F.violencia.indicadores.roubo_rua_100k.peso)} cada).
      A letalidade pesa mais por ser o dado mais confiável: roubos são mais registrados em áreas de passagem e menos onde se denuncia menos.`],
    ["Por que bairros vizinhos têm a mesma nota de segurança?",
     "O ISP publica os números por área de delegacia (CISP), não por bairro. Bairros na mesma área de delegacia recebem números iguais ou parecidos. O detalhe de cada bairro mostra qual delegacia cobre os moradores."],
    ["De onde vem o preço do m²?",
     `Das transações declaradas no ITBI à Prefeitura (${esc(F.preco.periodo)}). É o valor médio dividido pela área média das vendas de cada bairro. Mistura casas e apartamentos, novos e usados, e serve como referência, não como avaliação de um imóvel.`],
    ["O que é o Minha Casa, Minha Vida e quem pode usar?",
     `É o programa federal de financiamento com juros menores para famílias com renda bruta de até ${fmtR(faixas[faixas.length - 1].ate)}. Pelas regras atuais (${esc(M.fonte)}, página de ${fmtData(M.pagina_atualizada_em)}):
      <ul>${faixas.map((f) => `<li><strong>${esc(f.faixa)}</strong>: renda até ${fmtR(f.ate)}; imóvel de até ${fmtR(f.teto)}; juros de ${fmtN(f.jmin, 2)}% a ${fmtN(f.jmax, 2)}% ao ano (Sudeste).</li>`).join("")}</ul>
      Fora dessas condições, a linha comum é o SBPE (no app: ${fmtN(P.sbpe.juros_ano, 2)}% ao ano, média da Caixa no Banco Central em ${esc(P.sbpe.mes)}).`],
    ["SAC ou Price: qual escolher?",
     "No SAC, você paga a mesma amortização todo mês, então a parcela começa maior e vai caindo, e o total de juros é menor. Na Price, a parcela é fixa: começa menor, mas o total de juros é maior. O simulador mostra os dois lado a lado. Os bancos costumam aprovar o valor pela 1ª parcela, que no SAC é a maior."],
    ["Preciso dar entrada? De quanto?",
     `Sim. O banco financia só uma parte do valor do imóvel (a cota); o resto é a entrada, que pode ser paga com dinheiro e FGTS.
      <ul><li><strong>SBPE (Caixa)</strong>: financia até ${pct(P.cota_max.sbpe.sac)} no SAC e ${pct(P.cota_max.sbpe.price)} na Price, então a entrada é de pelo menos ${pct(1 - P.cota_max.sbpe.sac)} ou ${pct(1 - P.cota_max.sbpe.price)}. Fonte: ${esc(P.cota_max.sbpe.fonte)}.</li>
      <li><strong>Minha Casa, Minha Vida</strong>: financia até ${pct(P.cota_max.mcmv.sac)}, então a entrada é de pelo menos ${pct(1 - P.cota_max.mcmv.sac)}. ${esc(P.cota_max.mcmv.texto)} Fonte: ${esc(P.cota_max.mcmv.fonte)}.</li>
      <li><strong>Pró-Cotista</strong>: ${esc(P.cota_max.pro_cotista.texto)}</li></ul>
      Por isso, sem entrada o preço máximo é zero, mesmo com renda alta. Outros bancos podem ter cotas diferentes.`],
    ["Quanto da renda posso comprometer com a parcela?",
     `O app usa até ${pct(P.comprometimento_renda_max)} da renda bruta. ${esc(P.comprometimento_renda_texto)} Cada banco faz a própria análise.`],
    ["Posso usar o FGTS?",
     `Em geral, sim, na entrada ou para amortizar, se cumprir as regras: <ul>${P.fgts_avisos.map((a) => `<li>${esc(a)}</li>`).join("")}</ul>`],
    ["Quais custos existem além da entrada?",
     `ITBI de ${pct(P.itbi.aliquota)} sobre o valor do imóvel (Prefeitura do Rio), escritura e registro em cartório e a avaliação do imóvel pelo banco.
      ${P.custos_sem_valor.map((c) => esc(c.texto)).join(" ")}`],
    ["A simulação vale como aprovação do banco?",
     `Não. ${esc(P.aviso_geral)} ${esc(P.simplificacoes)}`],
    ["O app guarda ou envia meus dados?",
     "Não. Tudo é calculado no seu aparelho. Renda, entrada e prioridades ficam só na memória da página e somem ao fechar. Os links de compartilhar levam só o bairro (ou o perfil e as prioridades), nunca valores."],
    ["Por que alguns bairros não têm nota final?",
     `<p>Em ${D.bairros.subnotificacao.bairros.length} bairros, ${D.bairros.subnotificacao.corte_pct}% ou mais dos moradores vivem em área de favela (${esc(D.bairros.subnotificacao.fonte)}).
      Nessas áreas, boletins de ocorrência e chamados ao 1746 costumam ser pouco registrados, e o app leria "pouco registro" como "pouco problema".
      Por isso esses bairros ficam sem nota de Segurança e de Menos barulho e sem nota final; os outros critérios, o preço e o simulador continuam.
      São eles: ${esc(D.bairros.subnotificacao.bairros.join(", "))}.</p>
      ${D.bairros.seguranca_insuficiente.bairros.length ? `<p>Em outros ${D.bairros.seguranca_insuficiente.bairros.length} bairros, só Segurança fica sem nota (e por isso também a nota final):
      a taxa do ISP é calculada para a área inteira da delegacia, e nesses bairros ela não representa bem quem mora ali
      (bairro separado fisicamente do resto da área da delegacia, como uma ilha).
      São eles: ${esc(D.bairros.seguranca_insuficiente.bairros.map((x) => x.nome).join(", "))}.</p>` : ""}`],
    ["Por que alguns bairros têm aviso de \"muita gente de fora\" em Segurança?",
     `A taxa de crimes é dividida só pelos moradores. Onde muita gente vai trabalhar, comprar ou passear, os roubos de rua acontecem com quem está de passagem,
      mas entram na conta como se fossem dos moradores. O app marca as áreas de delegacia em que o roubo de rua passa de ${fmtN(D.bairros.publico_de_fora.fator_mediana, 0)} vezes
      a mediana dos bairros (${fmtN(D.bairros.publico_de_fora.mediana, 0)} por 100 mil). Hoje isso vale para: ${esc(D.bairros.publico_de_fora.bairros.join(", "))}.
      A nota não muda; o aviso serve para ler o número com cuidado.`],
    ["Por que meu bairro não aparece?",
     `O app tem ${D.bairros.bairros.filter((b) => b.tem_nota).length} bairros. Ficam de fora os bairros com menos de mil moradores no Censo 2022 (${esc(D.bairros.bairros.filter((b) => !b.tem_nota).map((b) => b.nome).join(", "))}), porque as taxas por habitante ficariam instáveis.`],
    ["De quando são os dados?",
     `<ul><li>Segurança (ISP): ${esc(F.violencia.periodo)}</li><li>Preço do m² (ITBI): ${esc(F.preco.periodo)}</li>
      <li>Reclamações de barulho (1746): ${esc(F.barulho.fontes[0].periodo)}</li><li>Alagamentos registrados (COR): ${esc(F.alagamento.fontes[1].periodo)}</li>
      <li>Escolas: Censo Escolar e Ideb 2025 (INEP)</li><li>População: Censo 2022 (IBGE)</li></ul>
      Detalhes de cada fonte em <a href="#sobre">Sobre os dados</a>.`],
  ];
  $("#perguntas").innerHTML = perguntas.map(([q, r]) =>
    `<details class="pergunta"><summary>${esc(q)}</summary><div class="resposta">${r.includes("<") ? r : `<p>${r}</p>`}</div></details>`).join("");
}

/* ---------------- sobre os dados ---------------- */
function desenharSobre() {
  const F = D.bairros.fontes, P = D.params;
  const lista = (f) => (f.fontes || [{ nome: f.fonte, url: f.url, periodo: f.periodo }])
    .map((x) => `<li>${esc(x.nome)}${x.periodo ? ` (${esc(x.periodo)})` : ""}${x.url ? ` · <a href="${esc(x.url)}" target="_blank" rel="noopener noreferrer">link</a>` : ""}</li>`).join("");
  const inds = (f) => f.indicadores ? `<ul>${Object.values(f.indicadores).map((i) =>
    `<li>${esc(i.rotulo)}${i.peso != null ? ` (peso ${fmtN(i.peso * 100, 0)}%)` : ""}; ${i.maior_e_pior ? "quanto maior, pior" : "quanto maior, melhor"}.</li>`).join("")}</ul>` : "";
  const avisos = (f) => [].concat(f.aviso || [], f.avisos || []).map((a) => `<p class="pequeno">${esc(a)}</p>`).join("");
  $("#sobre").innerHTML = `
    <div class="sobre-fonte"><h3>Como a nota é calculada</h3>
      <p>${esc(D.bairros.metodo_nota)}</p>
      <p>Cada indicador é calculado para cada setor do Censo 2022 e depois vira a média dos moradores do bairro
        (média ponderada pela população). Assim, áreas sem moradores, como morros com floresta, não distorcem o bairro.</p>
      <p>Em todos os critérios, <strong>nota alta = melhor</strong>. Por isso os nomes estão no sentido positivo:
        "Segurança" (menos mortes violentas e roubos), "Menos alagamento" e "Menos barulho".
        Nos pontos de atenção aparece o nome do problema (ex.: "Atenção: Alagamento").</p>
      <p>A nota de cada critério é a média ponderada das notas dos seus indicadores. A nota final é a média das 6 notas,
        com os pesos de 1 a 5 que você escolhe.</p>
      <p>Bairros com menos de mil moradores não recebem nota. Dados gerados em ${fmtData(D.bairros.gerado_em)}.</p></div>
    ${D.bairros.criterios.map((c) => `<div class="sobre-fonte"><h3>${ROTULOS[c]}</h3>
      <ul>${lista(F[c])}</ul>${inds(F[c])}${avisos(F[c])}
      ${c === "emprego" ? `<p class="pequeno">Polos: ${Object.values(F.emprego.polos).map((p) => esc(p.rotulo)).join(", ")}.</p>` : ""}
      ${c === "escolas" ? `<p class="pequeno">Escolas consideradas: ${F.escolas.escolas_consideradas} (${F.escolas.localizadas_por_coordenada} por coordenada, ${F.escolas.localizadas_pelo_endereco} pelo bairro do endereço).</p>` : ""}
      </div>`).join("")}
    <div class="sobre-fonte"><h3>Preço de referência (ITBI)</h3>
      <ul>${lista(F.preco)}</ul>${avisos(F.preco)}<p class="pequeno">O preço não entra na nota; serve para estimar o valor e marcar o que passa do orçamento.</p></div>
    <div class="sobre-fonte"><h3>Simulador</h3>
      <ul><li>${esc(P.mcmv.fonte)}, página atualizada em ${fmtData(P.mcmv.pagina_atualizada_em)} · <a href="${esc(P.mcmv.url)}" target="_blank" rel="noopener noreferrer">link</a></li>
      <li>${esc(P.sbpe.fonte)}, ${esc(P.sbpe.mes)} · <a href="${esc(P.sbpe.url)}" target="_blank" rel="noopener noreferrer">link</a></li>
      <li>${esc(P.itbi.fonte)} · <a href="${esc(P.itbi.url)}" target="_blank" rel="noopener noreferrer">link</a></li>
      ${["sbpe", "mcmv", "pro_cotista"].map((k) => `<li>Cota de financiamento: ${esc(P.cota_max[k].fonte)} · <a href="${esc(P.cota_max[k].url)}" target="_blank" rel="noopener noreferrer">link</a></li>`).join("")}</ul>
      <p class="pequeno">${esc(P.cota_max_texto)}</p>
      <p class="pequeno">${esc(P.mcmv.divergencia)}</p><p class="pequeno">${esc(P.simplificacoes)}</p></div>
    <div class="sobre-fonte"><h3>Imóveis e anúncios</h3>
      <p class="pequeno">Imóveis da Caixa: lista oficial de imóveis retomados (venda direta e leilão)${D.caixa.data_lista ? `, de ${fmtData(D.caixa.data_lista)}` : ""}.
      Os botões dos portais só abrem a busca do portal; este app não lê nem copia anúncios.</p></div>
    <div class="sobre-fonte"><h3>Privacidade</h3><p>Tudo é calculado no seu aparelho. Nada do que você digita é enviado ou guardado.
      O link de compartilhamento leva só o perfil e as prioridades.</p></div>`;
}

/* ---------------- tela inicial ---------------- */
function desenharInicio() {
  const lista = D.bairros.bairros.filter((b) => b.tem_nota);
  $("#ir-bairro").innerHTML = '<option value="">Escolha um bairro</option>' +
    lista.slice().sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"))
      .map((b) => `<option value="${b.codbairro}">${esc(b.nome)}</option>`).join("");
  $("#ir-bairro").addEventListener("change", (e) => { if (e.target.value) ir("bairro/" + e.target.value); });
  // exemplo: o bairro com maior nota usando pesos iguais (dados reais do app)
  const com = lista.map((b) => ({ b, n: notasDoBairro(b) })).filter((x) => x.n.final != null).sort((x, y) => y.n.final - x.n.final);
  const { b, n } = com[0];
  $("#exemplo").innerHTML = `<div class="exemplo-cartao">
      <div class="exemplo-topo"><div><span class="cartao-regiao">${icone("local")}${esc(localTexto(b))}</span>
        <strong class="exemplo-nome">${esc(b.nome)}</strong></div><span class="selo selo-mini">Exemplo real</span></div>
      <div class="exemplo-meio">${anel(n.final, 76)}<p class="pequeno">Nota final com todos os critérios com o mesmo peso.
        Cada nota é a posição do bairro entre ${D.bairros.referencia_codigos.length} bairros do Rio.</p></div>
      ${barras(n)}
    </div>`;
}

/* ---------------- inicio ---------------- */
async function iniciar() {
  try {
    await carregar();
  } catch (e) {
    $("#carregando").textContent = "Não foi possível carregar os dados. Tente recarregar a página.";
    return;
  }
  $("#carregando").hidden = true;
  $("#n-bairros").textContent = D.bairros.bairros.filter((b) => b.tem_nota).length;
  $("#n-fontes").textContent = 9;
  desenharInicio();
  $("#data-geracao").textContent = fmtData(D.bairros.gerado_em);
  montarSelectTrabalho();
  ligarFormulario();
  lerLinkCompartilhado();
  $("#trabalho1").addEventListener("change", async (e) => { if (e.target.value.startsWith("bairro:")) await carregarDistancias(); });
  $("#trabalho2").addEventListener("change", async (e) => { if (e.target.value.startsWith("bairro:")) await carregarDistancias(); });
  window.addEventListener("hashchange", mostrar);
  mostrar();
}

iniciar();
