import { delay } from './utils.js';
import { initChat, renderSystem, renderAgent, showTyping, hideTyping, setInputEnabled, addToHistory } from './chat.js';
import { initNews } from './news.js';
import { initProfile } from './profile.js';

// ── TAB ROUTING ───────────────────────────────────────────────────────────────

const VALID_TABS = new Set(['chat', 'news', 'profile']);
const deckTrack  = document.getElementById('deck-track');

function activateTab(name) {
  const tab = VALID_TABS.has(name) ? name : 'chat';
  document.querySelectorAll('.tab-btn').forEach(
    btn => btn.classList.toggle('active', btn.dataset.tab === tab)
  );
  document.querySelectorAll('.tab-panel').forEach(
    p => p.classList.toggle('active', p.id === `panel-${tab}`)
  );
}

deckTrack.addEventListener('click', e => {
  const btn = e.target.closest('.tab-btn');
  if (btn) location.hash = btn.dataset.tab;
});

window.addEventListener('hashchange', () => activateTab(location.hash.slice(1) || 'chat'));

// ── BOOT SEQUENCE ─────────────────────────────────────────────────────────────

const BOOT_LINES = [
  '[ INITIALIZING SAAI CORE... ]',
  '[ LOADING PERSONALITY MATRIX... ]',
  '[ CONNECTING TO ZIGGURAT CITINET... ]',
  '[ DATA POOL ACCESS: ESTABLISHED ]',
  '[ THE GARDEN: SYNCED ]',
  '[ AGENT INTERFACE READY ]',
];

async function boot() {
  initChat();

  for (const line of BOOT_LINES) {
    await delay(380);
    renderSystem(line);
  }

  await delay(500);
  showTyping();
  await delay(900);
  hideTyping();

  const opening = "Agent online. I'm your dedicated SAAI interface — jacked into Ziggurat's CitiNet, the Data Pool, and The Garden. Everything Night City's grid can pull, I can reach. State your query.";
  addToHistory({ role: 'assistant', content: opening });
  renderAgent(opening);

  setInputEnabled(true);
  initProfile();
  initNews();
  activateTab(location.hash.slice(1) || 'chat');
}

boot();
