import { delay } from './utils.js';
import { initChat, renderSystem, renderAgent, showTyping, hideTyping, setInputEnabled, addToHistory } from './chat.js';
import { initNews } from './news.js';
import { initMarket } from './market.js';
import { initProfile } from './profile.js';
import { initGigs } from './gigs.js';
import { initShards } from './shards.js';
import { fetchGreeting } from './api.js';

// ── TAB ROUTING ───────────────────────────────────────────────────────────────

const VALID_TABS = new Set(['chat', 'news', 'market', 'gigs', 'profile', 'shards']);
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

  const FALLBACK = "Agent online. Jacked into CitiNet. State your query.";
  let opening = FALLBACK;
  try {
    const res = await fetchGreeting();
    if (res.ok) {
      const data = await res.json();
      if (data.greeting) opening = data.greeting;
    }
  } catch (_) {}

  hideTyping();
  addToHistory({ role: 'assistant', content: opening });
  renderAgent(opening);

  setInputEnabled(true);
  initProfile();
  initNews();
  initMarket();
  initGigs();
  initShards();
  activateTab(location.hash.slice(1) || 'chat');
}

boot();
