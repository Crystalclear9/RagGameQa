const SESSIONS_KEY = "rag-game-qa-sessions-v1";

function generateId() {
  return Math.random().toString(36).substr(2, 9);
}

function loadSessions() {
  try {
    const raw = window.localStorage.getItem(SESSIONS_KEY);
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) && parsed.length > 0 ? parsed : createDefaultSession();
  } catch {
    return createDefaultSession();
  }
}

function createDefaultSession() {
  return [{ 
    id: generateId(), 
    title: '新对话', 
    gameId: 'wow', 
    messages: [{ role: 'system', text: '您好！我是您的游戏问答智能体，请在这片全新净土提问。' }] 
  }];
}

function initParticleLogo() {
  const canvas = document.getElementById('particleLogo');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  
  const dpr = window.devicePixelRatio || 1;
  const size = 32;
  canvas.width = size * dpr;
  canvas.height = size * dpr;
  ctx.scale(dpr, dpr);
  
  const particles = [];
  const numParticles = 14;
  for(let i = 0; i < numParticles; i++) {
    particles.push({
      x: Math.random() * size, 
      y: Math.random() * size,
      vx: (Math.random() - 0.5) * 0.4, 
      vy: (Math.random() - 0.5) * 0.4
    });
  }
  
  function animate() {
    ctx.clearRect(0, 0, size, size);
    for(let i = 0; i < particles.length; i++) {
      let p = particles[i];
      p.x += p.vx; p.y += p.vy;
      
      if (p.x < 0 || p.x > size) p.vx *= -1;
      if (p.y < 0 || p.y > size) p.vy *= -1;
      
      ctx.beginPath();
      ctx.arc(p.x, p.y, 1.2, 0, Math.PI * 2);
      ctx.fillStyle = '#0ea5e9';
      ctx.fill();
      
      for(let j = i + 1; j < particles.length; j++) {
        let p2 = particles[j];
        let d = Math.hypot(p.x - p2.x, p.y - p2.y);
        if (d < 12) {
          ctx.beginPath();
          ctx.moveTo(p.x, p.y); 
          ctx.lineTo(p2.x, p2.y);
          ctx.strokeStyle = `rgba(14, 165, 233, ${1 - d/12})`;
          ctx.lineWidth = 0.6;
          ctx.stroke();
        }
      }
    }
    requestAnimationFrame(animate);
  }
  animate();
}

const state = {
  sessions: loadSessions(),
  currentSessionId: null
};

const refs = {
  gamePickCards: Array.from(document.querySelectorAll('.game-pill')),
  gameIdInput: document.getElementById('gameId'),
  historyList: document.getElementById('historyList'),
  chatContainer: document.getElementById('chatContainer'),
  chatForm: document.getElementById('chatForm'),
  questionInput: document.getElementById('questionInput'),
  sendBtn: document.querySelector('.send-btn'),
  newChatBtn: document.getElementById('newChatBtn'),
  enableWebRetrieval: document.getElementById('enableWebRetrieval'),
  assistiveGuide: document.getElementById('assistiveGuide'),
  familyMode: document.getElementById('familyMode'),
  voiceBtn: document.getElementById('voiceBtn'),
  confidenceLabel: document.getElementById('confidenceLabel'),
  plusMenuBtn: document.getElementById('plusMenuBtn'),
  pluginsMenu: document.getElementById('pluginsMenu')
};

function saveSessions() {
  try {
    window.localStorage.setItem(SESSIONS_KEY, JSON.stringify(state.sessions));
  } catch { }
}

function getActiveSession() {
  return state.sessions.find(s => s.id === state.currentSessionId) || state.sessions[0];
}

function switchSession(sessionId) {
  state.currentSessionId = sessionId;
  const session = getActiveSession();
  
  // Select game pill
  refs.gamePickCards.forEach(c => {
    c.classList.toggle('active', c.dataset.game === session.gameId);
  });
  refs.gameIdInput.value = session.gameId;

  renderMessages();
  renderSidebar();
}

