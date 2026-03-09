const state = {
  selectedRating: null,
  lastQueryLogId: null,
};

const refs = {
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

function setStatus(text, busy = false) {
  refs.statusBadge.textContent = text;
  refs.statusBadge.style.color = busy ? "#f1a65b" : "";
}

function renderMeta(metadata = {}) {
  const entries = [
    ["耗时", metadata.processing_time ? `${metadata.processing_time}s` : "--"],
    ["检索文档", metadata.retrieved ?? "--"],
    ["日志ID", metadata.query_log_id ?? "--"],
  ];
  refs.metaRow.innerHTML = entries
    .map(([label, value]) => `<span class="meta-pill">${label} ${value}</span>`)
    .join("");
}

function renderSources(sources = []) {
  if (!sources.length) {
    refs.sourcesList.innerHTML = "<li>暂无来源</li>";
    return;
  }
  refs.sourcesList.innerHTML = sources
    .map((item) => `<li>${item.source}</li>`)
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
      return `<li><span class="step-badge">${index + 1}</span>${cue} ${description}</li>`;
    })
    .join("");
}

function renderStats(stats) {
  refs.statsGrid.innerHTML = `
    <div class="stat-card">
      <span>近 7 天查询</span>
      <strong>${stats.total_queries}</strong>
    </div>
    <div class="stat-card">
      <span>平均置信度</span>
      <strong>${stats.avg_confidence.toFixed(3)}</strong>
    </div>
    <div class="stat-card">
      <span>平均耗时</span>
      <strong>${stats.avg_processing_time.toFixed(3)}s</strong>
    </div>
    <div class="stat-card">
      <span>累计反馈</span>
      <strong>${stats.total_feedback}</strong>
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
          <span class="trend-label">${label}<br>${item.count}</span>
        </div>
      `;
    })
    .join("");
}

function renderTopQuestions(questions = []) {
  refs.topQuestions.innerHTML = questions.length
    ? questions.map((question) => `<li>${question}</li>`).join("")
    : "<li>暂无数据</li>";
}

function renderPriority(items = []) {
  refs.priorityList.innerHTML = items.length
    ? items
        .map(
          (item) =>
            `<li><strong>${item.label}</strong><span class="priority-score">${item.score}</span><br>${item.title}</li>`,
        )
        .join("")
    : "<li>暂无反馈数据</li>";
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
    await refreshDashboard();
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
    await refreshDashboard();
  } catch (error) {
    refs.feedbackMessage.textContent = `反馈提交失败：${error.message}`;
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

bindRatingButtons();
refreshDashboard();
