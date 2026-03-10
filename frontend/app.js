const state = {
  selectedRating: null,
  lastQueryLogId: null,
  overview: null,
  audit: null,
  controllers: {},
};

const refs = {
  navLinks: Array.from(document.querySelectorAll(".nav-link")),
  sections: Array.from(document.querySelectorAll("section[id]")),
  heroTitle: document.getElementById("heroTitle"),
  heroSubtitle: document.getElementById("heroSubtitle"),
  heroChips: document.getElementById("heroChips"),
  overviewCards: document.getElementById("overviewCards"),
  databaseBadge: document.getElementById("databaseBadge"),
  runtimeCards: document.getElementById("runtimeCards"),
  coverageChip: document.getElementById("coverageChip"),
  coverageGrid: document.getElementById("coverageGrid"),
  auditChip: document.getElementById("auditChip"),
  auditSummary: document.getElementById("auditSummary"),
  architectureStack: document.getElementById("architectureStack"),
  implementedList: document.getElementById("implementedList"),
  apiReferenceList: document.getElementById("apiReferenceList"),
  providerStatusBadge: document.getElementById("providerStatusBadge"),
  providerSnapshot: document.getElementById("providerSnapshot"),
  pythonConfigPath: document.getElementById("pythonConfigPath"),
  pythonConfigSteps: document.getElementById("pythonConfigSteps"),
  pythonConfigCode: document.getElementById("pythonConfigCode"),
  syncStatusChip: document.getElementById("syncStatusChip"),
  syncStats: document.getElementById("syncStats"),
  syncSelectedGame: document.getElementById("syncSelectedGame"),
  syncSchedulerEnabled: document.getElementById("syncSchedulerEnabled"),
  syncInterval: document.getElementById("syncInterval"),
  syncRunScheduled: document.getElementById("syncRunScheduled"),
  saveSyncSchedule: document.getElementById("saveSyncSchedule"),
  refreshSyncStatus: document.getElementById("refreshSyncStatus"),
  syncMessage: document.getElementById("syncMessage"),
  jiraStatusChip: document.getElementById("jiraStatusChip"),
  jiraStats: document.getElementById("jiraStats"),
  previewJiraExport: document.getElementById("previewJiraExport"),
  createJiraExport: document.getElementById("createJiraExport"),
  jiraMessage: document.getElementById("jiraMessage"),
  moduleAuditGrid: document.getElementById("moduleAuditGrid"),
  demoScenarioButtons: document.getElementById("demoScenarioButtons"),
  batchDemoResults: document.getElementById("batchDemoResults"),
  runBatchDemo: document.getElementById("runBatchDemo"),
  qaForm: document.getElementById("qaForm"),
  gameId: document.getElementById("gameId"),
  userType: document.getElementById("userType"),
  difficultyLevel: document.getElementById("difficultyLevel"),
  topK: document.getElementById("topK"),
  enableWebRetrieval: document.getElementById("enableWebRetrieval"),
  assistiveGuide: document.getElementById("assistiveGuide"),
  familyMode: document.getElementById("familyMode"),
  questionInput: document.getElementById("questionInput"),
  answerBox: document.getElementById("answerBox"),
  confidenceChip: document.getElementById("confidenceChip"),
  metaRow: document.getElementById("metaRow"),
  sourcesList: document.getElementById("sourcesList"),
  assistiveSteps: document.getElementById("assistiveSteps"),
  familyGuideBox: document.getElementById("familyGuideBox"),
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

function nextRequestOptions(slot) {
  const active = state.controllers[slot];
  if (active) {
    active.abort();
  }
  const controller = new AbortController();
  state.controllers[slot] = controller;
  return { signal: controller.signal };
}

function isAbortError(error) {
  return error?.name === "AbortError";
}

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

function renderList(container, items = [], emptyText = "暂无数据") {
  container.innerHTML = items.length
    ? items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")
    : `<li>${escapeHtml(emptyText)}</li>`;
}

function setStatus(text, busy = false) {
  refs.statusBadge.textContent = text;
  refs.statusBadge.style.color = busy ? "#f1a65b" : "";
}

function renderHero(overview) {
  const info = overview.system_info || {};
  const runtime = overview.runtime_metrics || {};
  refs.heroTitle.textContent = info.project_name || "RAG 游戏问答系统";
  refs.heroSubtitle.textContent = info.summary || "项目信息加载中";
  refs.heroChips.innerHTML = [
    `定位 ${info.positioning || "--"}`,
    `Provider ${runtime.ai_provider || "mock"}`,
    `模型 ${runtime.model || "--"}`,
    `总查询 ${runtime.total_queries ?? 0}`,
    `总反馈 ${runtime.total_feedback ?? 0}`,
  ].map((item) => `<span class="chip">${escapeHtml(item)}</span>`).join("");
}

function renderOverviewCards(overview) {
  const cards = overview.overview_cards || [];
  refs.overviewCards.innerHTML = cards
    .map(
      (item) => `
        <div class="mini-stat">
          <span>${escapeHtml(item.label)}</span>
          <strong>${escapeHtml(item.value)}</strong>
          <p>${escapeHtml(item.description)}</p>
        </div>
      `,
    )
    .join("");
}

function renderRuntime(overview) {
  const runtime = overview.runtime_metrics || {};
  const database = runtime.database || {};
  refs.databaseBadge.textContent = database.using_fallback
    ? "SQLite 回退模式"
    : (database.is_external ? "外部数据库已连接" : "数据库已连接");
  refs.databaseBadge.className = `status-badge ${database.using_fallback ? "alert-chip" : "success-chip"}`;
  const entries = [
    ["当前 Provider", runtime.ai_provider ?? "mock", runtime.live_llm_enabled ? "已启用真实大模型" : "当前为本地演示或回退模式"],
    ["当前模型", runtime.model ?? "--", "由 Python 配置文件或运行时配置决定"],
    ["数据库后端", database.backend ?? "--", database.active_url || "未识别到连接串"],
    ["联网检索", runtime.web_retrieval_enabled ? "enabled" : "disabled", `触发阈值 ${runtime.web_retrieval_trigger_doc_count ?? "--"} 条`],
    ["自动同步", runtime.knowledge_sync_scheduler_enabled ? "enabled" : "disabled", `间隔 ${runtime.knowledge_sync_interval_minutes ?? "--"} 分钟`],
    ["Jira 联动", runtime.jira_configured ? "configured" : "not configured", "可把优先级报告导出成 Jira 工单"],
    ["配置文件", runtime.python_config_file ?? "--", runtime.python_config_exists ? "本地 Python 配置文件存在" : "请按示例创建配置文件"],
    ["平均耗时", `${runtime.average_processing_time ?? 0}s`, "按最近查询统计"],
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

  refs.providerStatusBadge.textContent = `${runtime.ai_provider || "mock"} · ${runtime.model || "--"}`;
  refs.providerSnapshot.innerHTML = [
    `Provider ${runtime.ai_provider || "mock"}`,
    `模型 ${runtime.model || "--"}`,
    `配置文件 ${runtime.python_config_file || "--"}`,
    `保存方式 ${runtime.storage_mode || "--"}`,
  ].map((item) => `<span class="meta-pill">${escapeHtml(item)}</span>`).join("");
}

function renderCoverage(overview) {
  const coverage = overview.knowledge_coverage || {};
  refs.coverageChip.textContent = `${coverage.total_documents || 0} 篇文档`;
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

function renderArchitecture(overview) {
  refs.architectureStack.innerHTML = (overview.architecture_sections || [])
    .map(
      (section) => `
        <article class="highlight-card">
          <h3>${escapeHtml(section.title)}</h3>
          <ul>${(section.items || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
        </article>
      `,
    )
    .join("");
}

function renderApiReference(overview) {
  refs.apiReferenceList.innerHTML = (overview.api_reference || [])
    .map(
      (item) => `
        <article class="api-card">
          <span class="api-method">${escapeHtml(item.method)}</span>
          <strong>${escapeHtml(item.path)}</strong>
          <p>${escapeHtml(item.name)}</p>
          <small>${escapeHtml(item.description)}</small>
        </article>
      `,
    )
    .join("");
}

function renderPythonConfig(overview) {
  const config = overview.python_config || {};
  refs.pythonConfigPath.textContent = config.config_file || "config/local_provider_config.py";
  renderList(refs.pythonConfigSteps, config.instructions || [], "暂无说明");
  refs.pythonConfigCode.textContent = (config.sample_lines || []).join("\n");
}

function renderKnowledgeSync(overview) {
  const sync = overview.knowledge_sync || {};
  const scheduler = overview.knowledge_sync_scheduler || sync.scheduler || {};
  const games = sync.games || [];
  refs.syncStatusChip.textContent = sync.total_synced_docs
    ? `已同步 ${sync.total_synced_docs} 篇`
    : "尚未落库";

  const topGames = games
    .slice(0, 3)
    .map((item) => `${item.game_id} ${item.synced_docs} 篇`)
    .join(" / ");

  const entries = [
    ["在线文档", sync.total_synced_docs ?? 0, "已经写入数据库的联网资料数量"],
    ["最近同步", sync.last_sync_at ? sync.last_sync_at.replace("T", " ").slice(0, 19) : "--", "最后一次成功落库时间"],
    ["覆盖游戏", games.length || 0, topGames || "还没有同步记录"],
    ["自动计划", scheduler.running ? "运行中" : (scheduler.enabled ? "已启用" : "未启用"), scheduler.next_run_at ? `下次 ${scheduler.next_run_at.replace("T", " ").slice(0, 19)}` : "点击下方按钮开始设置"],
    ["默认来源", (sync.recent_sources || []).length ? "Wiki / Wikipedia" : "--", (sync.recent_sources || []).slice(0, 2).join(" | ") || "点击下方按钮开始同步"],
  ];

  refs.syncStats.innerHTML = entries
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

  refs.syncSchedulerEnabled.checked = Boolean(scheduler.enabled);
  refs.syncInterval.value = scheduler.interval_minutes || 60;
}

function renderJira(overview) {
  const jira = overview.jira || {};
  refs.jiraStatusChip.textContent = jira.configured ? "已配置" : "未配置";
  refs.jiraStats.innerHTML = [
    ["连接状态", jira.configured ? "ready" : "missing", jira.base_url || "请在本地 Python 配置里填写 Jira 地址"],
    ["项目 Key", jira.project_key || "--", jira.issue_type ? `默认类型 ${jira.issue_type}` : "未设置"],
    ["账号", jira.email_masked || "--", jira.api_token_configured ? "Token 已配置" : "Token 未配置"],
    ["标签前缀", jira.label_prefix || "rag-feedback", "导出时会自动打上这组标签"],
  ]
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

function renderAudit(audit) {
  state.audit = audit;
  const summary = audit.summary || {};
  refs.auditChip.textContent = `${summary.implemented || 0} 已实现 / ${summary.partial || 0} 部分实现 / ${summary.missing || 0} 未实现`;
  refs.auditSummary.innerHTML = [
    ["已实现", summary.implemented ?? 0, "可以直接展示或调用"],
    ["部分实现", summary.partial ?? 0, "已有代码但未完全打通"],
    ["未实现", summary.missing ?? 0, "文档中提到但主流程未落地"],
    ["总模块数", summary.total ?? 0, "按当前设计核查"],
  ]
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

  refs.moduleAuditGrid.innerHTML = (audit.items || [])
    .map(
      (item) => `
        <article class="audit-card status-${escapeHtml(item.status)}">
          <div class="panel-header compact-header">
            <h3>${escapeHtml(item.module)}</h3>
            <span class="metric-chip">${escapeHtml(item.status)}</span>
          </div>
          <p>${escapeHtml(item.description)}</p>
          <ul class="simple-list compact-list">
            ${(item.evidence || []).length ? item.evidence.map((evidence) => `<li>${escapeHtml(evidence)}</li>`).join("") : "<li>暂无直接证据文件</li>"}
          </ul>
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
    : "<p class='subtle'>暂无示例问题。</p>";

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
    ["检索模式", metadata.retrieval_mode ?? "--"],
    ["联网补充", metadata.web_augmented ? `是 (${metadata.web_docs || 0})` : "否"],
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

function renderFamilyGuide(familyGuide = null) {
  if (!familyGuide) {
    refs.familyGuideBox.textContent = "本次未启用祖孙协作模式。";
    return;
  }

  const guideType = familyGuide.guide_type || "general_guide";
  const stepGuide = familyGuide.step_guide || [];
  const tips = familyGuide.family_tips || [];
  refs.familyGuideBox.innerHTML = `
    <p><strong>类型：</strong>${escapeHtml(guideType)}</p>
    <p><strong>步骤数：</strong>${escapeHtml(stepGuide.length)}</p>
    <p><strong>家庭提示：</strong>${escapeHtml(tips.slice(0, 2).join("；") || "暂无")}</p>
  `;
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

async function loadOverview() {
  try {
    const overview = await fetchJson("/api/v1/project/overview", nextRequestOptions("overview"));
    state.overview = overview;
    renderHero(overview);
    renderOverviewCards(overview);
    renderRuntime(overview);
    renderCoverage(overview);
    renderArchitecture(overview);
    renderList(refs.implementedList, overview.implemented_modules || [], "暂无已实现模块");
    renderApiReference(overview);
    renderPythonConfig(overview);
    renderKnowledgeSync(overview);
    renderJira(overview);
    renderDemoScenarios(overview);
  } catch (error) {
    if (isAbortError(error)) {
      return;
    }
    throw error;
  }
}

async function loadAudit() {
  try {
    const audit = await fetchJson("/api/v1/project/module-audit", nextRequestOptions("audit"));
    renderAudit(audit);
  } catch (error) {
    if (isAbortError(error)) {
      return;
    }
    throw error;
  }
}

async function refreshDashboard() {
  const gameId = refs.gameId.value;
  try {
    const [stats, priorities] = await Promise.all([
      fetchJson(
        `/api/v1/analytics/query-stats?game_id=${encodeURIComponent(gameId)}&days=7`,
        nextRequestOptions("dashboard"),
      ),
      fetchJson(
        `/api/v1/analytics/priority-report?game_id=${encodeURIComponent(gameId)}`,
        nextRequestOptions("priority"),
      ),
    ]);
    renderStats(stats);
    renderTrends(stats.recent_days || []);
    renderTopQuestions(stats.top_questions || []);
    renderPriority(priorities || []);
  } catch (error) {
    if (isAbortError(error)) {
      return;
    }
    refs.feedbackMessage.textContent = `看板刷新失败：${error.message}`;
  }
}

async function syncProjectView(includeAudit = false) {
  const tasks = [loadOverview(), refreshDashboard()];
  if (includeAudit || !state.audit) {
    tasks.push(loadAudit());
  }
  await Promise.all(tasks);
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
      include_family_guide: refs.familyMode.checked,
      enable_web_retrieval: refs.enableWebRetrieval.checked,
      user_context: {
        user_id: "web-user",
        user_type: refs.userType.value,
        difficulty_level: refs.difficultyLevel.value,
        family_mode: refs.familyMode.checked,
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
    renderFamilyGuide(result.metadata?.family_guide || null);
    setStatus("提问完成");
    await syncProjectView();
  } catch (error) {
    refs.answerBox.textContent = `请求失败：${error.message}`;
    refs.confidenceChip.textContent = "置信度 --";
    renderMeta({});
    renderSources([]);
    renderAssistiveGuide([]);
    renderFamilyGuide(null);
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
    await Promise.all([loadOverview(), refreshDashboard()]);
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
    await Promise.all([loadOverview(), refreshDashboard()]);
  } catch (error) {
    refs.batchDemoResults.innerHTML = `<p class="subtle">批量演示失败：${escapeHtml(error.message)}</p>`;
  }
}

async function runKnowledgeSync() {
  const gameId = refs.gameId.value;
  refs.syncMessage.textContent = `正在同步 ${gameId} 的在线资料...`;
  try {
    const result = await fetchJson("/api/v1/project/knowledge-sync", {
      method: "POST",
      body: JSON.stringify({
        game_id: gameId,
        max_results_per_query: 2,
      }),
    });
    refs.syncMessage.textContent = `同步完成：新增 ${result.stored_new_docs || 0} 篇，跳过 ${result.skipped_existing_docs || 0} 篇重复内容。`;
    await Promise.all([loadOverview(), refreshDashboard()]);
  } catch (error) {
    refs.syncMessage.textContent = `同步失败：${error.message}`;
  }
}

async function saveKnowledgeSyncSchedule() {
  const gameId = refs.gameId.value;
  refs.syncMessage.textContent = `正在保存 ${gameId} 的自动同步计划...`;
  try {
    const result = await fetchJson("/api/v1/project/knowledge-sync/scheduler", {
      method: "POST",
      body: JSON.stringify({
        enabled: refs.syncSchedulerEnabled.checked,
        interval_minutes: Number(refs.syncInterval.value || 60),
        game_ids: [gameId],
        max_results_per_query: 2,
      }),
    });
    refs.syncMessage.textContent = `计划已保存：${result.enabled ? "已启用" : "已停用"}，间隔 ${result.interval_minutes} 分钟。`;
    await loadOverview();
  } catch (error) {
    refs.syncMessage.textContent = `保存失败：${error.message}`;
  }
}

async function runScheduledSyncNow() {
  const gameId = refs.gameId.value;
  refs.syncMessage.textContent = `正在按计划立即执行 ${gameId} 的同步...`;
  try {
    const result = await fetchJson("/api/v1/project/knowledge-sync/scheduler/run", {
      method: "POST",
      body: JSON.stringify({
        game_ids: [gameId],
      }),
    });
    refs.syncMessage.textContent = `执行完成：新增 ${result.total_stored_new_docs || 0} 篇，跳过 ${result.total_skipped_existing_docs || 0} 篇。`;
    await loadOverview();
  } catch (error) {
    refs.syncMessage.textContent = `执行失败：${error.message}`;
  }
}

async function exportJira(dryRun = true) {
  refs.jiraMessage.textContent = dryRun ? "正在生成 Jira 预览..." : "正在创建 Jira 工单...";
  try {
    const result = await fetchJson("/api/v1/analytics/jira/export", {
      method: "POST",
      body: JSON.stringify({
        game_id: refs.gameId.value,
        limit: 3,
        dry_run: dryRun,
      }),
    });
    const issuePreview = (result.issues || [])
      .map((item) => (item.jira_key ? `${item.summary} -> ${item.jira_key}` : item.summary))
      .join("；");
    refs.jiraMessage.textContent = dryRun
      ? `预览完成：共 ${result.issue_count} 项。${issuePreview || "暂无可导出的优先级项。"}`
      : `已处理 ${result.issue_count} 项。${issuePreview || "没有生成新工单。"}`
    ;
    await Promise.all([loadOverview(), refreshDashboard()]);
  } catch (error) {
    refs.jiraMessage.textContent = `Jira 导出失败：${error.message}`;
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

function setActiveNav(targetId) {
  refs.navLinks.forEach((link) => {
    const active = link.getAttribute("href") === `#${targetId}`;
    link.classList.toggle("is-active", active);
  });
}

function bindSectionNav() {
  if (!("IntersectionObserver" in window) || !refs.sections.length) {
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      const visible = entries
        .filter((entry) => entry.isIntersecting)
        .sort((left, right) => right.intersectionRatio - left.intersectionRatio);
      if (visible.length) {
        setActiveNav(visible[0].target.id);
      }
    },
    {
      rootMargin: "-18% 0px -55% 0px",
      threshold: [0.2, 0.45, 0.7],
    },
  );

  refs.sections.forEach((section) => observer.observe(section));
  refs.navLinks.forEach((link) => {
    link.addEventListener("click", () => {
      const targetId = link.getAttribute("href")?.replace("#", "");
      if (targetId) {
        setActiveNav(targetId);
      }
    });
  });
}

refs.qaForm.addEventListener("submit", submitQuestion);
refs.submitFeedback.addEventListener("click", submitFeedback);
refs.refreshDashboard.addEventListener("click", refreshDashboard);
refs.gameId.addEventListener("change", refreshDashboard);
refs.runBatchDemo.addEventListener("click", runBatchDemo);
refs.syncSelectedGame.addEventListener("click", runKnowledgeSync);
refs.saveSyncSchedule.addEventListener("click", saveKnowledgeSyncSchedule);
refs.syncRunScheduled.addEventListener("click", runScheduledSyncNow);
refs.refreshSyncStatus.addEventListener("click", () => syncProjectView(false));
refs.previewJiraExport.addEventListener("click", () => exportJira(true));
refs.createJiraExport.addEventListener("click", () => exportJira(false));

bindRatingButtons();
bindSectionNav();
syncProjectView(true).catch((error) => {
  refs.heroSubtitle.textContent = `系统页面加载失败：${error.message}`;
  refs.batchDemoResults.innerHTML = `<p class="subtle">初始化失败：${escapeHtml(error.message)}</p>`;
});