function renderSidebar() {
  refs.historyList.innerHTML = state.sessions.map(s => `
    <div class="history-item ${s.id === state.currentSessionId ? 'active' : ''}" data-id="${s.id}">
      <svg class="history-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
      <span class="history-title">${s.title}</span>
      <button class="delete-session-btn" data-id="${s.id}" title="删除对话">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
      </button>
    </div>
  `).join("");
}

function renderMessages() {
  refs.chatContainer.innerHTML = '';
  const session = getActiveSession();
  session.messages.forEach(msg => {
    _appendMessageDOM(msg.role, msg.text, msg.metadata);
  });
}

function _appendMessageDOM(role, text, metadata = null) {
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${role}-message`;
  
  const avatarDiv = document.createElement('div');
  avatarDiv.className = `avatar ${role}-avatar`;
  
  if (role === 'system') {
    avatarDiv.innerHTML = `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 10a8 8 0 0 1 16 0v5"></path><rect x="2" y="10" width="4" height="7" rx="1.5"></rect><rect x="18" y="10" width="4" height="7" rx="1.5"></rect><rect x="7" y="9" width="10" height="6" rx="2" fill="currentColor" fill-opacity="0.15"></rect><circle cx="9.5" cy="12" r="1.5" fill="currentColor"></circle><circle cx="14.5" cy="12" r="1.5" fill="currentColor"></circle><path d="M20 15v2c0 1-1 1.5-1 1.5l-2.5 .5"></path></svg>`;
  } else {
    avatarDiv.innerHTML = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="5"></circle><path d="M20 21a8 8 0 1 0-16 0"></path></svg>`;
  }

  const bubbleDiv = document.createElement('div');
  bubbleDiv.className = 'bubble';
  bubbleDiv.textContent = text;
  
  if (role === 'system' && metadata && metadata.sources && metadata.sources.length > 0) {
    const sourcesDiv = document.createElement('div');
    sourcesDiv.className = 'sources-box';
    sourcesDiv.innerHTML = `<strong>检索来源:</strong> ` + [...new Set(metadata.sources.map(s => s.source))].join(" ; ");
    bubbleDiv.appendChild(sourcesDiv);
  }

  // Interactive Avatar: click to trigger animation
  avatarDiv.style.cursor = "pointer";
  avatarDiv.title = role === 'system' ? '点击我看看动画' : '点击我打个招呼';
  avatarDiv.addEventListener('click', () => {
    // Remove existing animation class to allow re-trigger
    avatarDiv.classList.remove('avatar-clicked');
    void avatarDiv.offsetWidth; // force reflow
    avatarDiv.classList.add('avatar-clicked');
    // Spawn ripple ring
    const ripple = document.createElement('span');
    ripple.className = 'avatar-ripple';
    avatarDiv.appendChild(ripple);
    setTimeout(() => ripple.remove(), 600);
  });

  messageDiv.appendChild(avatarDiv);
  messageDiv.appendChild(bubbleDiv);
  refs.chatContainer.appendChild(messageDiv);
  refs.chatContainer.scrollTo({ top: refs.chatContainer.scrollHeight, behavior: 'smooth' });
  
  return { bubbleDiv, messageDiv };
}

function addMessageToSession(role, text, metadata = null) {
  const session = getActiveSession();
  session.messages.push({ role, text, metadata });
  // Dynamic Title
  if (session.messages.length === 3 && role === 'user') {
    session.title = text.substring(0, 15) + (text.length > 15 ? '...' : '');
  }
  saveSessions();
  renderSidebar();
}

function checkInput() {
  refs.sendBtn.disabled = refs.questionInput.value.trim() === '';
}

refs.questionInput.addEventListener('input', () => {
  refs.questionInput.style.height = 'auto';
  refs.questionInput.style.height = (refs.questionInput.scrollHeight) + 'px';
  checkInput();
});

refs.questionInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    if (!refs.sendBtn.disabled) refs.chatForm.dispatchEvent(new Event('submit'));
  }
});

refs.gamePickCards.forEach(card => {
  card.addEventListener('click', () => {
    refs.gamePickCards.forEach(c => c.classList.remove('active'));
    card.classList.add('active');
    refs.gameIdInput.value = card.dataset.game;
    
    // Change active session's game if we are starting a fresh chat
    const session = getActiveSession();
    if (session.messages.length <= 1) {
      session.gameId = card.dataset.game;
      saveSessions();
      renderSidebar();
    }
  });
});

if (refs.plusMenuBtn && refs.pluginsMenu) {
  refs.plusMenuBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    refs.pluginsMenu.classList.toggle('show');
  });
  
  document.addEventListener('click', (e) => {
    if (!refs.pluginsMenu.contains(e.target) && !refs.plusMenuBtn.contains(e.target)) {
      refs.pluginsMenu.classList.remove('show');
    }
  });
}

refs.newChatBtn.addEventListener('click', () => {
  const newSess = { 
    id: generateId(), 
    title: '新对话', 
    gameId: refs.gameIdInput.value, 
    messages: [{ role: 'system', text: '您好！我是您的专属问答智能体，已为您开启一段全新的对话之旅。' }] 
  };
  state.sessions.unshift(newSess);
  saveSessions();
  switchSession(newSess.id);
});

if (refs.voiceBtn) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SpeechRecognition) {
    const recognition = new SpeechRecognition();
    recognition.lang = 'zh-CN';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = function() {
      refs.voiceBtn.classList.add('recording');
      refs.questionInput.value = "正在倾听 (Speak now)...";
    };

    recognition.onresult = function(event) {
      const transcript = event.results[0][0].transcript;
      refs.questionInput.value = transcript;
      checkInput();
    };

    recognition.onerror = function(event) {
      refs.voiceBtn.classList.remove('recording');
      if (event.error === 'not-allowed') {
        refs.questionInput.value = "无法使用麦克风：浏览器拦截了请求！请尝试通过 http://127.0.0.1:8000 访问，或检查浏览器麦克风权限。";
      } else {
        refs.questionInput.value = "语音识别错误: " + event.error;
      }
    };

    recognition.onend = function() {
      refs.voiceBtn.classList.remove('recording');
      checkInput();
    };

    refs.voiceBtn.addEventListener('click', () => {
      refs.questionInput.value = '';
      if (refs.voiceBtn.classList.contains('recording')) {
        recognition.stop();
      } else {
        try {
          recognition.start();
        } catch(e) {
          refs.questionInput.value = "启动麦克风失败，可能未正确加载授权。";
        }
      }
    });
  } else {
    refs.voiceBtn.addEventListener('click', () => {
      refs.questionInput.value = "您的浏览器不支持 Web Speech API，请使用 Chrome。";
    });
  }
}

// ==================== Submit with Retry + Abort + Edit ====================
let _currentAbortController = null;
let _lastUserQuestion = '';

function _setStopMode(active) {
  if (active) {
    refs.sendBtn.disabled = false;
    refs.sendBtn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="6" y="6" width="12" height="12" rx="2"></rect></svg>';
    refs.sendBtn.title = '停止生成';
    refs.sendBtn.classList.add('stop-mode');
  } else {
    refs.sendBtn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>';
    refs.sendBtn.title = '发送';
    refs.sendBtn.classList.remove('stop-mode');
    checkInput();
  }
}

async function _doFetch(question, gameId, signal) {
  const response = await fetch("/api/v1/qa/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    signal,
    body: JSON.stringify({
      question,
      game_id: gameId,
      top_k: 5,
      include_sources: true,
      enable_web_retrieval: refs.enableWebRetrieval.checked,
      include_assistive_guide: refs.assistiveGuide.checked,
      include_family_guide: refs.familyMode.checked,
      user_context: { user_id: "web-user", user_type: refs.familyMode.checked ? "elderly" : "normal" }
    })
  });
  if (!response.ok) throw new Error("Server error");
  return response.json();
}

function _isRetryableAnswer(text) {
  const markers = ['连接失败', '请求异常', '请稍后重试', 'timed out', 'timeout'];
  return markers.some(m => text.includes(m));
}

refs.chatForm.addEventListener('submit', async (e) => {
  e.preventDefault();

  // If currently generating → abort
  if (_currentAbortController) {
    _currentAbortController.abort();
    _currentAbortController = null;
    return;
  }

  const question = refs.questionInput.value.trim();
  if (!question) return;

  _lastUserQuestion = question;
  const gameId = refs.gameIdInput.value;

  const session = getActiveSession();
  if (session.messages.length === 1) {
    session.gameId = gameId;
    session.title = question.substring(0, 15);
  }

  const { messageDiv: userMsgDiv } = _appendMessageDOM('user', question);
  addMessageToSession('user', question);

  refs.questionInput.value = '';
  refs.questionInput.style.height = 'auto';
  checkInput();

  const { bubbleDiv: loadingBubble, messageDiv: loadingMsg } = _appendMessageDOM('system', '正在检索并生成答案...');
  refs.confidenceLabel.textContent = "执行中...";

  const abortCtrl = new AbortController();
  _currentAbortController = abortCtrl;
  _setStopMode(true);

  const MAX_RETRIES = 3;
  let lastError = null;

  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    if (abortCtrl.signal.aborted) break;
    try {
      if (attempt > 1) {
        loadingBubble.textContent = `第 ${attempt}/${MAX_RETRIES} 次重试中，请稍候...`;
      }
      const result = await _doFetch(question, gameId, abortCtrl.signal);

      let answerText = result.answer;

      // Check if server returned a retryable error message
      if (_isRetryableAnswer(answerText) && attempt < MAX_RETRIES) {
        lastError = answerText;
        continue; // auto-retry
      }

      let metadataObj = null;
      if (refs.assistiveGuide.checked && result.metadata?.assistive_guide) {
        answerText += "\n\n【分步引导】\n" + result.metadata.assistive_guide.map((s, i) => `${i + 1}. ${s.description}`).join("\n");
      }
      if (result.sources && result.sources.length) {
        metadataObj = { sources: result.sources };
      }

      loadingBubble.textContent = answerText;
      if (metadataObj && metadataObj.sources) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'sources-box';
        sourcesDiv.innerHTML = `<strong>检索来源:</strong> ` + [...new Set(metadataObj.sources.map(s => s.source))].join(" ; ");
        loadingBubble.appendChild(sourcesDiv);
      }

      addMessageToSession('system', answerText, metadataObj);
      refs.confidenceLabel.textContent = `生成完毕 | 置信度: ${(result.confidence || 0).toFixed(2)}`;
      lastError = null;
      break; // success

    } catch (err) {
      if (err.name === 'AbortError') {
        // Remove both the user msg and loading bubble from DOM
        if (userMsgDiv && userMsgDiv.parentNode) userMsgDiv.remove();
        if (loadingMsg && loadingMsg.parentNode) loadingMsg.remove();
        // Remove from session data (pop the user message we just added)
        const sess = getActiveSession();
        if (sess.messages.length > 0 && sess.messages[sess.messages.length - 1].role === 'user') {
          sess.messages.pop();
          saveSessions();
          renderSidebar();
        }
        refs.confidenceLabel.textContent = "已撤回";
        // Restore question for editing
        refs.questionInput.value = _lastUserQuestion;
        refs.questionInput.style.height = 'auto';
        refs.questionInput.focus();
        checkInput();
        lastError = null;
        break;
      }
      lastError = err.message || '未知错误';
      if (attempt >= MAX_RETRIES) break;
    }
  }

  if (lastError) {
    loadingBubble.textContent = `经过 ${MAX_RETRIES} 次尝试仍失败：${lastError}\n点击消息可将问题还原到输入框重新编辑发送。`;
    addMessageToSession('system', `请求失败：${lastError}`);
    refs.confidenceLabel.textContent = "执行出错";
    // Click-to-edit on error bubble
    loadingBubble.style.cursor = 'pointer';
    loadingBubble.addEventListener('click', () => {
      refs.questionInput.value = _lastUserQuestion;
      refs.questionInput.focus();
      checkInput();
    }, { once: true });
  }

  _currentAbortController = null;
  _setStopMode(false);
});

// Init
refs.historyList.addEventListener('click', (e) => {
  const btn = e.target.closest('.delete-session-btn');
  if (btn) {
    e.stopPropagation();
    e.preventDefault();
    const targetId = btn.dataset.id;
    // Hard purge
    state.sessions = state.sessions.filter(s => s.id !== targetId);
    if (!state.sessions || state.sessions.length === 0) {
      const activeGame = (typeof refs !== 'undefined' && refs.gameIdInput) ? refs.gameIdInput.value : 'wow';
      state.sessions = [{
        id: generateId(),
        title: '新对话',
        gameId: activeGame,
        messages: [{ role: 'system', text: '您好！我是您的游戏问答智能体，已为您开启一段全新的对话之旅。' }]
      }];
      state.currentSessionId = state.sessions[0].id;
    } else if (targetId === state.currentSessionId) {
      state.currentSessionId = state.sessions[0].id;
    }
    saveSessions();
    switchSession(state.currentSessionId);
    return;
  }
  
  const item = e.target.closest('.history-item');
  if (item) {
    switchSession(item.dataset.id);
  }
});

// ==================== Accordion Fold ====================
(function initAccordion() {
  const trigger = document.getElementById('gameDomainsTrigger');
  const panel   = document.getElementById('gameDomainsContent');
  const chevron = trigger ? trigger.querySelector('.chevron') : null;
  if (!trigger || !panel) return;
  let collapsed = false;
  trigger.addEventListener('click', () => {
    collapsed = !collapsed;
    panel.classList.toggle('collapsed', collapsed);
    if (chevron) chevron.classList.toggle('rotated', collapsed);
  });
})();

// ==================== Custom Game Domain ====================
(function initCustomDomain() {
  const input = document.getElementById('customDomainInput');
  const btn   = document.getElementById('addDomainBtn');
  const panel = document.getElementById('gameDomainsContent');
  if (!input || !btn || !panel) return;

  function addDomain() {
    const name = input.value.trim();
    if (!name) return;
    // Check duplicate
    const exists = refs.gamePickCards.some(c => c.dataset.game === name);
    if (exists) { input.value = ''; return; }

    // Deselect all
    refs.gamePickCards.forEach(c => c.classList.remove('active'));

    const pill = document.createElement('button');
    pill.className = 'game-pill active';
    pill.dataset.game = name;
    pill.textContent = name;

    // Add close ×
    const delBtn = document.createElement('span');
    delBtn.textContent = ' ×';
    delBtn.style.cssText = 'margin-left:4px;color:#dc2626;cursor:pointer;font-weight:bold;';
    delBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      pill.remove();
      refs.gamePickCards = refs.gamePickCards.filter(c => c !== pill);
      if (refs.gameIdInput.value === name && refs.gamePickCards.length > 0) {
        refs.gamePickCards[0].classList.add('active');
        refs.gameIdInput.value = refs.gamePickCards[0].dataset.game;
      }
    });
    pill.appendChild(delBtn);

    pill.addEventListener('click', () => {
      refs.gamePickCards.forEach(c => c.classList.remove('active'));
      pill.classList.add('active');
      refs.gameIdInput.value = name;
      const session = getActiveSession();
      if (session.messages.length <= 1) {
        session.gameId = name;
        saveSessions();
        renderSidebar();
      }
    });

    refs.gamePickCards.push(pill);
    const box = panel.querySelector('.custom-domain-box');
    if (box) panel.insertBefore(pill, box);
    else panel.appendChild(pill);

    refs.gameIdInput.value = name;
    input.value = '';

    const session = getActiveSession();
    if (session.messages.length <= 1) {
      session.gameId = name;
      saveSessions();
      renderSidebar();
    }
  }

  btn.addEventListener('click', addDomain);
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { e.preventDefault(); addDomain(); }
  });
})();

initParticleLogo();
state.currentSessionId = state.sessions[0].id;
switchSession(state.currentSessionId);
checkInput();
