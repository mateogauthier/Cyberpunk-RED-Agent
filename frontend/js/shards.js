import { escHtml } from './utils.js';
import { fetchShards, extractShards } from './api.js';

const extractBtn     = document.getElementById('extract-shards-btn');
const shardsStatus   = document.getElementById('shards-status');
const corpSection    = document.getElementById('shards-corps');
const distSection    = document.getElementById('shards-districts');
const factionSection = document.getElementById('shards-factions');

const SECTION_META = {
  corporations: { el: () => corpSection,    empty: '// NO CORPORATE DATA — RUN EXTRACTION //' },
  districts:    { el: () => distSection,    empty: '// NO DISTRICT DATA — RUN EXTRACTION //' },
  factions:     { el: () => factionSection, empty: '// NO FACTION DATA — RUN EXTRACTION //' },
};

function initSubtabs() {
  const tabs   = document.querySelectorAll('#panel-shards .shards-subtab');
  const panels = document.querySelectorAll('.shards-category-panel');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      panels.forEach(p => p.classList.remove('active'));
      tab.classList.add('active');
      document.getElementById(tab.dataset.target).classList.add('active');
    });
  });
}

function renderEntityCard(entity) {
  const card = document.createElement('div');
  card.className = 'shard-card';
  card.innerHTML = `
    <button class="shard-card-header" aria-expanded="false">
      <span class="shard-name">${escHtml(entity.name)}</span>
      <span class="shard-chevron">▶</span>
    </button>
    <div class="shard-card-body" hidden>
      <p class="shard-desc">${escHtml(entity.description)}</p>
    </div>
  `;
  const header = card.querySelector('.shard-card-header');
  const body   = card.querySelector('.shard-card-body');
  header.addEventListener('click', () => {
    const expanded = header.getAttribute('aria-expanded') === 'true';
    header.setAttribute('aria-expanded', String(!expanded));
    body.hidden = expanded;
  });
  return card;
}

function renderSection(key, items) {
  const meta = SECTION_META[key];
  const el = meta.el();
  el.innerHTML = '';

  if (items.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'shard-empty-state';
    empty.textContent = meta.empty;
    el.appendChild(empty);
    return;
  }

  items.forEach(entity => el.appendChild(renderEntityCard(entity)));
}

async function loadShards() {
  try {
    const res = await fetchShards();
    if (!res.ok) return;
    const data = await res.json();
    renderSection('corporations', data.corporations ?? []);
    renderSection('districts',    data.districts    ?? []);
    renderSection('factions',     data.factions     ?? []);
  } catch (_) {}
}

async function triggerExtraction() {
  extractBtn.disabled = true;
  shardsStatus.textContent = '[ SCANNING LORE — THIS TAKES ~60–90 SECONDS... ]';

  try {
    const res  = await extractShards();
    const data = await res.json();
    if (!res.ok) {
      shardsStatus.textContent = `⚠ EXTRACTION ERROR: ${data.detail ?? res.statusText}`;
    } else {
      const { counts } = data;
      shardsStatus.textContent =
        `[ EXTRACTED — CORPS: ${counts.CORPORATION ?? 0}  DISTRICTS: ${counts.DISTRICT ?? 0}  FACTIONS: ${counts.FACTION ?? 0} ]`;
      await loadShards();
    }
  } catch (err) {
    shardsStatus.textContent = `⚠ SIGNAL LOST: ${err.message}`;
  } finally {
    extractBtn.disabled = false;
  }
}

export function initShards() {
  initSubtabs();
  extractBtn.addEventListener('click', triggerExtraction);
  loadShards();
}
