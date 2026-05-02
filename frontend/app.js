/**
 * app.js — Voice AI Agent Frontend
 * Manages: Voice I/O, REST API calls, UI rendering
 */

const API_BASE = '';
let sessionId = '';
let isListening = false;
let isSpeaking = false;
let currentFilter = '';
let recognition = null;
let synth = window.speechSynthesis;
let textMode = false;

// ── Elements ────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const micBtn          = $('micBtn');
const micIcon         = $('micIcon');
const statusDot       = $('statusDot');
const statusLabel     = $('statusLabel');
const chatMessages    = $('chatMessages');
const transcriptText  = $('transcriptText');
const transcriptPlaceholder = $('transcriptPlaceholder');
const waveform        = $('waveform');
const waveBarsEl      = $('waveBars');
const todoList        = $('todoList');
const todoEmpty       = $('todoEmpty');
const todoCount       = $('todoCount');
const memoryList      = $('memoryList');
const memoryEmpty     = $('memoryEmpty');
const memoryCount     = $('memoryCount');
const toastContainer  = $('toastContainer');
const textInputArea   = $('textInputArea');
const textInput       = $('textInput');
const btnTextMode     = $('btnTextMode');
const btnSend         = $('btnSend');
const btnClearChat    = $('btnClearChat');

// ── Wave bars init ───────────────────────────────────────────
(function initWaveBars() {
  for (let i = 0; i < 24; i++) {
    const bar = document.createElement('div');
    bar.className = 'wave-bar';
    bar.style.animationDelay = `${(i * 0.08).toFixed(2)}s`;
    waveBarsEl.appendChild(bar);
  }
})();

// ── Status helpers ───────────────────────────────────────────
function setStatus(state, label) {
  statusDot.className = 'status-dot' + (state ? ` ${state}` : '');
  statusLabel.textContent = label;
}

// ── Voice: Speech Recognition ────────────────────────────────
function initRecognition() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) { showToast('⚠ Speech Recognition not supported. Use Chrome.', 'error'); return null; }
  const r = new SR();
  r.continuous = false;
  r.interimResults = true;
  r.lang = 'en-US';

  r.onstart = () => {
    isListening = true;
    micBtn.classList.add('listening');
    micIcon.textContent = '⏹';
    waveform.classList.add('active');
    transcriptPlaceholder.style.display = 'none';
    transcriptText.textContent = '';
    setStatus('listening', 'Listening…');
    animateWave();
  };

  r.onresult = e => {
    let interim = '', final = '';
    for (let i = e.resultIndex; i < e.results.length; i++) {
      if (e.results[i].isFinal) final += e.results[i][0].transcript;
      else interim += e.results[i][0].transcript;
    }
    transcriptText.textContent = final || interim;
  };

  r.onend = () => {
    isListening = false;
    micBtn.classList.remove('listening');
    micIcon.textContent = '🎤';
    waveform.classList.remove('active');
    setStatus('', 'Ready');
    const spoken = transcriptText.textContent.trim();
    if (spoken) {
      transcriptPlaceholder.style.display = 'none';
      sendMessage(spoken);
    } else {
      transcriptPlaceholder.style.display = '';
      transcriptText.textContent = '';
    }
  };

  r.onerror = e => {
    isListening = false;
    micBtn.classList.remove('listening');
    micIcon.textContent = '🎤';
    waveform.classList.remove('active');
    setStatus('', 'Ready');
    if (e.error !== 'no-speech') showToast(`Mic error: ${e.error}`, 'error');
    transcriptPlaceholder.style.display = '';
  };

  return r;
}

function animateWave() {
  if (!isListening) return;
  const bars = waveBarsEl.querySelectorAll('.wave-bar');
  bars.forEach(bar => {
    const h = Math.random() * 32 + 4;
    bar.style.height = h + 'px';
  });
  setTimeout(animateWave, 120);
}

