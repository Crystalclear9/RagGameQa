const state = {
  selectedRating: null,
  lastQueryLogId: null,
  overview: null,
  providerCatalog: {},
};

const refs = {
  heroTitle: document.getElementById("heroTitle"),
  heroSubtitle: document.getElementById("heroSubtitle"),
  heroChips: document.getElementById("heroChips"),
  projectMeta: document.getElementById("projectMeta"),
  fundingChip: document.getElementById("fundingChip"),
  fundingBar: document.getElementById("fundingBar"),
  fundingSummary: document.getElementById("fundingSummary"),
  fundingDetails: document.getElementById("fundingDetails"),
  databaseBadge: document.getElementById("databaseBadge"),
  runtimeCards: document.getElementById("runtimeCards"),
  timelineList: document.getElementById("timelineList"),
  progressList: document.getElementById("progressList"),
  resultsList: document.getElementById("resultsList"),
  issuesList: document.getElementById("issuesList"),
  planList: document.getElementById("planList"),
  innovationList: document.getElementById("innovationList"),
  teamGrid: document.getElementById("teamGrid"),
  proposalHighlights: document.getElementById("proposalHighlights"),
  coverageChip: document.getElementById("coverageChip"),
  coverageGrid: document.getElementById("coverageGrid"),
  demoScenarioButtons: document.getElementById("demoScenarioButtons"),
  batchDemoResults: document.getElementById("batchDemoResults"),
  runBatchDemo: document.getElementById("runBatchDemo"),
  providerForm: document.getElementById("providerForm"),
  providerSelect: document.getElementById("providerSelect"),
  providerModel: document.getElementById("providerModel"),
  providerApiKey: document.getElementById("providerApiKey"),
  storageMode: document.getElementById("storageMode"),
  clearEnvOnRemove: document.getElementById("clearEnvOnRemove"),
  toggleApiKeyVisibility: document.getElementById("toggleApiKeyVisibility"),
  clearProviderConfig: document.getElementById("clearProviderConfig"),
  testProviderConfig: document.getElementById("testProviderConfig"),
  providerStatusBadge: document.getElementById("providerStatusBadge"),
  providerSnapshot: document.getElementById("providerSnapshot"),
  providerMessage: document.getElementById("providerMessage"),
  providerHint: document.getElementById("providerHint"),
  modelSuggestionList: document.getElementById("modelSuggestionList"),
  qaForm: document.getElementById("qaForm"),
  gameId: document.getElementById("gameId"),
  userType: document.getElementById("userType"),
  difficultyLevel: document.getElementById("difficultyLevel"),
  topK: document.getElementById("topK"),
  assistiveGuide: document.getElementById("assistiveGuide"),
  questionInput: document.getElementById("questionInput"),
  answerBox: document.getElementById("answerBox"),
  confidenceChip: document.getElementById("confidenceChip"),
  metaRow: document.getElementById("metaRow"),
  sourcesList: document.getElementById("sourcesList"),
  assistiveSteps: document.getElementById("assistiveSteps"),
  statusBadge: document.getElementById("statusBadge"),
  ratingRow: document.getElementById("ratingRow"),
  feedbackComment: document.getElementById("feedbackComment"),
  submitFeedback: document.getElementById("submitFeedback"),
  feedbackMessage: document.getElementById("feedbackMessage"),
  refreshDashboard: document.getElementById("refreshDashboard"),
  statsGrid: document.getElementById("statsGrid"),
  trendBars: document.getElementById("trendBars"),
  topQuestions: document.getElementById("topQuestions"),
  priorityList: document.getElementById("priorityList"),
};

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || payload.message || `请求失败：${response.status}`);
  }

  return response.json();
}

