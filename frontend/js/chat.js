import { escHtml } from './utils.js';
import { chatRequest } from './api.js';

const messagesEl = document.getElementById('messages');
const inputEl    = document.getElementById('user-input');
const sendBtn    = document.getElementById('send-btn');
const typingEl   = document.getElementById('typing');

const history = [];

export function renderSystem(text) {
  const el = document.createElement('div');
  el.className = 'msg-system';
  el.textContent = text;
  messagesEl.insertBefore(el, typingEl);
  scrollBottom();
}

export function renderAgent(text) {
  const wrap   = document.createElement('div');
  wrap.className = 'msg-agent';
  const label  = document.createElement('div');
  label.className = 'label';
  label.textContent = '◈ AGENT';
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
      renderAgent(data.response);
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
