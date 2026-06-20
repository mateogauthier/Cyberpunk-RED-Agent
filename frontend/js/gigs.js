import { escHtml } from './utils.js';
import { GIG_ICONS } from './icons.js';
import { fetchGigs, generateGig } from './api.js';

const pullBtn  = document.getElementById('pull-gigs-btn');
const gigStatus = document.getElementById('gig-status');
const gigFeed   = document.getElementById('gig-feed');

const RISK_CLASS = {
  STREET:   'risk-street',
  STANDARD: 'risk-standard',
  PRIME:    'risk-prime',
  BLACK:    'risk-black',
};

function gigTimestamp(isoStr) {
  const d   = isoStr ? new Date(isoStr.replace(' ', 'T') + 'Z') : new Date();
  const pad = n => String(n).padStart(2, '0');
  return `${pad(d.getHours())}:${pad(d.getMinutes())} // ${d.getFullYear()}.${pad(d.getMonth() + 1)}.${pad(d.getDate())}`;
}

function formatPayout(payout) {
  return `€$ ${Number(payout ?? 0).toLocaleString('en-US')}`;
}

function renderGig(gig, prepend = true) {
  gigFeed.querySelector('.gig-empty-state')?.remove();

  const icon    = GIG_ICONS[gig.category] ?? GIG_ICONS.RECON ?? '';
  const riskKey = gig.risk ?? 'STREET';

  const card = document.createElement('article');
  card.className = 'gig-card';
  card.innerHTML = `
    <div class="gig-card-header">
      <span class="gig-location-tag">[ ${escHtml(gig.district ?? 'NIGHT CITY')} ]</span>
      <span class="gig-risk ${RISK_CLASS[riskKey] ?? ''}">${escHtml(riskKey)}</span>
      <span class="gig-timestamp">${gigTimestamp(gig.created_at ?? null)}</span>
    </div>
    <div class="gig-card-body">
      <div class="gig-image-slot">${icon}</div>
      <div class="gig-content">
        <h2 class="gig-title">${escHtml(gig.title ?? 'POSTING')}</h2>
        <div class="gig-meta">VIA: ${escHtml(gig.fixer ?? 'ANONYMOUS')} // ${escHtml(gig.category ?? '')}</div>
        <div class="gig-description">${escHtml(gig.description ?? '')}</div>
        ${gig.requirements ? `<div class="gig-requirements">REQ: ${escHtml(gig.requirements)}</div>` : ''}
        <div class="gig-footer">
          <div class="gig-contact">CONTACT: ${escHtml(gig.contact ?? 'UNKNOWN')}</div>
          <div class="gig-payout">${escHtml(formatPayout(gig.payout))}</div>
        </div>
      </div>
    </div>
  `;

  gigFeed.insertBefore(card, prepend ? gigFeed.firstChild : null);
}

async function loadGigs() {
  try {
    const res = await fetchGigs();
    if (!res.ok) return;
    const gigs = await res.json();
    [...gigs].reverse().forEach(g => renderGig(g, false));
  } catch (_) {}
}

async function pullGig() {
  pullBtn.disabled = true;
  gigStatus.textContent = '[ SCANNING FIXER CHANNELS... ]';

  try {
    const res  = await generateGig();
    const data = await res.json();
    if (!res.ok) {
      gigStatus.textContent = `⚠ BOARD ERROR: ${data.detail ?? res.statusText}`;
    } else {
      renderGig(data);
      gigStatus.textContent = '';
    }
  } catch (err) {
    gigStatus.textContent = `⚠ SIGNAL LOST: ${err.message}`;
  } finally {
    pullBtn.disabled = false;
  }
}

export function initGigs() {
  pullBtn.addEventListener('click', pullGig);
  loadGigs();
}