function escapeHtml(text) {
  return String(text ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function setStatus(text, busy = false) {
  refs.statusBadge.textContent = text;
  refs.statusBadge.style.color = busy ? "#f1a65b" : "";
}

function renderList(container, items = [], emptyText = "暂无数据") {
  container.innerHTML = items.length
    ? items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")
    : `<li>${escapeHtml(emptyText)}</li>`;
}

function renderHero(overview) {
  const info = overview.project_info || {};
  const runtime = overview.runtime_metrics || {};
  refs.heroTitle.textContent = info.project_name || "项目展示台";
  refs.heroSubtitle.textContent = `${info.project_number || ""} · ${info.college || ""} · 负责人 ${info.leader || ""}。当前页面整合了中期检查、申报书亮点、系统演示与实时数据，可用于答辩展示与功能演示。`;
  refs.heroChips.innerHTML = [
    `项目编号 ${info.project_number || "--"}`,
    `负责人 ${info.leader || "--"}`,
    `指导老师 ${info.advisor || "--"}`,
    `Provider ${runtime.ai_provider || "mock"}`,
    `总查询 ${runtime.total_queries ?? 0}`,
    `总反馈 ${runtime.total_feedback ?? 0}`,
  ].map((item) => `<span class="chip">${escapeHtml(item)}</span>`).join("");
}

function renderProjectMeta(overview) {
  const info = overview.project_info || {};
  const duration = info.duration || {};
  const entries = [
    ["所属学科", info.discipline || "--"],
    ["实施时间", `${duration.start || "--"} 至 ${duration.end || "--"}`],
    ["填表时间", duration.midterm_fill_date || "--"],
    ["联系电话", info.phone || "--"],
  ];
  refs.projectMeta.innerHTML = entries
    .map(
      ([label, value]) => `
        <div class="detail-item">
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(value)}</strong>
        </div>
      `,
    )
    .join("");
}

function renderFunding(overview) {
  const funding = overview.funding || {};
  const received = Number(funding.received || 0);
  const used = Number(funding.used || 0);
  const remaining = Number(funding.remaining || Math.max(received - used, 0));
  const percent = received ? Math.min((used / received) * 100, 100) : 0;
  refs.fundingChip.textContent = `已使用 ${percent.toFixed(1)}%`;
  refs.fundingBar.style.width = `${percent}%`;
  refs.fundingSummary.textContent = `已获资助 ${received} 元，已使用 ${used} 元，剩余 ${remaining} 元。`;
  refs.fundingDetails.innerHTML = (funding.details || [])
    .map((item) => `<li>${escapeHtml(item.item)}：${escapeHtml(item.amount)} 元</li>`)
    .join("");
}

function renderRuntime(overview) {
  const runtime = overview.runtime_metrics || {};
  const database = runtime.database || {};
  refs.databaseBadge.textContent = database.using_fallback ? "SQLite 回退模式" : "数据库已连接";
  refs.databaseBadge.className = `status-badge ${database.using_fallback ? "alert-chip" : "success-chip"}`;

  const entries = [
    ["总查询量", runtime.total_queries ?? 0, "运行期累计"],
    ["总反馈量", runtime.total_feedback ?? 0, "闭环数据"],
    ["平均置信度", runtime.average_confidence ?? 0, "问答输出"],
    ["平均耗时", `${runtime.average_processing_time ?? 0}s`, "接口处理"],
    [
      "当前模型",
      runtime.ai_provider ?? "mock",
      runtime.live_llm_enabled ? "真实外部模型已启用" : "当前为本地演示或回退模式",
    ],
  ];
  refs.runtimeCards.innerHTML = entries
    .map(
      ([label, value, desc]) => `
        <div class="mini-stat">
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(value)}</strong>
          <p>${escapeHtml(desc)}</p>
        </div>
      `,
    )
    .join("");
}

function renderTimeline(overview) {
  refs.timelineList.innerHTML = (overview.timeline || [])
    .map(
      (item) => `
        <div class="timeline-item">
          <span>${escapeHtml(item.date)}</span>
          <strong>${escapeHtml(item.title)}</strong>
          <p>${escapeHtml(item.description)}</p>
        </div>
      `,
    )
    .join("");
}

function renderTeam(overview) {
  refs.teamGrid.innerHTML = (overview.team || [])
    .map(
      (member) => `
        <article class="member-card">
          <span>${escapeHtml(member.role)}</span>
          <strong>${escapeHtml(member.name)}</strong>
          <p>${escapeHtml(member.student_id)} · ${escapeHtml(member.focus)}</p>
        </article>
      `,
    )
    .join("");
}

function renderProposalHighlights(overview) {
  refs.proposalHighlights.innerHTML = (overview.proposal_highlights || [])
    .map(
      (section) => `
        <article class="highlight-card">
          <h3>${escapeHtml(section.title)}</h3>
          <ul>
            ${(section.items || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
          </ul>
        </article>
      `,
    )
    .join("");
}

function renderCoverage(overview) {
  const coverage = overview.knowledge_coverage || {};
  refs.coverageChip.textContent = `${coverage.total_documents || 0} 篇示例文档`;
  refs.coverageGrid.innerHTML = (coverage.games || [])
    .map(
      (game) => `
        <article class="coverage-card">
          <span>${escapeHtml(game.game_id)}</span>
          <strong>${escapeHtml(game.game_name)}</strong>
          <p>版本 ${escapeHtml(game.version)} · 文档 ${escapeHtml(game.document_count)}</p>
        </article>
      `,
    )
    .join("");
}

function applyScenarioToForm(scenario) {
  refs.gameId.value = scenario.game_id;
  refs.questionInput.value = scenario.question;
  refs.assistiveGuide.checked = true;
  window.scrollTo({ top: refs.qaForm.offsetTop - 30, behavior: "smooth" });
}

function renderDemoScenarios(overview) {
  const scenarios = overview.demo_questions || [];
  refs.demoScenarioButtons.innerHTML = scenarios.length
    ? scenarios
        .map(
          (scenario, index) => `
            <button class="scenario-button" type="button" data-index="${index}">
              ${escapeHtml(scenario.game_id.toUpperCase())} · ${escapeHtml(scenario.question)}
            </button>
          `,
        )
        .join("")
    : `<p class="subtle">暂无预设示例。</p>`;

  refs.demoScenarioButtons.querySelectorAll(".scenario-button").forEach((button) => {
    button.addEventListener("click", () => {
      const scenario = scenarios[Number(button.dataset.index)];
      applyScenarioToForm(scenario);
    });
  });
}

function renderMeta(metadata = {}) {
  const entries = [
    ["耗时", metadata.processing_time ? `${metadata.processing_time}s` : "--"],
    ["检索文档", metadata.retrieved ?? "--"],
    ["日志 ID", metadata.query_log_id ?? "--"],
    ["Provider", metadata.ai_provider ?? "--"],
  ];
  refs.metaRow.innerHTML = entries
    .map(([label, value]) => `<span class="meta-pill">${escapeHtml(label)} ${escapeHtml(value)}</span>`)
    .join("");
}

function renderSources(sources = []) {
  refs.sourcesList.innerHTML = sources.length
    ? sources.map((item) => `<li>${escapeHtml(item.source)}</li>`).join("")
    : "<li>暂无来源</li>";
}

function renderAssistiveGuide(steps = []) {
  refs.assistiveSteps.innerHTML = steps.length
    ? steps
        .map((step, index) => {
          const description = step.description || "请按提示操作";
          const cue = step.visual_cue || "";
          return `<li><span class="step-badge">${index + 1}</span>${escapeHtml(cue)} ${escapeHtml(description)}</li>`;
        })
        .join("")
    : "<li>本次未返回分步引导。</li>";
}

function renderStats(stats) {
  refs.statsGrid.innerHTML = `
    <div class="stat-card">
      <span>近 7 天查询</span>
      <strong>${escapeHtml(stats.total_queries)}</strong>
    </div>
    <div class="stat-card">
      <span>平均置信度</span>
      <strong>${Number(stats.avg_confidence || 0).toFixed(3)}</strong>
    </div>
    <div class="stat-card">
      <span>平均耗时</span>
      <strong>${Number(stats.avg_processing_time || 0).toFixed(3)}s</strong>
    </div>
    <div class="stat-card">
      <span>累计反馈</span>
      <strong>${escapeHtml(stats.total_feedback)}</strong>
    </div>
  `;
}

function renderTrends(days = []) {
  if (!days.length) {
    refs.trendBars.innerHTML = "<p class='subtle'>暂无趋势数据</p>";
    return;
  }

  const maxCount = Math.max(...days.map((item) => item.count), 1);
  refs.trendBars.innerHTML = days
    .map((item) => {
      const height = Math.max((item.count / maxCount) * 140, item.count ? 12 : 8);
      const label = item.date.slice(5);
      return `
        <div class="trend-bar">
          <div class="trend-fill" style="height:${height}px"></div>
          <span class="trend-label">${escapeHtml(label)}<br>${escapeHtml(item.count)}</span>
        </div>
      `;
    })
    .join("");
}

function renderTopQuestions(questions = []) {
  refs.topQuestions.innerHTML = questions.length
    ? questions.map((question) => `<li>${escapeHtml(question)}</li>`).join("")
    : "<li>暂无数据</li>";
}

function renderPriority(items = []) {
  refs.priorityList.innerHTML = items.length
    ? items
        .map(
          (item) =>
            `<li><strong>${escapeHtml(item.label)}</strong><span class="priority-score">${escapeHtml(item.score)}</span><br>${escapeHtml(item.title)}</li>`,
        )
        .join("")
    : "<li>暂无反馈数据</li>";
}

function renderBatchDemoResults(results = [], loading = false) {
  if (loading) {
    refs.batchDemoResults.innerHTML = "<p class='subtle'>正在运行批量演示，请稍候...</p>";
    return;
  }

  if (!results.length) {
    refs.batchDemoResults.innerHTML = "<p class='subtle'>运行批量演示后，这里会显示各问题的回答结果。</p>";
    return;
  }

  refs.batchDemoResults.innerHTML = results
    .map(
      (item) => `
        <article class="batch-card">
          <span class="chip">${escapeHtml(item.game_id.toUpperCase())}</span>
          <p><strong>问题：</strong>${escapeHtml(item.question)}</p>
          <p><strong>回答：</strong>${escapeHtml(item.answer)}</p>
          <p><strong>置信度：</strong>${Number(item.confidence || 0).toFixed(3)} · <strong>耗时：</strong>${escapeHtml(item.processing_time)}s</p>
        </article>
      `,
    )
    .join("");
}

function getProviderCatalog(provider) {
  return state.providerCatalog[provider] || {
    recommended: "",
    latest_verified_at: "",
    source_url: "",
    models: [],
  };
}

function renderModelSuggestions(provider) {
  const catalog = getProviderCatalog(provider);
  refs.modelSuggestionList.innerHTML = (catalog.models || [])
    .map((item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.label || item.id)}</option>`)
    .join("");
  const sourceLink = catalog.source_url
    ? `<a href="${escapeHtml(catalog.source_url)}" target="_blank" rel="noreferrer">官方模型文档</a>`
    : "";
  refs.providerHint.innerHTML = provider === "mock"
    ? "mock 模式不需要 API Key，适合本地答辩演示和接口联调。"
    : `推荐模型：<strong>${escapeHtml(catalog.recommended || "")}</strong>。最新校验日期：${escapeHtml(catalog.latest_verified_at || "--")}。${sourceLink}`;
}

function storageModeLabel(mode) {
  if (mode === "secure_local") {
    return "本机安全存储";
  }
  if (mode === "env") {
    return ".env 调试模式";
  }
  return "当前会话";
}

function renderProviderSnapshot(snapshot) {
  state.providerCatalog = snapshot.provider_catalog || {};
  refs.providerStatusBadge.textContent = `${snapshot.provider} · ${snapshot.live_llm_enabled ? "已启用" : "待配置"} · ${storageModeLabel(snapshot.storage_mode)}`;
  refs.providerSelect.value = snapshot.provider || "mock";
  refs.providerModel.value = snapshot.model || "";
  refs.providerApiKey.value = "";
  refs.storageMode.value = snapshot.secure_storage_supported ? snapshot.storage_mode || "session" : "session";
  renderModelSuggestions(refs.providerSelect.value);

  const secureHint = snapshot.secure_storage_supported ? "可用" : "当前系统不支持";
  refs.providerSnapshot.innerHTML = [
    `Provider ${snapshot.provider || "mock"}`,
    `模型 ${snapshot.model || "--"}`,
    snapshot.api_key_configured ? `已配置密钥 ${snapshot.api_key_masked || ""}` : "未配置密钥",
    `保存方式 ${storageModeLabel(snapshot.storage_mode)}`,
    `安全存储 ${secureHint}`,
  ].map((item) => `<span class="meta-pill">${escapeHtml(item)}</span>`).join("");
}

async function loadOverview() {
  const overview = await fetchJson("/api/v1/project/overview");
  state.overview = overview;
  renderHero(overview);
  renderProjectMeta(overview);
  renderFunding(overview);
  renderRuntime(overview);
  renderTimeline(overview);
  renderList(refs.progressList, overview.research_progress, "暂无研究进展");
  renderList(refs.resultsList, overview.phased_results, "暂无阶段成果");
  renderList(refs.issuesList, overview.current_issues, "暂无问题记录");
  renderList(refs.planList, overview.next_plan, "暂无后续计划");
  renderList(refs.innovationList, overview.innovations, "暂无创新点描述");
  renderTeam(overview);
  renderProposalHighlights(overview);
  renderCoverage(overview);
  renderDemoScenarios(overview);
}

async function loadProviderConfig() {
  const snapshot = await fetchJson("/api/v1/runtime/provider-config");
  renderProviderSnapshot(snapshot);
  return snapshot;
}

async function refreshDashboard() {
  const gameId = refs.gameId.value;
  try {
    const [stats, priorities] = await Promise.all([
      fetchJson(`/api/v1/analytics/query-stats?game_id=${encodeURIComponent(gameId)}&days=7`),
      fetchJson(`/api/v1/analytics/priority-report?game_id=${encodeURIComponent(gameId)}`),
    ]);

    renderStats(stats);
    renderTrends(stats.recent_days || []);
    renderTopQuestions(stats.top_questions || []);
    renderPriority(priorities || []);
  } catch (error) {
    refs.feedbackMessage.textContent = `看板刷新失败：${error.message}`;
  }
}

async function syncProjectView() {
  await Promise.all([loadOverview(), refreshDashboard(), loadProviderConfig()]);
}

async function submitQuestion(event) {
  event.preventDefault();
  const question = refs.questionInput.value.trim();
  if (!question) {
    refs.feedbackMessage.textContent = "请输入问题后再提交。";
    return;
  }

  setStatus("正在检索与生成...", true);
  refs.feedbackMessage.textContent = "";

  try {
    const payload = {
      question,
      game_id: refs.gameId.value,
      top_k: Number(refs.topK.value || 5),
      include_sources: true,
      include_assistive_guide: refs.assistiveGuide.checked,
      user_context: {
        user_id: "web-user",
        user_type: refs.userType.value,
        difficulty_level: refs.difficultyLevel.value,
      },
    };

    const result = await fetchJson("/api/v1/qa/ask", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    state.lastQueryLogId = result.metadata?.query_log_id ?? null;
    refs.answerBox.textContent = result.answer || "未返回回答";
    refs.confidenceChip.textContent = `置信度 ${Number(result.confidence || 0).toFixed(3)}`;
    renderMeta(result.metadata || {});
    renderSources(result.sources || []);
    renderAssistiveGuide(result.metadata?.assistive_guide || []);
    setStatus("提问完成");
    await syncProjectView();
  } catch (error) {
    refs.answerBox.textContent = `请求失败：${error.message}`;
    refs.confidenceChip.textContent = "置信度 --";
    renderMeta({});
    renderSources([]);
    renderAssistiveGuide([]);
    setStatus("请求失败");
  }
}

async function submitFeedback() {
  if (!state.selectedRating) {
    refs.feedbackMessage.textContent = "请先选择反馈等级。";
    return;
  }

  try {
    const payload = {
      game_id: refs.gameId.value,
      user_id: "web-user",
      query_log_id: state.lastQueryLogId,
      rating: state.selectedRating,
      comment: refs.feedbackComment.value.trim(),
    };

    await fetchJson("/api/v1/analytics/feedback", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    refs.feedbackComment.value = "";
    refs.feedbackMessage.textContent = "反馈已记录，已纳入后续分析。";
    await syncProjectView();
  } catch (error) {
    refs.feedbackMessage.textContent = `反馈提交失败：${error.message}`;
  }
}

async function runBatchDemo() {
  if (!state.overview?.demo_questions?.length) {
    refs.batchDemoResults.innerHTML = "<p class='subtle'>暂无可用示例。</p>";
    return;
  }

  renderBatchDemoResults([], true);
  try {
    const payload = {
      items: state.overview.demo_questions.map((item) => ({
        ...item,
        user_context: {
          user_id: "demo-batch",
          user_type: "normal",
        },
      })),
    };
    const result = await fetchJson("/api/v1/project/demo-batch", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    renderBatchDemoResults(result.results || []);
    await syncProjectView();
  } catch (error) {
    refs.batchDemoResults.innerHTML = `<p class="subtle">批量演示失败：${escapeHtml(error.message)}</p>`;
  }
}

async function saveProviderConfig(event) {
  event.preventDefault();
  refs.providerMessage.textContent = "正在保存配置...";
  try {
    const payload = {
      provider: refs.providerSelect.value,
      model: refs.providerModel.value.trim() || null,
      api_key: refs.providerApiKey.value.trim() || null,
      storage_mode: refs.storageMode.value,
    };
    const snapshot = await fetchJson("/api/v1/runtime/provider-config", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    renderProviderSnapshot(snapshot);
    refs.providerMessage.textContent = snapshot.persisted
      ? `配置已保存到${storageModeLabel(snapshot.storage_mode)}。`
      : "配置已保存到当前会话，不会写入磁盘。";
    await syncProjectView();
  } catch (error) {
    refs.providerMessage.textContent = `保存失败：${error.message}`;
  }
}

async function testProviderConfig() {
  refs.providerMessage.textContent = "正在测试连接...";
  try {
    const payload = {
      provider: refs.providerSelect.value,
      model: refs.providerModel.value.trim() || null,
      api_key: refs.providerApiKey.value.trim() || null,
    };
    const result = await fetchJson("/api/v1/runtime/provider-config/test", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    refs.providerMessage.textContent = result.success
      ? `连接测试成功：${result.preview}`
      : `连接测试未通过：${result.preview}`;
  } catch (error) {
    refs.providerMessage.textContent = `测试失败：${error.message}`;
  }
}

async function clearProviderConfig() {
  refs.providerMessage.textContent = "正在清除已保存密钥...";
  try {
    const payload = {
      provider: refs.providerSelect.value,
      clear_env: refs.clearEnvOnRemove.checked,
    };
    const snapshot = await fetchJson("/api/v1/runtime/provider-config/clear", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    renderProviderSnapshot(snapshot);
    refs.providerApiKey.value = "";
    refs.providerMessage.textContent = "已移除保存的密钥，当前已回退到安全状态。";
    await syncProjectView();
  } catch (error) {
    refs.providerMessage.textContent = `清除失败：${error.message}`;
  }
}

function bindRatingButtons() {
  const buttons = refs.ratingRow.querySelectorAll(".rating-button");
  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedRating = Number(button.dataset.rating);
      buttons.forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
    });
  });
}

function bindProviderInteractions() {
  refs.providerSelect.addEventListener("change", () => {
    const provider = refs.providerSelect.value;
    renderModelSuggestions(provider);
    const catalog = getProviderCatalog(provider);
    if (!refs.providerModel.value.trim() && catalog.recommended) {
      refs.providerModel.value = catalog.recommended;
    }
  });

  refs.storageMode.addEventListener("change", () => {
    if (refs.storageMode.value === "env") {
      refs.providerMessage.textContent = "提示：.env 属于开发调试模式，安全性低于本机安全存储。";
    }
  });

  refs.toggleApiKeyVisibility.addEventListener("click", () => {
    const showing = refs.providerApiKey.type === "text";
    refs.providerApiKey.type = showing ? "password" : "text";
    refs.toggleApiKeyVisibility.textContent = showing ? "显示" : "隐藏";
  });
}

refs.qaForm.addEventListener("submit", submitQuestion);
refs.providerForm.addEventListener("submit", saveProviderConfig);
refs.submitFeedback.addEventListener("click", submitFeedback);
refs.refreshDashboard.addEventListener("click", refreshDashboard);
refs.gameId.addEventListener("change", refreshDashboard);
refs.runBatchDemo.addEventListener("click", runBatchDemo);
refs.testProviderConfig.addEventListener("click", testProviderConfig);
refs.clearProviderConfig.addEventListener("click", clearProviderConfig);

bindRatingButtons();
bindProviderInteractions();

syncProjectView().catch((error) => {
  refs.heroSubtitle.textContent = `项目展示数据加载失败：${error.message}`;
  refs.batchDemoResults.innerHTML = `<p class="subtle">初始化失败：${escapeHtml(error.message)}</p>`;
});
