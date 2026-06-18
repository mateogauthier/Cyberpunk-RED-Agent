const messagesEl = document.getElementById('messages');
const inputEl    = document.getElementById('user-input');
const sendBtn    = document.getElementById('send-btn');
const typingEl   = document.getElementById('typing');

const history = [];

// ── RENDER HELPERS ──────────────────────────────────────────────────────────

function renderSystem(text) {
  const el = document.createElement('div');
  el.className = 'msg-system';
  el.textContent = text;
  messagesEl.insertBefore(el, typingEl);
  scrollBottom();
}

function renderAgent(text) {
  const wrap = document.createElement('div');
  wrap.className = 'msg-agent';
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.innerHTML = marked.parse(text);
  const label = document.createElement('div');
  label.className = 'label';
  label.textContent = '◈ AGENT';
  wrap.appendChild(label);
  wrap.appendChild(bubble);
  messagesEl.insertBefore(wrap, typingEl);
  scrollBottom();
}

function renderUser(text) {
  const wrap = document.createElement('div');
  wrap.className = 'msg-user';
  wrap.innerHTML = `
    <div class="label">YOU ▶</div>
    <div class="bubble">${escHtml(text)}</div>
  `;
  messagesEl.insertBefore(wrap, typingEl);
  scrollBottom();
}

function showTyping()  { typingEl.classList.add('visible');    scrollBottom(); }
function hideTyping()  { typingEl.classList.remove('visible'); }
function scrollBottom(){ messagesEl.scrollTop = messagesEl.scrollHeight; }
function escHtml(s)    { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function delay(ms)     { return new Promise(r => setTimeout(r, ms)); }

function setInputEnabled(enabled) {
  inputEl.disabled = !enabled;
  sendBtn.disabled = !enabled;
  if (enabled) inputEl.focus();
}

// ── SEND ────────────────────────────────────────────────────────────────────

async function sendMessage() {
  const text = inputEl.value.trim();
  if (!text) return;

  inputEl.value = '';
  setInputEnabled(false);

  const outgoingHistory = [...history];
  history.push({ role: 'user', content: text });
  renderUser(text);
  showTyping();

  try {
    const res  = await fetch('/chat', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ message: text, history: outgoingHistory }),
    });
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

// ── BOOT SEQUENCE ────────────────────────────────────────────────────────────

const BOOT_LINES = [
  '[ INITIALIZING SAAI CORE... ]',
  '[ LOADING PERSONALITY MATRIX... ]',
  '[ CONNECTING TO ZIGGURAT CITINET... ]',
  '[ DATA POOL ACCESS: ESTABLISHED ]',
  '[ THE GARDEN: SYNCED ]',
  '[ AGENT INTERFACE READY ]',
];

async function boot() {
  for (const line of BOOT_LINES) {
    await delay(380);
    renderSystem(line);
  }
  await delay(500);

  showTyping();
  await delay(900);
  hideTyping();

  const opening = "Agent online. I'm your dedicated SAAI interface — jacked into Ziggurat's CitiNet, the Data Pool, and The Garden. Everything Night City's grid can pull, I can reach. State your query.";
  history.push({ role: 'assistant', content: opening });
  renderAgent(opening);

  setInputEnabled(true);
}

// ── EVENT LISTENERS ──────────────────────────────────────────────────────────

sendBtn.addEventListener('click', sendMessage);
inputEl.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});

boot();
