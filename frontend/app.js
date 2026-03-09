const state = {
  selectedRating: null,
  lastQueryLogId: null,
  overview: null,
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
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || `请求失败: ${response.status}`);
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
  refs.heroSubtitle.textContent = `${info.project_number || ""} · ${info.college || ""} · 负责人 ${info.leader || ""}。当前页面整合了中期检查信息、申报书亮点、系统演示与实时数据，用于课程汇报和答辩展示。`;
  refs.heroChips.innerHTML = [
    `项目编号 ${info.project_number || "--"}`,
    `负责人 ${info.leader || "--"}`,
    `指导老师 ${info.advisor || "--"}`,
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
  refs.databaseBadge.textContent = database.using_fallback ? "SQLite 回退模式" : "已连接配置数据库";
  refs.databaseBadge.className = `status-badge ${database.using_fallback ? "alert-chip" : "success-chip"}`;
  const entries = [
    ["总查询量", runtime.total_queries ?? 0, "运行期累计"],
    ["总反馈量", runtime.total_feedback ?? 0, "闭环数据"],
    ["平均置信度", runtime.average_confidence ?? 0, "问答输出"],
    ["平均耗时", `${runtime.average_processing_time ?? 0}s`, "接口处理"],
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
    ["日志ID", metadata.query_log_id ?? "--"],
  ];
  refs.metaRow.innerHTML = entries
    .map(([label, value]) => `<span class="meta-pill">${escapeHtml(label)} ${escapeHtml(value)}</span>`)
    .join("");
}

function renderSources(sources = []) {
  if (!sources.length) {
    refs.sourcesList.innerHTML = "<li>暂无来源</li>";
    return;
  }
  refs.sourcesList.innerHTML = sources
    .map((item) => `<li>${escapeHtml(item.source)}</li>`)
    .join("");
}

function renderAssistiveGuide(steps = []) {
  if (!steps.length) {
    refs.assistiveSteps.innerHTML = "<li>本次未返回分步引导。</li>";
    return;
  }

  refs.assistiveSteps.innerHTML = steps
    .map((step, index) => {
      const description = step.description || "请按提示操作";
      const cue = step.visual_cue || "";
      return `<li><span class="step-badge">${index + 1}</span>${escapeHtml(cue)} ${escapeHtml(description)}</li>`;
    })
    .join("");
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
    refs.batchDemoResults.innerHTML = "<p class='subtle'>正在运行答辩示例，请稍候...</p>";
    return;
  }
  if (!results.length) {
    refs.batchDemoResults.innerHTML = "<p class='subtle'>点击右上角“运行答辩示例”后，这里会显示批量演示结果。</p>";
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
  renderList(refs.innovationList, overview.innovations, "暂无创新描述");
  renderTeam(overview);
  renderProposalHighlights(overview);
  renderCoverage(overview);
  renderDemoScenarios(overview);
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
  await Promise.all([loadOverview(), refreshDashboard()]);
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
    refs.feedbackMessage.textContent = "请选择一个反馈等级。";
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

refs.qaForm.addEventListener("submit", submitQuestion);
refs.submitFeedback.addEventListener("click", submitFeedback);
refs.refreshDashboard.addEventListener("click", refreshDashboard);
refs.gameId.addEventListener("change", refreshDashboard);
refs.runBatchDemo.addEventListener("click", runBatchDemo);

bindRatingButtons();
syncProjectView().catch((error) => {
  refs.heroSubtitle.textContent = `项目展示数据加载失败：${error.message}`;
  refs.batchDemoResults.innerHTML = `<p class="subtle">初始化失败：${escapeHtml(error.message)}</p>`;
});
