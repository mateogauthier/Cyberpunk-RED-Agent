const messagesEl = document.getElementById('messages');
const inputEl    = document.getElementById('user-input');
const sendBtn    = document.getElementById('send-btn');
const typingEl   = document.getElementById('typing');

// Tab elements
const deckTrack   = document.getElementById('deck-track');
const tabBtns     = document.querySelectorAll('.tab-btn');
const tabPanels   = document.querySelectorAll('.tab-panel');

// News elements
const genNewsBtn  = document.getElementById('generate-news-btn');
const newsStatus  = document.getElementById('news-status');
const newsFeed    = document.getElementById('news-feed');

// Profile elements
const profileForm = document.getElementById('profile-form');

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

// ── TAB ROUTING (hash-based) ──────────────────────────────────────────────────

const VALID_TABS = new Set(['chat', 'map', 'news', 'profile']);

function activateTab(tabName) {
  const tab = VALID_TABS.has(tabName) ? tabName : 'chat';
  tabBtns.forEach(btn => btn.classList.toggle('active', btn.dataset.tab === tab));
  tabPanels.forEach(p => p.classList.toggle('active', p.id === `panel-${tab}`));
}

function currentTab() {
  return location.hash.slice(1) || 'chat';
}

deckTrack.addEventListener('click', e => {
  const btn = e.target.closest('.tab-btn');
  if (btn) location.hash = btn.dataset.tab;
});

window.addEventListener('hashchange', () => activateTab(currentTab()));

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

// ── NEWS ─────────────────────────────────────────────────────────────────────

function newsTimestamp(isoStr) {
  const d = isoStr
    ? new Date(isoStr.replace(' ', 'T') + 'Z')
    : new Date();
  const hh = String(d.getHours()).padStart(2, '0');
  const mm = String(d.getMinutes()).padStart(2, '0');
  const yy = d.getFullYear();
  const mo = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${hh}:${mm} // ${yy}.${mo}.${dd}`;
}

function renderNewsCard(article, append = false) {
  const emptyState = newsFeed.querySelector('.news-empty-state');
  if (emptyState) emptyState.remove();

  const icon = (typeof CATEGORY_ICONS !== 'undefined' && CATEGORY_ICONS[article.category])
    ? CATEGORY_ICONS[article.category]
    : (typeof CATEGORY_ICONS !== 'undefined' ? CATEGORY_ICONS['GENERAL'] : '');

  const bodyHtml = (article.body ?? '')
    .split(/\n\n+/)
    .map(p => `<p>${escHtml(p.trim())}</p>`)
    .join('');

  const card = document.createElement('article');
  card.className = 'news-card';
  card.innerHTML = `
    <div class="news-card-header">
      <span class="news-district-tag">[ ${escHtml(article.district ?? 'NIGHT CITY')} ]</span>
      <span class="news-timestamp">${newsTimestamp(article.created_at ?? null)}</span>
    </div>
    <div class="news-card-body">
      <div class="news-image-slot">${icon}</div>
      <div class="news-content">
        <h2 class="news-title">${escHtml(article.title ?? 'UNTITLED')}</h2>
        <div class="news-byline">BY: ${escHtml(article.byline ?? 'ANON GONK')} // NIGHT CITY NET</div>
        <div class="news-body">${bodyHtml}</div>
      </div>
    </div>
  `;

  if (append) {
    newsFeed.appendChild(card);
  } else {
    newsFeed.insertBefore(card, newsFeed.firstChild);
  }
}

async function loadNews() {
  try {
    const res = await fetch('/news');
    if (!res.ok) return;
    const articles = await res.json();
    // API returns newest-first; reverse so we prepend oldest→newest, leaving newest on top
    [...articles].reverse().forEach(a => renderNewsCard(a));
  } catch (_) { /* server unreachable on load */ }
}

async function generateNews() {
  genNewsBtn.disabled = true;
  newsStatus.textContent = '[ PULLING FROM DATA POOLS... ]';

  try {
    const res  = await fetch('/news', { method: 'POST' });
    const data = await res.json();

    if (!res.ok) {
      newsStatus.textContent = `⚠ FEED ERROR: ${data.detail ?? res.statusText}`;
    } else {
      renderNewsCard(data);
      newsStatus.textContent = '';
    }
  } catch (err) {
    newsStatus.textContent = `⚠ SIGNAL LOST: ${err.message}`;
  } finally {
    genNewsBtn.disabled = false;
  }
}

genNewsBtn.addEventListener('click', generateNews);

// ── PROFILE ──────────────────────────────────────────────────────────────────

const profile = { handle: '', role: '', bio: '' };

async function loadProfile() {
  try {
    const res = await fetch('/profile');
    if (!res.ok) return;
    const data = await res.json();
    Object.assign(profile, data);
    if (data.handle) document.getElementById('profile-handle').value = data.handle;
    if (data.role)   document.getElementById('profile-role').value   = data.role;
    if (data.bio)    document.getElementById('profile-bio').value    = data.bio;
  } catch (_) { /* server unreachable */ }
}

async function saveProfile(e) {
  e.preventDefault();
  profile.handle = document.getElementById('profile-handle').value.trim();
  profile.role   = document.getElementById('profile-role').value;
  profile.bio    = document.getElementById('profile-bio').value.trim();

  const btn = document.getElementById('profile-save-btn');
  btn.disabled = true;

  try {
    const res = await fetch('/profile', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(profile),
    });
    btn.textContent = res.ok ? '◈ RECORD COMMITTED ◈' : '⚠ SAVE FAILED';
  } catch (_) {
    btn.textContent = '⚠ CONNECTION LOST';
  }

  btn.disabled = false;
  setTimeout(() => { btn.textContent = '◈ COMMIT TO RECORD ◈'; }, 2000);
}

profileForm.addEventListener('submit', saveProfile);

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
  loadProfile();
  loadNews();
  activateTab(currentTab());
}

// ── EVENT LISTENERS ──────────────────────────────────────────────────────────

sendBtn.addEventListener('click', sendMessage);
inputEl.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});

boot();
