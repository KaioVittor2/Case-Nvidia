// Enhanced front-end logic for "Descobrir Investimentos de VCs"
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
  const btnPesquisarProfundo = document.getElementById("btnPesquisarProfundo");

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

  const detailsModal = document.getElementById("detailsModal");
  const closeDetails = document.getElementById("closeDetails");

  // state
  let currentResults = [];
  let filteredResults = [];
  let selectedIds = new Set();
  let savedSet = loadSaved();
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
    if (!v) return showToast("Digite pelo menos um VC.", "error");
    const vcList = v.split(",").map(s => s.trim()).filter(Boolean);
    await performSearch(vcList);
  });

  // Event listener para pesquisa profunda
  if (btnPesquisarProfundo) {
    btnPesquisarProfundo.addEventListener("click", async () => {
      const v = vcInput.value.trim();
      if (!v) return showToast("Digite pelo menos um VC para pesquisa profunda.", "error");
      const vcList = v.split(",").map(s => s.trim()).filter(Boolean);
      await performDeepSearch(vcList);
    });
  }

  btnHistorico.addEventListener("click", toggleHistoryPanel);
  closeHistory && closeHistory.addEventListener("click", () => hidePanel(historyPanel));

  btnExportCsv.addEventListener("click", () => {
    if (!filteredResults.length) return showToast("Sem resultados para exportar.", "error");
    downloadCSV(filteredResults);
  });

  btnPrint.addEventListener("click", () => window.print());

  toggleRaw.addEventListener("change", () => {
    document.querySelectorAll('.technical-data').forEach(el => {
      el.classList.toggle('show', toggleRaw.checked);
    });
  });

  [filterYearFrom, filterYearTo, filterSector, filterMinValue, filterMaxValue].forEach(el => {
    el.addEventListener("input", debounce(applyFilters, 300));
  });

  btnClearFilters.addEventListener("click", () => {
    filterYearFrom.value = filterYearTo.value = filterSector.value = filterMinValue.value = filterMaxValue.value = "";
    applyFilters();
    showToast("Filtros limpos", "success");
  });

  btnCompare.addEventListener("click", openCompareModal);
  closeCompare && closeCompare.addEventListener("click", () => hideModal(compareModal));
  closeDetails && closeDetails.addEventListener("click", () => hideModal(detailsModal));

  btnSaveSelected.addEventListener("click", saveSelected);
  btnClearSaved.addEventListener("click", () => {
    localStorage.removeItem("savedStartups");
    savedSet = {};
    showToast("Favoritos limpos.", "success");
    updateSavedButtonsState();
  });

  showEmptyState(true);
  updateSelectedUI();

  [compareModal, detailsModal].forEach(modal => {
    modal && modal.addEventListener('click', (e) => {
      if (e.target === modal) hideModal(modal);
    });
  });

  // ----- Functions -----
  function buildSuggestions() {
    suggestionsEl.innerHTML = "";
    sampleSuggestions.forEach(s => {
      const b = document.createElement("button");
      b.className = "chip";
      b.type = "button";
      b.textContent = s;
      b.addEventListener("click", () => {
        vcInput.value = s;
        vcInput.focus();
      });
      suggestionsEl.appendChild(b);
    });
  }

  async function performSearch(vcList) {
    showEmptyState(false);
    showLoading(true);
    
    try {
      const res = await fetch("/pesquisar", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({vc_list: vcList})
      });
      
      const json = await res.json();
      
      if (!res.ok) {
        showToast(json.erro || "Erro na busca", "error");
        showEmptyState(true);
        return;
      }

      const payload = json.resultado;
      let arr = normalizeSearchResults(payload);

      currentResults = arr.map(normalizeStartup);
      currentVCs = vcList;
      
      applyFilters();
      showToast(`${currentResults.length} startups encontradas!`, "success");
      
    } catch (err) {
      console.error("Search error:", err);
      showToast("Erro de conexão. Tente novamente.", "error");
      showEmptyState(true);
    } finally {
      showLoading(false);
    }
  }

  async function performDeepSearch(vcList) {
    showEmptyState(false);
    showLoadingDeep(true);
    
    try {
      const res = await fetch("/pesquisar-profundo", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({vc_list: vcList})
      });
      
      const json = await res.json();
      
      if (!res.ok) {
        showToast(json.erro || "Erro na pesquisa profunda", "error");
        showLoadingDeep(false);
        showEmptyState(true);
        return;
      }

      const payload = json.resultado;
      const metadados = json.metadados || {};
      
      let arr = Array.isArray(payload) ? payload : [payload];
      currentResults = arr.map(normalizeStartup);
      currentVCs = vcList;
      
      applyFilters();
      showDeepResearchInfo(metadados);
      
      const msg = `✨ Pesquisa Profunda: ${currentResults.length} startups de ${metadados.total_fontes || 'várias'} fontes`;
      showToast(msg, "success");
      
    } catch (err) {
      console.error("Deep search error:", err);
      showToast("Erro na pesquisa profunda. Tente novamente.", "error");
      showEmptyState(true);
    } finally {
      showLoadingDeep(false);
    }
  }

  function showLoadingDeep(show) {
    let overlay = document.getElementById("__loading_deep_overlay");
    
    if (show) {
      if (!overlay) {
        overlay = document.createElement("div");
        overlay.id = "__loading_deep_overlay";
        overlay.style.cssText = `
          position: fixed; inset: 0;
          background: rgba(15, 98, 254, 0.05);
          backdrop-filter: blur(8px);
          z-index: 90;
          display: flex;
          align-items: center;
          justify-content: center;
        `;
        
        overlay.innerHTML = `
          <div style="
            background: white;
            padding: 32px 40px;
            border-radius: 16px;
            box-shadow: 0 12px 32px rgba(0,0,0,0.15);
            max-width: 400px;
            text-align: center;
          ">
            <div style="font-size: 48px; margin-bottom: 16px;">🔍</div>
            <h3 style="margin: 0 0 12px; color: #111827; font-size: 20px;">
              Pesquisa Profunda em Andamento
            </h3>
            <p style="margin: 0 0 20px; color: #6b7280; font-size: 14px;">
              Analisando múltiplas fontes para resultados mais precisos...
            </p>
            
            <div style="
              background: #f3f4f6;
              border-radius: 8px;
              height: 8px;
              overflow: hidden;
              margin-bottom: 12px;
            ">
              <div style="
                background: linear-gradient(90deg, #0f62fe, #00bfa6);
                height: 100%;
                width: 0%;
                animation: progressAnimation 60s ease-in-out forwards;
              "></div>
            </div>
            
            <div id="deepSearchStatus" style="
              font-size: 13px;
              color: #9ca3af;
              font-weight: 600;
            ">
              Camada 1: Pesquisa inicial...
            </div>
          </div>
          
          <style>
            @keyframes progressAnimation {
              0% { width: 0%; }
              30% { width: 40%; }
              60% { width: 70%; }
              90% { width: 95%; }
              100% { width: 100%; }
            }
          </style>
        `;
        
        document.body.appendChild(overlay);
        simulateDeepSearchProgress();
      }
    } else {
      if (overlay) overlay.remove();
    }
  }

  function simulateDeepSearchProgress() {
    const statusEl = document.getElementById("deepSearchStatus");
    if (!statusEl) return;
    
    const steps = [
      { time: 0, text: "📊 Camada 1: Pesquisa inicial..." },
      { time: 15000, text: "🤔 Analisando fontes iniciais..." },
      { time: 25000, text: "🔎 Gerando pergunta de aprofundamento..." },
      { time: 30000, text: "📊 Camada 2: Pesquisa detalhada..." },
      { time: 45000, text: "🧠 Sintetizando informações..." },
      { time: 55000, text: "✨ Finalizando análise..." }
    ];
    
    steps.forEach(step => {
      setTimeout(() => {
        if (statusEl) statusEl.textContent = step.text;
      }, step.time);
    });
  }

  function showDeepResearchInfo(metadados) {
    const info = `
      <div style="
        background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
        border: 2px solid #0ea5e9;
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
      ">
        <h4 style="margin: 0 0 12px; color: #0369a1; display: flex; align-items: center; gap: 8px;">
          <span style="font-size: 24px;">✨</span>
          Pesquisa Profunda Concluída
        </h4>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin-top: 16px;">
          <div style="background: white; padding: 12px; border-radius: 8px;">
            <div style="font-size: 12px; color: #64748b; font-weight: 600;">FONTES CONSULTADAS</div>
            <div style="font-size: 24px; color: #0369a1; font-weight: 700;">${metadados.total_fontes || '—'}</div>
          </div>
          
          <div style="background: white; padding: 12px; border-radius: 8px;">
            <div style="font-size: 12px; color: #64748b; font-weight: 600;">STARTUPS ENCONTRADAS</div>
            <div style="font-size: 24px; color: #16a34a; font-weight: 700;">${metadados.total_startups || '—'}</div>
          </div>
          
          <div style="background: white; padding: 12px; border-radius: 8px;">
            <div style="font-size: 12px; color: #64748b; font-weight: 600;">VCS PESQUISADAS</div>
            <div style="font-size: 24px; color: #7c3aed; font-weight: 700;">${metadados.vcs_pesquisadas?.length || '—'}</div>
          </div>
        </div>
        
        ${metadados.query_aprofundamento ? `
          <div style="margin-top: 16px; padding: 12px; background: white; border-radius: 8px; border-left: 3px solid #0ea5e9;">
            <div style="font-size: 12px; color: #64748b; font-weight: 600; margin-bottom: 4px;">APROFUNDAMENTO REALIZADO</div>
            <div style="font-size: 13px; color: #334155;">${escapeHtml(metadados.query_aprofundamento)}</div>
          </div>
        ` : ''}
      </div>
    `;
    
    const container = document.getElementById('deepSearchInfoContainer');
    if (container) {
      container.innerHTML = info;
    }
  }

  function normalizeSearchResults(payload) {
    if (Array.isArray(payload)) return payload;
    if (payload && payload.result && Array.isArray(payload.result)) return payload.result;
    if (payload && typeof payload === "object") {
      const values = Object.values(payload);
      const arrayValues = values.filter(v => Array.isArray(v));
      if (arrayValues.length > 0) return arrayValues.flat();
      return [payload];
    }
    return [];
  }

  function normalizeStartup(raw) {
    const r = raw || {};
    const id = r.id || generateId(r.nome || r.name || 'unknown');
    
    return {
      id,
      nome: r.nome || r.name || r.company || "Nome não informado",
      site: r.site || r.url || r.website || "",
      setor: r.setor || r.sector || r.industry || "Não informado",
      ano_fundacao: r.ano_fundacao || r.year || r.founded_year || r.founded || null,
      valor_investimento: r.valor_investimento || r.investment_value || r.valor || r.funding || "Não informado",
      rodada: r.rodada || r.round || r.funding_round || "Não informada",
      data_investimento: r.data_investimento || r.investment_date || r.date || "Não informada",
      vc_investidor: r.vc_investidor || r.vc || r.investor || "Não informado",
      descricao_breve: r.descricao_breve || r.description || r.bio || r.summary || "",
      linkedin_fundador: r.linkedin_fundador || r.linkedin || r.founder_linkedin || "",
      raw: r
    };
  }

  function generateId(name) {
    const cleanName = String(name).slice(0, 20).replace(/[^a-zA-Z0-9]/g, '');
    const randomSuffix = Math.random().toString(36).slice(2, 8);
    return `${cleanName}-${randomSuffix}`;
  }

  function applyFilters() {
    const yFrom = Number(filterYearFrom.value) || null;
    const yTo = Number(filterYearTo.value) || null;
    const sector = (filterSector.value || "").trim().toLowerCase();
    const minVal = parseMaybeHumanNumber(filterMinValue.value);
    const maxVal = parseMaybeHumanNumber(filterMaxValue.value);

    filteredResults = currentResults.filter(s => {
      if (yFrom && s.ano_fundacao) {
        const year = Number(s.ano_fundacao);
        if (year && year < yFrom) return false;
      }
      if (yTo && s.ano_fundacao) {
        const year = Number(s.ano_fundacao);
        if (year && year > yTo) return false;
      }
      
      if (sector && !s.setor.toLowerCase().includes(sector)) return false;
      
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
    
    list.forEach((item, index) => {
      const card = createCard(item);
      card.style.animationDelay = `${index * 50}ms`;
      card.classList.add('fade-in');
      resultsEl.appendChild(card);
    });

    updateStats(list);
    drawSectorChart(buildSectorCounts(list));
    updateSelectedUI();
    updateSavedButtonsState();
  }

  function createCard(item) {
    const card = document.createElement("article");
    card.className = "startup-card";
    card.dataset.id = item.id;

    card.innerHTML = `
      <div class="startup-top">
        <div class="logo-wrap">${getInitials(item.nome)}</div>
        <div class="startup-body">
          <h3 class="startup-title">${escapeHtml(item.nome)}</h3>
          <p class="startup-desc">${escapeHtml(item.descricao_breve || 'Sem descrição disponível.')}</p>
          <div class="tags">
            ${createTags(item)}
          </div>
        </div>
      </div>
      
      <div class="meta">
        <div class="meta-row">
          <span class="meta-label">Valor do Investimento</span>
          <span class="meta-value investment-value">${formatInvestment(item.valor_investimento)}</span>
        </div>
        <div class="meta-row">
          <span class="meta-label">Rodada</span>
          <span class="meta-value">${escapeHtml(item.rodada)}</span>
        </div>
        <div class="meta-row">
          <span class="meta-label">Fundação</span>
          <span class="meta-value">${escapeHtml(item.ano_fundacao || '—')}</span>
        </div>
        <div class="meta-row">
          <span class="meta-label">Investimento</span>
          <span class="meta-value">${escapeHtml(item.data_investimento)}</span>
        </div>
        <div class="meta-row">
          <span class="meta-label">VC Investidor</span>
          <span class="meta-value">${escapeHtml(item.vc_investidor)}</span>
        </div>
      </div>

      <div class="card-actions">
        <div class="left-actions">
          <input type="checkbox" class="select-checkbox" ${selectedIds.has(item.id) ? 'checked' : ''}>
          <button class="small-btn save-btn ${savedSet[item.id] ? 'saved' : ''}">${savedSet[item.id] ? 'Salvo' : 'Salvar'}</button>
        </div>
        <div class="right-actions">
          <button class="small-btn linkedin-btn">LinkedIn</button>
          <button class="small-btn details-btn primary">Ver detalhes</button>
        </div>
      </div>

      <div class="technical-data ${toggleRaw.checked ? 'show' : ''}">
        <pre>${JSON.stringify(item.raw, null, 2)}</pre>
      </div>
    `;

    const selectCb = card.querySelector('.select-checkbox');
    const saveBtn = card.querySelector('.save-btn');
    const linkedinBtn = card.querySelector('.linkedin-btn');
    const detailsBtn = card.querySelector('.details-btn');

    selectCb.addEventListener('change', (e) => {
      if (e.target.checked) {
        selectedIds.add(item.id);
      } else {
        selectedIds.delete(item.id);
      }
      updateSelectedUI();
    });

    saveBtn.addEventListener('click', () => toggleSaveStartup(item, saveBtn));
    linkedinBtn.addEventListener('click', () => openLinkedIn(item));
    detailsBtn.addEventListener('click', () => showDetailsModal(item));

    return card;
  }

  function createTags(item) {
    const tags = [];
    if (item.setor && item.setor !== 'Não informado') {
      tags.push(`<span class="tag">${escapeHtml(item.setor)}</span>`);
    }
    if (item.rodada && item.rodada !== 'Não informada') {
      tags.push(`<span class="tag">${escapeHtml(item.rodada)}</span>`);
    }
    return tags.join('');
  }

  function getInitials(name) {
    if (!name) return "—";
    return name.split(" ")
      .slice(0, 2)
      .map(word => word[0]?.toUpperCase() || "")
      .join("");
  }

  function toggleSaveStartup(item, button) {
    if (savedSet[item.id]) {
      delete savedSet[item.id];
      button.textContent = "Salvar";
      button.classList.remove('saved');
      showToast("Removido dos favoritos", "success");
    } else {
      savedSet[item.id] = item;
      button.textContent = "Salvo";
      button.classList.add('saved');
      showToast("Salvo nos favoritos", "success");
    }
    persistSaved();
  }

  function openLinkedIn(item) {
    if (item.linkedin_fundador) {
      window.open(item.linkedin_fundador, "_blank");
    } else {
      showToast("Link do LinkedIn não disponível", "error");
    }
  }

  function showDetailsModal(item) {
    const content = document.getElementById('detailsContent') || document.createElement('div');
    content.id = 'detailsContent';
    content.innerHTML = createDetailedView(item);
    
    if (!detailsModal.querySelector('#detailsContent')) {
      detailsModal.querySelector('.modal-content').appendChild(content);
    }
    
    showModal(detailsModal);
  }

  function createDetailedView(item) {
    return `
      <div class="details-header">
        <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 16px;">
          <div class="logo-wrap" style="width: 64px; height: 64px; font-size: 24px;">
            ${getInitials(item.nome)}
          </div>
          <div>
            <h2 style="margin: 0; font-size: 28px; font-weight: 700; color: #111827;">
              ${escapeHtml(item.nome)}
            </h2>
            <p style="margin: 8px 0 0; color: var(--muted); font-size: 16px;">
              ${escapeHtml(item.descricao_breve || 'Sem descrição disponível.')}
            </p>
          </div>
        </div>
        <div class="tags">
          ${createTags(item)}
        </div>
      </div>

      <div class="details-content">
        <div class="details-section">
          <h4>📊 Informações do Investimento</h4>
          <div class="details-grid">
            <div class="detail-item">
              <div class="detail-label">Valor do Investimento</div>
              <div class="detail-value success">${formatInvestment(item.valor_investimento)}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">Rodada</div>
              <div class="detail-value">${escapeHtml(item.rodada)}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">Data do Investimento</div>
              <div class="detail-value">${escapeHtml(item.data_investimento)}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">VC Investidor</div>
              <div class="detail-value primary">${escapeHtml(item.vc_investidor)}</div>
            </div>
          </div>
        </div>

        <div class="details-section">
          <h4>🏢 Informações da Empresa</h4>
          <div class="details-grid">
            <div class="detail-item">
              <div class="detail-label">Setor</div>
              <div class="detail-value">${escapeHtml(item.setor)}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">Ano de Fundação</div>
              <div class="detail-value">${escapeHtml(item.ano_fundacao || '—')}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">Website</div>
              <div class="detail-value">
                ${item.site ? `<a href="${escapeHtml(item.site)}" target="_blank">${escapeHtml(item.site)}</a>` : '—'}
              </div>
            </div>
            <div class="detail-item">
              <div class="detail-label">LinkedIn do Fundador</div>
              <div class="detail-value">
                ${item.linkedin_fundador ? `<a href="${escapeHtml(item.linkedin_fundador)}" target="_blank">Ver perfil</a>` : '—'}
              </div>
            </div>
          </div>
        </div>

        <div class="details-section">
          <h4>🔧 Dados Técnicos</h4>
          <pre style="background: #f8fafc; padding: 16px; border-radius: 8px; font-size: 12px; overflow: auto; max-height: 300px;">${JSON.stringify(item.raw, null, 2)}</pre>
        </div>
      </div>
    `;
  }

  function updateSelectedUI() {
    selectedCountEl.textContent = selectedIds.size;
    btnCompare.disabled = selectedIds.size < 2;
    btnSaveSelected.disabled = selectedIds.size === 0;
  }

  function updateSavedButtonsState() {
    document.querySelectorAll('.save-btn').forEach(btn => {
      const card = btn.closest('.startup-card');
      const itemId = card?.dataset.id;
      if (itemId && savedSet[itemId]) {
        btn.textContent = 'Salvo';
        btn.classList.add('saved');
      } else {
        btn.textContent = 'Salvar';
        btn.classList.remove('saved');
      }
    });
  }

  function openCompareModal() {
    const items = currentResults.filter(s => selectedIds.has(s.id));
    if (items.length < 2) {
      showToast("Selecione ao menos 2 startups para comparar", "error");
      return;
    }

    compareArea.innerHTML = items.map(item => `
      <div class="compare-card">
        <h4>${escapeHtml(item.nome)}</h4>
        <p style="color: var(--muted); margin-bottom: 16px;">${escapeHtml(item.descricao_breve || '')}</p>
        <ul>
          <li><strong>Setor:</strong> ${escapeHtml(item.setor)}</li>
          <li><strong>Fundação:</strong> ${escapeHtml(item.ano_fundacao || '—')}</li>
          <li><strong>Rodada:</strong> ${escapeHtml(item.rodada)}</li>
          <li><strong>Valor:</strong> ${escapeHtml(formatInvestment(item.valor_investimento))}</li>
          <li><strong>VC:</strong> ${escapeHtml(item.vc_investidor)}</li>
          <li><strong>LinkedIn:</strong> ${item.linkedin_fundador ? `<a target="_blank" href="${escapeHtml(item.linkedin_fundador)}">Ver perfil</a>` : '—'}</li>
        </ul>
      </div>
    `).join('');

    showModal(compareModal);
  }

  function saveSelected() {
    const items = currentResults.filter(s => selectedIds.has(s.id));
    items.forEach(item => savedSet[item.id] = item);
    persistSaved();
    showToast(`${items.length} startup(s) salvas nos favoritos`, "success");
    updateSavedButtonsState();
  }

  function toggleHistoryPanel() {
    if (historyPanel.classList.contains('hidden')) {
      showPanel(historyPanel);
      loadHistory();
    } else {
      hidePanel(historyPanel);
    }
  }

  async function loadHistory() {
    historyList.innerHTML = "<div style='padding: 20px; color: var(--muted); text-align: center;'>Carregando histórico...</div>";
    
    try {
      const res = await fetch("/historico");
      const json = await res.json();
      
      if (!Array.isArray(json) || json.length === 0) {
        historyList.innerHTML = "<div style='padding: 20px; color: var(--muted); text-align: center;'>Nenhuma pesquisa no histórico.</div>";
        return;
      }

      historyList.innerHTML = json.map(item => {
        const tipo = item.tipo_pesquisa || 'normal';
        const badge = tipo === 'profunda' ? '<span style="background: linear-gradient(135deg, #0f62fe, #00bfa6); color: white; padding: 2px 6px; border-radius: 8px; font-size: 10px; font-weight: 700; margin-left: 8px;">✨ DEEP</span>' : '';
        
        return `
          <div class="history-item">
            <div>
              <div style="font-weight: 700; color: #374151;">
                ${escapeHtml(item.vc_list)}
                ${badge}
              </div>
              <div style="font-size: 13px; color: var(--muted);">
                ${Array.isArray(item.resultado) ? item.resultado.length : 0} startups encontradas
              </div>
            </div>
            <button class="btn ghost" onclick="loadHistoryItem(${item.id})">Carregar</button>
          </div>
        `;
      }).join('');
      
    } catch (err) {
      console.error("History loading error:", err);
      historyList.innerHTML = "<div style='padding: 20px; color: var(--muted); text-align: center;'>Erro ao carregar histórico.</div>";
    }
  }

  window.loadHistoryItem = async (id) => {
    try {
      const res = await fetch("/historico");
      const json = await res.json();
      const item = json.find(h => h.id === id);
      
      if (!item) return;
      
      const arr = Array.isArray(item.resultado) ? item.resultado : [item.resultado];
      currentResults = arr.map(normalizeStartup);
      currentVCs = item.vc_list.split(',').map(s => s.trim());
      
      applyFilters();
      hidePanel(historyPanel);
      showToast("Histórico carregado com sucesso", "success");
      
    } catch (err) {
      console.error("Error loading history item:", err);
      showToast("Erro ao carregar item do histórico", "error");
    }
  };

  function updateStats(list) {
    statTotalStartups.textContent = list.length;
    statTotalVCs.textContent = currentVCs.length || "—";
    
    const total = list.reduce((acc, s) => {
      const n = parseMaybeHumanNumber(String(s.valor_investimento || 0));
      return acc + (n || 0);
    }, 0);
    
    statTotalValue.textContent = total ? formatCurrency(total) : "—";
  }

  function buildSectorCounts(list) {
    const counts = {};
    list.forEach(s => {
      const sector = s.setor === 'Não informado' ? 'Outros' : s.setor;
      counts[sector] = (counts[sector] || 0) + 1;
    });
    return counts;
  }

  function drawSectorChart(sectorCounts) {
    const ctx = sectorChart.getContext("2d");
    const canvas = sectorChart;
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    const entries = Object.entries(sectorCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6);
      
    if (!entries.length) {
      ctx.fillStyle = "var(--muted)";
      ctx.font = "14px Inter";
      ctx.textAlign = "center";
      ctx.fillText("Sem dados para exibir", canvas.width / 2, canvas.height / 2);
      return;
    }
    
    const padding = 20;
    const chartWidth = canvas.width - padding * 2;
    const chartHeight = canvas.height - padding * 2;
    const maxValue = Math.max(...entries.map(e => e[1]));
    const barHeight = Math.floor(chartHeight / entries.length * 0.7);
    const barGap = Math.floor(chartHeight / entries.length * 0.3);
    
    const colors = ['#0f62fe', '#00bfa6', '#8b5cf6', '#f59e0b', '#ef4444', '#10b981'];
    
    entries.forEach(([label, value], index) => {
      const y = padding + index * (barHeight + barGap);
      const barWidth = Math.max(4, (value / maxValue) * (chartWidth * 0.65));
      
      ctx.fillStyle = colors[index % colors.length];
      ctx.fillRect(padding, y, barWidth, barHeight);
      
      ctx.fillStyle = '#374151';
      ctx.font = 'bold 12px Inter';
      ctx.textAlign = 'left';
      ctx.fillText(`${label} (${value})`, padding + barWidth + 10, y + barHeight / 1.5);
    });
  }

  function buildCSV(rows) {
    const header = [
      "nome", "site", "setor", "ano_fundacao", "valor_investimento", 
      "rodada", "data_investimento", "vc_investidor", "descricao_breve", "linkedin_fundador"
    ];
    
    const lines = [header.join(",")];
    
    rows.forEach(row => {
      const values = header.map(key => {
        const value = row[key] ?? "";
        return `"${String(value).replace(/"/g, '""')}"`;
      });
      lines.push(values.join(","));
    });
    
    return lines.join("\n");
  }

  function downloadCSV(rows) {
    const csv = buildCSV(rows);
    const blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const date = new Date().toISOString().slice(0, 10);
    
    link.href = url;
    link.download = `startups_export_${date}.csv`;
    link.click();
    
    URL.revokeObjectURL(url);
    showToast("CSV exportado com sucesso", "success");
  }

  function showLoading(show) {
    let overlay = document.getElementById("__loading_overlay");
    
    if (show) {
      if (!overlay) {
        overlay = document.createElement("div");
        overlay.id = "__loading_overlay";
        overlay.style.cssText = `
          position: fixed; inset: 0;
          background: rgba(255,255,255,0.8);
          backdrop-filter: blur(4px);
          z-index: 90;
          display: flex;
          align-items: center;
          justify-content: center;
        `;
        overlay.innerHTML = `
          <div style="
            background: white;
            padding: 24px 32px;
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.12);
            font-weight: 700;
            font-size: 16px;
            color: #374151;
          ">
            🔍 Buscando startups...
          </div>
        `;
        document.body.appendChild(overlay);
      }
    } else {
      if (overlay) overlay.remove();
    }
  }

  function showEmptyState(show) {
    emptyState.style.display = show ? "block" : "none";
    resultsEl.style.display = show ? "none" : "grid";
  }

  function showToast(message, type = "success") {
    toast.textContent = message;
    toast.className = `toast ${type}`;
    toast.classList.remove("hidden");
    
    if (toast._timeout) clearTimeout(toast._timeout);
    
    toast._timeout = setTimeout(() => {
      toast.classList.add("hidden");
    }, 3000);
  }

  function showModal(modal) {
    modal.classList.remove("hidden");
    document.body.style.overflow = "hidden";
  }

  function hideModal(modal) {
    modal.classList.add("hidden");
    document.body.style.overflow = "";
  }

  function showPanel(panel) {
    panel.classList.remove("hidden");
  }

  function hidePanel(panel) {
    panel.classList.add("hidden");
  }

  function formatInvestment(value) {
    if (!value || value === "Não informado") return "—";
    if (typeof value === "number") return formatCurrency(value);
    
    const str = String(value);
    if (/[$€£R]/.test(str)) return str;
    
    const num = parseMaybeHumanNumber(str);
    if (num !== null) return formatCurrency(num);
    
    return str;
  }

  function parseMaybeHumanNumber(str) {
    if (!str) return null;
    
    const cleaned = String(str)
      .replace(/\s+/g, '')
      .replace(/\./g, '')
      .replace(/,/g, '.');
    
    const match = cleaned.match(/([0-9]+(?:\.[0-9]+)?)([kKmMbB])?/);
    
    if (!match) {
      const digits = cleaned.replace(/[^\d]/g, '');
      return digits ? Number(digits) : null;
    }
    
    let num = Number(match[1]);
    const suffix = match[2] ? match[2].toUpperCase() : null;
    
    if (suffix === "K") num *= 1_000;
    if (suffix === "M") num *= 1_000_000;
    if (suffix === "B") num *= 1_000_000_000;
    
    return Math.round(num);
  }

  function formatCurrency(num) {
    try {
      return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL',
        maximumFractionDigits: 0
      }).format(num);
    } catch (e) {
      return `R$ ${num.toLocaleString('pt-BR')}`;
    }
  }

  function escapeHtml(str) {
    const text = String(str || "");
    const map = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;'
    };
    return text.replace(/[&<>"']/g, c => map[c]);
  }

  function persistSaved() {
    try {
      localStorage.setItem("savedStartups", JSON.stringify(savedSet));
    } catch (e) {
      console.error("Error saving to localStorage:", e);
      showToast("Erro ao salvar favoritos", "error");
    }
  }

  function loadSaved() {
    try {
      const saved = localStorage.getItem("savedStartups");
      return saved ? JSON.parse(saved) : {};
    } catch (e) {
      console.error("Error loading from localStorage:", e);
      return {};
    }
  }

  function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      if (!compareModal.classList.contains('hidden')) hideModal(compareModal);
      if (!detailsModal.classList.contains('hidden')) hideModal(detailsModal);
      if (!historyPanel.classList.contains('hidden')) hidePanel(historyPanel);
    }
    
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      vcInput.focus();
      vcInput.select();
    }
  });

  window.addEventListener('beforeprint', () => {
    document.querySelectorAll('.technical-data').forEach(el => {
      el.style.display = 'none';
    });
    document.querySelector('.bottom-bar')?.style.setProperty('display', 'none');
  });

  window.addEventListener('afterprint', () => {
    document.querySelectorAll('.technical-data').forEach(el => {
      if (toggleRaw.checked) {
        el.style.display = 'block';
      }
    });
    document.querySelector('.bottom-bar')?.style.setProperty('display', 'flex');
  });

})();