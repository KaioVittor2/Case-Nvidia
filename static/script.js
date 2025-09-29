// Front-end logic for "Descobrir Investimentos de VCs"
(() => {
  // --- DOM elements
  const searchForm = document.getElementById("searchForm");
  const vcInput = document.getElementById("vc_input");
  const suggestionsEl = document.getElementById("suggestions");
  const chips = document.querySelectorAll(".chip");
  const resultsEl = document.getElementById("results");
  const emptyState = document.getElementById("emptyState");
  const toggleRaw = document.getElementById("toggleRaw");
  const btnHistorico = document.getElementById("btnHistorico");
  const historyPanel = document.getElementById("historyPanel");
  const historyList = document.getElementById("historyList");
  const closeHistory = document.getElementById("closeHistory");
  const toast = document.getElementById("toast");
  const btnExportCsv = document.getElementById("btnExportCsv");
  const btnPrint = document.getElementById("btnPrint");

  const filterYearFrom = document.getElementById("filter_year_from");
  const filterYearTo = document.getElementById("filter_year_to");
  const filterSector = document.getElementById("filter_sector");
  const filterMinValue = document.getElementById("filter_min_value");
  const filterMaxValue = document.getElementById("filter_max_value");
  const btnClearFilters = document.getElementById("btnClearFilters");

  const statTotalStartups = document.getElementById("statTotalStartups");
  const statTotalValue = document.getElementById("statTotalValue");
  const statTotalVCs = document.getElementById("statTotalVCs");
  const sectorChart = document.getElementById("sectorChart");

  const selectedCountEl = document.getElementById("selectedCount");
  const btnCompare = document.getElementById("btnCompare");
  const btnSaveSelected = document.getElementById("btnSaveSelected");
  const btnClearSaved = document.getElementById("btnClearSaved");

  const compareModal = document.getElementById("compareModal");
  const closeCompare = document.getElementById("closeCompare");
  const compareArea = document.getElementById("compareArea");

  // state
  let currentResults = [];    // array of startup objects
  let filteredResults = [];
  let selectedIds = new Set();
  let savedSet = loadSaved(); // map id->startup
  let currentVCs = [];

  // suggestions
  const sampleSuggestions = ["Sequoia Capital","SoftBank","a16z","Kaszek","Monashees"];
  buildSuggestions();

  // events
  chips.forEach(ch => ch.addEventListener("click", () => {
    vcInput.value = vcInput.value ? vcInput.value + ", " + ch.textContent : ch.textContent;
  }));

  searchForm.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const v = vcInput.value.trim();
    if (!v) return showToast("Digite pelo menos um VC.");
    const vcList = v.split(",").map(s => s.trim()).filter(Boolean);
    await performSearch(vcList);
  });

  btnHistorico.addEventListener("click", showHistoryPanel);
  closeHistory && closeHistory.addEventListener("click", () => historyPanel.classList.add("hidden"));

  btnExportCsv.addEventListener("click", () => {
    if (!filteredResults.length) return showToast("Sem resultados para exportar.");
    downloadCSV(filteredResults);
  });

  btnPrint.addEventListener("click", () => {
    window.print();
  });

  toggleRaw.addEventListener("change", () => renderResults(filteredResults));

  filterYearFrom.addEventListener("change", applyFilters);
  filterYearTo.addEventListener("change", applyFilters);
  filterSector.addEventListener("input", applyFilters);
  filterMinValue.addEventListener("input", applyFilters);
  filterMaxValue.addEventListener("input", applyFilters);
  btnClearFilters.addEventListener("click", () => {
    filterYearFrom.value = filterYearTo.value = filterSector.value = filterMinValue.value = filterMaxValue.value = "";
    applyFilters();
  });

  btnCompare.addEventListener("click", openCompareModal);
  closeCompare && closeCompare.addEventListener("click", () => compareModal.classList.add("hidden"));
  btnSaveSelected.addEventListener("click", saveSelected);
  btnClearSaved.addEventListener("click", () => {
    localStorage.removeItem("savedStartups");
    savedSet = {};
    showToast("Favoritos limpos.");
  });

  // initial empty
  showEmptyState(true);

  // ----- functions -----
  function buildSuggestions() {
    suggestionsEl.innerHTML = "";
    sampleSuggestions.forEach(s => {
      const b = document.createElement("button");
      b.className = "chip";
      b.type = "button";
      b.textContent = s;
      b.addEventListener("click", () => {
        vcInput.value = s;
      });
      suggestionsEl.appendChild(b);
    });
  }

  async function performSearch(vcList) {
    showEmptyState(false);
    showLoading(true);
    try {
      // call backend /pesquisar
      const res = await fetch("/pesquisar", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({vc_list: vcList})
      });
      const json = await res.json();
      if (!res.ok) {
        showToast(json.erro || "Erro na busca");
        showLoading(false);
        return;
      }
      const payload = json.resultado;
      // The agent returns possibly a list or an object. Normalize.
      let arr = [];
      if (Array.isArray(payload)) arr = payload;
      else if (payload && payload.result && Array.isArray(payload.result)) arr = payload.result;
      else if (payload && typeof payload === "object" && !Array.isArray(payload)) {
        // If it's a mapping or an object with keys that represent startups, try to extract
        // but safest is to wrap object in array
        arr = Array.isArray(payload) ? payload : [payload];
      } else {
        arr = [];
      }

      // Normalize expected keys (safe access)
      currentResults = arr.map(normalizeStartup);
      currentVCs = vcList;
      // apply filters & render
      applyFilters();

      // success message
      showToast(`Resultados carregados: ${currentResults.length}`);
    } catch (err) {
      console.error(err);
      showToast("Erro ao buscar. Verifique o servidor.");
    } finally {
      showLoading(false);
    }
  }

  function normalizeStartup(raw) {
    // raw may already match expected keys; try a best-effort normalization.
    const r = raw || {};
    return {
      id: r.id || r.nome?.toString().slice(0,20) + "-" + Math.random().toString(36).slice(2,7),
      nome: r.nome || r.name || r.company || "Nome não informado",
      site: r.site || r.url || r.website || "",
      setor: r.setor || r.sector || r.industry || "—",
      ano_fundacao: r.ano_fundacao || r.year || r.founded_year || null,
      valor_investimento: r.valor_investimento || r.investment_value || r.valor || "—",
      rodada: r.rodada || r.round || "—",
      data_investimento: r.data_investimento || r.investment_date || "—",
      vc_investidor: r.vc_investidor || r.vc || "—",
      descricao_breve: r.descricao_breve || r.description || r.bio || "",
      linkedin_fundador: r.linkedin_fundador || r.linkedin || r.founder_linkedin || "",
      raw: r
    };
  }

  function applyFilters() {
    const yFrom = Number(filterYearFrom.value) || null;
    const yTo = Number(filterYearTo.value) || null;
    const sector = (filterSector.value || "").trim().toLowerCase();
    const minVal = parseMaybeHumanNumber(filterMinValue.value);
    const maxVal = parseMaybeHumanNumber(filterMaxValue.value);

    filteredResults = currentResults.filter(s => {
      if (yFrom && s.ano_fundacao && Number(s.ano_fundacao) < yFrom) return false;
      if (yTo && s.ano_fundacao && Number(s.ano_fundacao) > yTo) return false;
      if (sector && s.setor && !s.setor.toLowerCase().includes(sector)) return false;
      const numericVal = parseMaybeHumanNumber(String(s.valor_investimento || ""));
      if (minVal !== null && numericVal !== null && numericVal < minVal) return false;
      if (maxVal !== null && numericVal !== null && numericVal > maxVal) return false;
      return true;
    });
    renderResults(filteredResults);
  }

  function renderResults(list) {
    resultsEl.innerHTML = "";
    if (!list || !list.length) {
      showEmptyState(true);
      updateStats([]);
      drawSectorChart({});
      return;
    }
    showEmptyState(false);
    list.forEach(item => {
      const c = createCard(item);
      resultsEl.appendChild(c);
    });
    updateStats(list);
    drawSectorChart(buildSectorCounts(list));
  }

  function createCard(item) {
    const el = document.createElement("article");
    el.className = "startup-card";
    el.dataset.id = item.id;

    // top
    const top = document.createElement("div");
    top.className = "startup-top";

    const logoWrap = document.createElement("div");
    logoWrap.className = "logo-wrap";
    // try logo from raw or site favicon (not fetched). Use initials fallback.
    const initials = (item.nome || "—").split(" ").slice(0,2).map(t => t[0]?.toUpperCase()||"").join("");
    logoWrap.textContent = initials;

    const body = document.createElement("div");
    body.className = "startup-body";
    const title = document.createElement("div");
    title.className = "startup-title";
    title.textContent = item.nome;

    const desc = document.createElement("div");
    desc.className = "startup-desc";
    desc.textContent = item.descricao_breve || "Sem descrição disponível.";

    const tags = document.createElement("div");
    tags.className = "tags";
    if (item.setor) {
      const t = document.createElement("span"); t.className = "tag"; t.textContent = item.setor; tags.appendChild(t);
    }
    if (item.rodada) {
      const t = document.createElement("span"); t.className = "tag"; t.textContent = item.rodada; tags.appendChild(t);
    }

    const meta = document.createElement("div");
    meta.className = "meta";
    const val = document.createElement("span"); val.textContent = formatInvestment(item.valor_investimento);
    const founded = document.createElement("span"); founded.textContent = item.ano_fundacao ? `Fundação: ${item.ano_fundacao}` : "";
    const dateInv = document.createElement("span"); dateInv.textContent = item.data_investimento ? `Investido: ${item.data_investimento}` : "";
    meta.append(val, founded, dateInv);

    body.append(title, desc, tags, meta);

    top.append(logoWrap, body);

    // actions
    const actions = document.createElement("div");
    actions.className = "card-actions";

    const leftActions = document.createElement("div");
    leftActions.style.display="flex"; leftActions.style.gap="8px";

    const selectCb = document.createElement("input");
    selectCb.type = "checkbox";
    selectCb.addEventListener("change", (e)=>{
      if (e.target.checked) selectedIds.add(item.id); else selectedIds.delete(item.id);
      updateSelectedUI();
    });

    const saveBtn = document.createElement("button");
    saveBtn.className = "small-btn";
    saveBtn.textContent = savedSet[item.id] ? "Salvo" : "Salvar";
    saveBtn.addEventListener("click", () => {
      savedSet[item.id] = item;
      persistSaved();
      saveBtn.textContent = "Salvo";
      showToast("Startup salva em favoritos (local).");
    });

    leftActions.append(selectCb, saveBtn);

    const rightActions = document.createElement("div");
    rightActions.style.display="flex"; rightActions.style.gap="8px";

    const linkBtn = document.createElement("button");
    linkBtn.className = "small-btn";
    linkBtn.textContent = "LinkedIn";
    linkBtn.addEventListener("click", () => {
      if (item.linkedin_fundador) window.open(item.linkedin_fundador, "_blank");
      else showToast("Link do LinkedIn não disponível.");
    });

    const detailsBtn = document.createElement("button");
    detailsBtn.className = "small-btn";
    detailsBtn.textContent = "Ver";
    detailsBtn.addEventListener("click", () => {
      // toggle raw JSON or simple modal with full data
      showDetailsModal(item);
    });

    rightActions.append(linkBtn, detailsBtn);

    actions.append(leftActions, rightActions);

    // optionally show raw
    const rawPre = document.createElement("pre");
    rawPre.style.maxHeight="200px"; rawPre.style.overflow="auto"; rawPre.style.display = toggleRaw.checked ? "block" : "none";
    rawPre.textContent = JSON.stringify(item.raw, null, 2);

    el.append(top, actions, rawPre);

    return el;
  }

  function updateSelectedUI() {
    selectedCountEl.textContent = selectedIds.size;
    btnCompare.disabled = selectedIds.size < 2;
    btnSaveSelected.disabled = selectedIds.size === 0;
  }

  function openCompareModal(){
    compareArea.innerHTML = "";
    const items = currentResults.filter(s => selectedIds.has(s.id));
    if (!items.length) { showToast("Selecione ao menos 2 startups."); return; }
    items.forEach(it => {
      const c = document.createElement("div"); c.className = "compare-card";
      c.innerHTML = `
        <h4 style="margin:6px 0">${escapeHtml(it.nome)}</h4>
        <p style="color:${'var(--muted)'}">${escapeHtml(it.descricao_breve || '')}</p>
        <ul style="margin-top:8px">
          <li><strong>Setor:</strong> ${escapeHtml(it.setor || '—')}</li>
          <li><strong>Fundação:</strong> ${escapeHtml(it.ano_fundacao || '—')}</li>
          <li><strong>Rodada:</strong> ${escapeHtml(it.rodada || '—')}</li>
          <li><strong>Valor:</strong> ${escapeHtml(formatInvestment(it.valor_investimento))}</li>
          <li><strong>LinkedIn:</strong> ${it.linkedin_fundador ? `<a target="_blank" href="${escapeHtml(it.linkedin_fundador)}">perfil</a>` : '—'}</li>
        </ul>
      `;
      compareArea.appendChild(c);
    });
    compareModal.classList.remove("hidden");
  }

  function saveSelected() {
    const items = currentResults.filter(s => selectedIds.has(s.id));
    items.forEach(it => savedSet[it.id] = it);
    persistSaved();
    showToast(`${items.length} startup(s) salvas (local).`);
  }

  function saveAndPersistOne(it) {
    savedSet[it.id] = it;
    persistSaved();
  }

  function persistSaved() {
    localStorage.setItem("savedStartups", JSON.stringify(savedSet));
  }

  function loadSaved() {
    try {
      return JSON.parse(localStorage.getItem("savedStartups") || "{}") || {};
    } catch (e) { return {}; }
  }

  function showDetailsModal(item) {
    // little modal using window.open could be simple; here we reuse compare modal for detail
    compareArea.innerHTML = "";
    const c = document.createElement("div"); c.className = "compare-card";
    c.innerHTML = `
      <h3>${escapeHtml(item.nome)}</h3>
      <p>${escapeHtml(item.descricao_breve || '')}</p>
      <p><strong>Setor:</strong> ${escapeHtml(item.setor || '—')}</p>
      <p><strong>Fundação:</strong> ${escapeHtml(item.ano_fundacao || '—')}</p>
      <p><strong>Rodada:</strong> ${escapeHtml(item.rodada || '—')}</p>
      <p><strong>Valor:</strong> ${escapeHtml(formatInvestment(item.valor_investimento))}</p>
      <p><strong>LinkedIn:</strong> ${item.linkedin_fundador ? `<a target="_blank" href="${escapeHtml(item.linkedin_fundador)}">perfil</a>` : '—'}</p>
      <pre style="max-height:300px;overflow:auto;margin-top:8px">${JSON.stringify(item.raw, null, 2)}</pre>
    `;
    compareArea.appendChild(c);
    compareModal.classList.remove("hidden");
  }

  function showHistoryPanel(){
    historyPanel.classList.toggle("hidden");
    loadHistory();
  }

  async function loadHistory(){
    historyList.innerHTML = "<div style='padding:12px;color:var(--muted)'>Carregando histórico...</div>";
    try {
      const res = await fetch("/historico");
      const json = await res.json();
      if (!Array.isArray(json) || json.length === 0) {
        historyList.innerHTML = "<div style='padding:12px;color:var(--muted)'>Nenhuma pesquisa encontrada.</div>";
        return;
      }
      historyList.innerHTML = "";
      json.forEach(item => {
        const el = document.createElement("div"); el.className = "history-item";
        const left = document.createElement("div");
        left.innerHTML = `<div style="font-weight:700">${escapeHtml(item.vc_list)}</div><div style="font-size:13px;color:var(--muted)">${(item.resultado && item.resultado.length) ? item.resultado.length + " startups" : "—"}</div>`;
        const right = document.createElement("div");
        const btnLoad = document.createElement("button");
        btnLoad.className = "btn";
        btnLoad.textContent = "Abrir";
        btnLoad.addEventListener("click", () => {
          // load into currentResults and render
          const arr = Array.isArray(item.resultado) ? item.resultado : [item.resultado];
          currentResults = arr.map(normalizeStartup);
          applyFilters();
          showToast("Histórico carregado.");
        });
        right.appendChild(btnLoad);
        el.append(left,right);
        historyList.appendChild(el);
      });
    } catch (err) {
      historyList.innerHTML = "<div style='padding:12px;color:var(--muted)'>Erro ao buscar histórico.</div>";
    }
  }

  function updateStats(list) {
    statTotalStartups.textContent = list.length || 0;
    statTotalVCs.textContent = (currentVCs && currentVCs.length) ? currentVCs.length : "—";
    // total invested
    const total = list.reduce((acc, s) => {
      const n = parseMaybeHumanNumber(String(s.valor_investimento || 0));
      return acc + (n || 0);
    }, 0);
    statTotalValue.textContent = total ? formatCurrency(total) : "—";
  }

  function buildSectorCounts(list) {
    const map = {};
    list.forEach(s => {
      const key = (s.setor || "—").toString();
      map[key] = (map[key] || 0) + 1;
    });
    return map;
  }

  function drawSectorChart(map) {
    const ctx = sectorChart.getContext("2d");
    ctx.clearRect(0,0,sectorChart.width,sectorChart.height);
    const entries = Object.entries(map).sort((a,b)=>b[1]-a[1]).slice(0,6);
    if (!entries.length) {
      ctx.fillStyle = "#9AA2B1";
      ctx.font = "14px sans-serif";
      ctx.fillText("Sem dados para gráfico", 10, 24);
      return;
    }
    // simple bar chart
    const padding = 20;
    const w = sectorChart.width - padding*2;
    const h = sectorChart.height - padding*2;
    const max = Math.max(...entries.map(e=>e[1]));
    const barH = Math.floor(h / entries.length * 0.7);
    entries.forEach((e,i) => {
      const [label, value] = e;
      const y = padding + i * (barH + 10);
      const barW = Math.max(2, (value / max) * (w*0.7));
      ctx.fillStyle = "#0f62fe";
      ctx.fillRect(padding, y, barW, barH);
      ctx.fillStyle = "#111827";
      ctx.font = "12px sans-serif";
      ctx.fillText(`${label} (${value})`, padding + barW + 8, y + barH/1.6);
    });
  }

  function buildCSV(rows) {
    const header = ["nome","site","setor","ano_fundacao","valor_investimento","rodada","data_investimento","vc_investidor","descricao_breve","linkedin_fundador"];
    const lines = [];
    lines.push(header.join(","));
    rows.forEach(r => {
      const arr = header.map(h => {
        const v = r[h] ?? (r[h] === 0 ? "0" : "");
        // escape quotes
        return `"${String(v).replace(/"/g,'""')}"`;
      });
      lines.push(arr.join(","));
    });
    return lines.join("\n");
  }

  function downloadCSV(rows) {
    const csv = buildCSV(rows);
    const blob = new Blob([csv], {type: "text/csv;charset=utf-8;"});
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `startups_export_${new Date().toISOString().slice(0,10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    showToast("CSV gerado para download.");
  }

  // --- helpers
  function showLoading(yes) {
    if (yes) {
      // simple overlay
      if (!document.getElementById("__loading_overlay")) {
        const o = document.createElement("div"); o.id="__loading_overlay";
        o.style.position="fixed"; o.style.inset="0"; o.style.background="rgba(255,255,255,0.6)";
        o.style.zIndex=90; o.innerHTML = `<div style="position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);font-weight:700">Carregando...</div>`;
        document.body.appendChild(o);
      }
    } else {
      const o = document.getElementById("__loading_overlay");
      if (o) o.remove();
    }
  }

  function showEmptyState(show) {
    emptyState.style.display = show ? "block" : "none";
    resultsEl.style.display = show ? "none" : "grid";
  }

  function showToast(msg, ms=2600) {
    toast.textContent = msg;
    toast.classList.remove("hidden");
    toast.style.opacity = "1";
    if (toast._timeout) clearTimeout(toast._timeout);
    toast._timeout = setTimeout(()=>{ toast.classList.add("hidden"); }, ms);
  }

  function formatInvestment(v) {
    if (!v && v !== 0) return "—";
    // if numeric
    if (typeof v === "number") return formatCurrency(v);
    // If string: try to parse; if contains currency sign, return as is
    const str = String(v);
    if (/[$€£]/.test(str)) return str;
    const n = parseMaybeHumanNumber(str);
    if (n !== null) return formatCurrency(n);
    return str;
  }

  function parseMaybeHumanNumber(str) {
    if (!str) return null;
    const s = String(str).replace(/\s+/g,'').replace(/\./g, '').replace(/,/g, '.');
    // find numeric + suffix
    const m = s.match(/([0-9]+(?:\.[0-9]+)?)([kKmMbB])?/)
    if (!m) {
      // last resort - try to extract digits
      const digits = s.replace(/[^\d]/g,'');
      if (!digits) return null;
      return Number(digits);
    }
    let n = Number(m[1]);
    const suf = m[2] ? m[2].toUpperCase() : null;
    if (suf === "K") n *= 1_000;
    if (suf === "M") n *= 1_000_000;
    if (suf === "B") n *= 1_000_000_000;
    return Math.round(n);
  }

  function formatCurrency(num) {
    try {
      return new Intl.NumberFormat('pt-BR', {style:'currency', currency:'BRL', maximumFractionDigits:0}).format(num);
    } catch (e) {
      return num;
    }
  }

  function buildSectorCounts(list) {
    const m = {};
    list.forEach(s => { const k = s.setor || "—"; m[k] = (m[k]||0)+1; });
    return m;
  }

  // minimal escape
  function escapeHtml(s){ return String(s||"").replace(/[&<>"']/g, (c)=> ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }

})();