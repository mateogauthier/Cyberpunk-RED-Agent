import { escHtml } from './utils.js';
import { CATEGORY_ICONS } from './icons.js';
import { fetchNews, generateNews } from './api.js';

const genNewsBtn = document.getElementById('generate-news-btn');
const newsStatus = document.getElementById('news-status');
const newsFeed   = document.getElementById('news-feed');

function newsTimestamp(isoStr) {
  const d   = isoStr ? new Date(isoStr.replace(' ', 'T') + 'Z') : new Date();
  const pad = n => String(n).padStart(2, '0');
  return `${pad(d.getHours())}:${pad(d.getMinutes())} // ${d.getFullYear()}.${pad(d.getMonth() + 1)}.${pad(d.getDate())}`;
}

function renderCard(article, prepend = true) {
  newsFeed.querySelector('.news-empty-state')?.remove();

  const icon     = CATEGORY_ICONS[article.category] ?? CATEGORY_ICONS.GENERAL ?? '';
  const bodyHtml = (article.body ?? '').split(/\n\n+/).map(p => `<p>${escHtml(p.trim())}</p>`).join('');

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

  newsFeed.insertBefore(card, prepend ? newsFeed.firstChild : null);
}

async function loadFeed() {
  try {
    const res = await fetchNews();
    if (!res.ok) return;
    const articles = await res.json();
    [...articles].reverse().forEach(a => renderCard(a));
  } catch (_) {}
}

async function generateArticle() {
  genNewsBtn.disabled = true;
  newsStatus.textContent = '[ PULLING FROM DATA POOLS... ]';

  try {
    const res  = await generateNews();
    const data = await res.json();
    if (!res.ok) {
      newsStatus.textContent = `⚠ FEED ERROR: ${data.detail ?? res.statusText}`;
    } else {
      renderCard(data);
      newsStatus.textContent = '';
    }
  } catch (err) {
    newsStatus.textContent = `⚠ SIGNAL LOST: ${err.message}`;
  } finally {
    genNewsBtn.disabled = false;
  }
}

export function initNews() {
  genNewsBtn.addEventListener('click', generateArticle);
  loadFeed();
}