// ── Voice: Text to Speech ─────────────────────────────────────
function speak(text) {
  if (!synth || !text) return;
  synth.cancel();
  const clean = text.replace(/[*_`#]/g, '').substring(0, 500);
  const utt = new SpeechSynthesisUtterance(clean);
  utt.rate = 1.05; utt.pitch = 1; utt.volume = 1;
  const voices = synth.getVoices();
  const preferred = voices.find(v => v.name.includes('Google') && v.lang.startsWith('en'))
    || voices.find(v => v.lang.startsWith('en-'));
  if (preferred) utt.voice = preferred;
  utt.onstart = () => { isSpeaking = true; setStatus('speaking', 'Speaking…'); };
  utt.onend   = () => { isSpeaking = false; setStatus('', 'Ready'); };
  synth.speak(utt);
}

// ── Mic button toggle ─────────────────────────────────────────
micBtn.addEventListener('click', () => {
  if (isSpeaking) { synth.cancel(); isSpeaking = false; setStatus('', 'Ready'); return; }
  if (isListening) { recognition && recognition.stop(); return; }
  if (!recognition) recognition = initRecognition();
  if (!recognition) return;
  try { recognition.start(); }
  catch(e) { recognition = initRecognition(); recognition && recognition.start(); }
});

// ── Text mode toggle ──────────────────────────────────────────
btnTextMode.addEventListener('click', () => {
  textMode = !textMode;
  textInputArea.style.display = textMode ? 'flex' : 'none';
  btnTextMode.style.background = textMode ? 'rgba(124,77,255,0.2)' : '';
  btnTextMode.style.borderColor = textMode ? 'var(--purple)' : '';
  if (textMode) textInput.focus();
});

btnSend.addEventListener('click', () => {
  const msg = textInput.value.trim();
  if (msg) { textInput.value = ''; sendMessage(msg); }
});

textInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    const msg = textInput.value.trim();
    if (msg) { textInput.value = ''; sendMessage(msg); }
  }
});

btnClearChat.addEventListener('click', () => {
  const msgs = chatMessages.querySelectorAll('.message');
  msgs.forEach((m, i) => { if (i > 0) m.remove(); });
  sessionId = '';
  showToast('💬 Conversation cleared');
});

// ── Send message ──────────────────────────────────────────────
async function sendMessage(text) {
  appendMessage('user', text);
  transcriptText.textContent = '';
  transcriptPlaceholder.style.display = '';
  setStatus('thinking', 'Thinking…');

  const thinkId = appendThinking();

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, message: text }),
    });
    if (!res.ok) throw new Error(`Server error ${res.status}`);
    const data = await res.json();

    sessionId = data.session_id;
    removeThinking(thinkId);

    appendMessage('agent', data.reply, data.tool_calls);
    renderTodos(data.todos);
    renderMemories(data.memories);

    if (data.tool_calls && data.tool_calls.length > 0) {
      data.tool_calls.forEach(t => showToast(`⚡ Tool called: ${t}`, 'tool'));
    }

    speak(data.reply);
    setStatus('', 'Ready');
  } catch (err) {
    removeThinking(thinkId);
    setStatus('', 'Error');
    const errMsg = `Sorry, I encountered an error: ${err.message}`;
    appendMessage('agent', errMsg, []);
    speak(errMsg);
    showToast(`❌ ${err.message}`, 'error');
  }
}

// ── Chat UI ───────────────────────────────────────────────────
function timeStr() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function appendMessage(role, text, toolCalls = []) {
  const div = document.createElement('div');
  div.className = `message message-${role}`;
  const avatar = role === 'agent' ? '◈' : '👤';

  const toolBadgesHtml = (toolCalls || []).map(t =>
    `<span class="tool-badge">⚡ ${t}</span>`
  ).join('');

  div.innerHTML = `
    <div class="message-avatar">${avatar}</div>
    <div class="message-content">
      <div class="message-bubble">
        <p>${escapeHtml(text)}</p>
      </div>
      ${toolBadgesHtml ? `<div>${toolBadgesHtml}</div>` : ''}
      <div class="message-time">${timeStr()}</div>
    </div>`;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return div;
}

let thinkCounter = 0;
function appendThinking() {
  const id = 'think-' + (++thinkCounter);
  const div = document.createElement('div');
  div.id = id; div.className = 'message message-agent';
  div.innerHTML = `
    <div class="message-avatar">◈</div>
    <div class="message-content">
      <div class="thinking-bubble">
        <div class="thinking-dots">
          <span></span><span></span><span></span>
        </div>
      </div>
    </div>`;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return id;
}
function removeThinking(id) { const el = $(id); if (el) el.remove(); }

function escapeHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── Todo Rendering ────────────────────────────────────────────
function renderTodos(todos) {
  const filtered = currentFilter ? todos.filter(t => t.status === currentFilter) : todos;
  todoCount.textContent = todos.length;

  if (!filtered.length) {
    todoList.innerHTML = '';
    todoList.appendChild(todoEmpty);
    todoEmpty.style.display = 'flex';
    return;
  }
  todoEmpty.style.display = 'none';
  todoList.innerHTML = '';

  filtered.forEach(t => {
    const card = document.createElement('div');
    card.className = `todo-card priority-${t.priority} status-${t.status}`;
    card.innerHTML = `
      <div class="todo-header">
        <span class="todo-title">${escapeHtml(t.title)}</span>
        <button class="todo-delete-btn" onclick="quickDelete(${t.id})" title="Delete">✕</button>
      </div>
      <div class="todo-meta">
        <span class="badge badge-status-${t.status}">${t.status.replace('_',' ')}</span>
        <span class="badge badge-priority-${t.priority}">${t.priority}</span>
        <span class="todo-id">#${t.id}</span>
        ${t.due_date ? `<span class="todo-due">📅 ${t.due_date}</span>` : ''}
      </div>`;
    todoList.appendChild(card);
  });
}

async function quickDelete(id) {
  try {
    await fetch(`${API_BASE}/api/todos/${id}`, { method: 'DELETE' });
    const res  = await fetch(`${API_BASE}/api/todos`);
    const data = await res.json();
    renderTodos(data.tasks || []);
    showToast(`🗑 Task #${id} deleted`);
  } catch(e) { showToast('Failed to delete task', 'error'); }
}

// ── Memory Rendering ──────────────────────────────────────────
function renderMemories(memories) {
  memoryCount.textContent = memories.length;
  if (!memories.length) {
    memoryList.innerHTML = '';
    memoryList.appendChild(memoryEmpty);
    memoryEmpty.style.display = 'flex';
    return;
  }
  memoryEmpty.style.display = 'none';
  memoryList.innerHTML = '';
  memories.forEach(m => {
    const card = document.createElement('div');
    card.className = `memory-card importance-${m.importance}`;
    const date = m.created_at ? new Date(m.created_at).toLocaleDateString() : '';
    card.innerHTML = `
      <p class="memory-summary">${escapeHtml(m.summary)}</p>
      <div class="memory-meta">
        <span class="badge badge-priority-${m.importance === 'high' ? 'high' : m.importance === 'low' ? 'low' : 'medium'}">${m.importance}</span>
        ${m.tags ? `<span class="memory-tags">${escapeHtml(m.tags)}</span>` : ''}
        <span class="memory-date">${date}</span>
      </div>`;
    memoryList.appendChild(card);
  });
}

// ── Filter tabs ───────────────────────────────────────────────
document.querySelectorAll('.filter-tab').forEach(tab => {
  tab.addEventListener('click', async () => {
    document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    currentFilter = tab.dataset.filter;
    const res  = await fetch(`${API_BASE}/api/todos`);
    const data = await res.json();
    renderTodos(data.tasks || []);
  });
});

// ── Toast notifications ───────────────────────────────────────
function showToast(msg, type = '') {
  const div = document.createElement('div');
  div.className = `toast${type === 'tool' ? ' toast-tool' : ''}`;
  div.textContent = msg;
  toastContainer.appendChild(div);
  setTimeout(() => div.remove(), 3500);
}

// ── Init: load data ───────────────────────────────────────────
async function init() {
  try {
    const [todosRes, memRes] = await Promise.all([
      fetch(`${API_BASE}/api/todos`),
      fetch(`${API_BASE}/api/memories`),
    ]);
    const todosData = await todosRes.json();
    const memData   = await memRes.json();
    renderTodos(todosData.tasks   || []);
    renderMemories(memData.memories || []);
  } catch(e) {
    showToast('⚠ Could not connect to backend. Is the server running?', 'error');
  }
  if (synth) synth.getVoices();
}

init();
