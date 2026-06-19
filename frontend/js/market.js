import { escHtml } from './utils.js';
import { MARKET_ICONS } from './icons.js';
import { fetchMarket, generateMarket } from './api.js';

const scoutBtn     = document.getElementById('scout-market-btn');
const marketStatus = document.getElementById('market-status');
const marketFeed   = document.getElementById('market-feed');

const RARITY_CLASS = { COMMON: 'rarity-common', UNCOMMON: 'rarity-uncommon', RARE: 'rarity-rare', LEGENDARY: 'rarity-legendary' };
const COND_CLASS   = { NEW: 'cond-new', USED: 'cond-used', HOT: 'cond-hot', SALVAGE: 'cond-salvage' };

function marketTimestamp(isoStr) {
  const d   = isoStr ? new Date(isoStr.replace(' ', 'T') + 'Z') : new Date();
  const pad = n => String(n).padStart(2, '0');
  return `${pad(d.getHours())}:${pad(d.getMinutes())} // ${d.getFullYear()}.${pad(d.getMonth() + 1)}.${pad(d.getDate())}`;
}

function formatPrice(price) {
  return `€$ ${Number(price ?? 0).toLocaleString('en-US')}`;
}

function renderListing(item, prepend = true) {
  marketFeed.querySelector('.market-empty-state')?.remove();

  const icon      = MARKET_ICONS[item.category] ?? MARKET_ICONS.TECH ?? '';
  const rarityKey = item.rarity ?? 'COMMON';
  const condKey   = item.condition ?? 'USED';

  const card = document.createElement('article');
  card.className = 'market-card';
  card.innerHTML = `
    <div class="market-card-header">
      <span class="market-district-tag">[ ${escHtml(item.district ?? 'NIGHT CITY')} ]</span>
      <div class="market-badges">
        <span class="market-rarity ${RARITY_CLASS[rarityKey] ?? ''}">${escHtml(rarityKey)}</span>
        <span class="market-condition ${COND_CLASS[condKey] ?? ''}">${escHtml(condKey)}</span>
      </div>
      <span class="market-timestamp">${marketTimestamp(item.created_at ?? null)}</span>
    </div>
    <div class="market-card-body">
      <div class="market-image-slot">${icon}</div>
      <div class="market-content">
        <h2 class="market-name">${escHtml(item.name ?? 'UNKNOWN ITEM')}</h2>
        <div class="market-meta">VIA: ${escHtml(item.seller ?? 'ANONYMOUS')} // ${escHtml(item.category ?? '')}</div>
        <div class="market-description">${escHtml(item.description ?? '')}</div>
        <div class="market-price-row">
          <span class="market-price">${escHtml(formatPrice(item.price))}</span>
        </div>
      </div>
    </div>
  `;

  marketFeed.insertBefore(card, prepend ? marketFeed.firstChild : null);
}

async function loadListings() {
  try {
    const res = await fetchMarket();
    if (!res.ok) return;
    const items = await res.json();
    [...items].reverse().forEach(i => renderListing(i, false));
  } catch (_) {}
}

async function scoutMarkets() {
  scoutBtn.disabled = true;
  marketStatus.textContent = '[ CONTACTING FIXER NETWORK... ]';

  try {
    const res  = await generateMarket();
    const data = await res.json();
    if (!res.ok) {
      marketStatus.textContent = `⚠ NETWORK ERROR: ${data.detail ?? res.statusText}`;
    } else {
      renderListing(data);
      marketStatus.textContent = '';
    }
  } catch (err) {
    marketStatus.textContent = `⚠ SIGNAL LOST: ${err.message}`;
  } finally {
    scoutBtn.disabled = false;
  }
}

export function initMarket() {
  scoutBtn.addEventListener('click', scoutMarkets);
  loadListings();
}
