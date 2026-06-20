import { escHtml } from './utils.js';
import { chatRequest } from './api.js';

const messagesEl  = document.getElementById('messages');
const inputEl     = document.getElementById('user-input');
const sendBtn     = document.getElementById('send-btn');
const typingEl    = document.getElementById('typing');
const ragDrawer   = document.getElementById('rag-debug-drawer');
const ragBody     = document.getElementById('rag-debug-body');
const ragClose    = document.getElementById('rag-debug-close');
const ragTitle    = document.getElementById('rag-debug-title');

const history = [];

export function renderSystem(text) {
  const el = document.createElement('div');
  el.className = 'msg-system';
  el.textContent = text;
  messagesEl.insertBefore(el, typingEl);
  scrollBottom();
}

// chunks=null → no RAG metadata (e.g. boot greeting); chunks=[] → RAG ran but nothing passed threshold
export function renderAgent(text, chunks = null) {
  const wrap   = document.createElement('div');
  wrap.className = 'msg-agent';

  const label  = document.createElement('div');
  label.className = 'label';
  label.textContent = '◈ AGENT';

  if (chunks !== null && chunks.length > 0) {
    const badge = document.createElement('span');
    badge.className = 'rag-badge rag-badge--hit';
    badge.textContent = `◈ ${chunks.length}`;
    badge.title = `${chunks.length} lore chunk(s) retrieved`;
    badge.style.cursor = 'pointer';
    label.appendChild(badge);
    wrap.dataset.chunks = JSON.stringify(chunks);
  }

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.innerHTML = marked.parse(text);
  wrap.appendChild(label);
  wrap.appendChild(bubble);
  messagesEl.insertBefore(wrap, typingEl);
  scrollBottom();
}

function renderUser(text) {
  const wrap = document.createElement('div');
  wrap.className = 'msg-user';
  wrap.innerHTML = `<div class="label">YOU ▶</div><div class="bubble">${escHtml(text)}</div>`;
  messagesEl.insertBefore(wrap, typingEl);
  scrollBottom();
}

function scrollBottom() { messagesEl.scrollTop = messagesEl.scrollHeight; }

export function showTyping()  { typingEl.classList.add('visible'); scrollBottom(); }
export function hideTyping()  { typingEl.classList.remove('visible'); }

export function setInputEnabled(enabled) {
  inputEl.disabled = !enabled;
  sendBtn.disabled = !enabled;
  if (enabled) inputEl.focus();
}

export function addToHistory(msg) {
  history.push(msg);
}

// ── RAG DEBUG DRAWER ──────────────────────────────────────────────────────────

function openRagDrawer(chunks) {
  const count = chunks.length;
  ragTitle.textContent = `◈ RAW DATA STREAM — ${count} CHUNK${count !== 1 ? 'S' : ''} RETRIEVED`;

  if (count === 0) {
    ragBody.innerHTML = '<div class="rag-empty">// NO LORE RETRIEVED — QUERY SCORED BELOW THRESHOLD //</div>';
  } else {
    ragBody.innerHTML = chunks.map(c => {
      const nl = c.indexOf('\n');
      const source = nl > -1 ? c.slice(1, nl - 1) : '?';
      const text   = nl > -1 ? c.slice(nl + 1).trim() : c;
      return `<div class="rag-chunk">
        <div class="rag-chunk-source">${escHtml(source)}</div>
        <div class="rag-chunk-text">${escHtml(text)}</div>
      </div>`;
    }).join('');
  }

  ragDrawer.classList.add('open');
}

function closeRagDrawer() {
  ragDrawer.classList.remove('open');
}

ragClose.addEventListener('click', closeRagDrawer);

// Open drawer only when clicking the RAG badge; close on anything else
messagesEl.addEventListener('click', e => {
  const badge = e.target.closest('.rag-badge');
  if (badge) {
    const msg = badge.closest('.msg-agent[data-chunks]');
    if (msg) openRagDrawer(JSON.parse(msg.dataset.chunks));
  } else {
    closeRagDrawer();
  }
});

// ── SEND ─────────────────────────────────────────────────────────────────────

async function sendMessage() {
  const text = inputEl.value.trim();
  if (!text) return;

  inputEl.value = '';
  setInputEnabled(false);

  const snapshot = [...history];
  history.push({ role: 'user', content: text });
  renderUser(text);
  showTyping();

  try {
    const res  = await chatRequest(text, snapshot);
    const data = await res.json();
    hideTyping();

    if (!res.ok) {
      renderSystem(`⚠ SIGNAL ERROR: ${data.detail ?? res.statusText}`);
      history.pop();
    } else {
      history.push({ role: 'assistant', content: data.response });
      renderAgent(data.response, data.lore_chunks ?? []);
    }
  } catch (err) {
    hideTyping();
    renderSystem(`⚠ CONNECTION LOST: ${err.message}`);
    history.pop();
  }

  setInputEnabled(true);
}

export function initChat() {
  sendBtn.addEventListener('click', sendMessage);
  inputEl.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });
}
