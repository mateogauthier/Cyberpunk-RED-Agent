import { fetchProfile, saveProfile } from './api.js';

const profileForm = document.getElementById('profile-form');
const handleInput = document.getElementById('profile-handle');
const roleSelect  = document.getElementById('profile-role');
const bioArea     = document.getElementById('profile-bio');
const saveBtn     = document.getElementById('profile-save-btn');
const avatarBox   = document.getElementById('profile-avatar');
const avatarLabel = document.getElementById('avatar-label');
const silhouette  = avatarBox.querySelector('.silhouette-svg');

const STATS = [
  { key: 'stat_int',  label: 'INT'  },
  { key: 'stat_ref',  label: 'REF'  },
  { key: 'stat_tech', label: 'TECH' },
  { key: 'stat_cool', label: 'COOL' },
  { key: 'stat_will', label: 'WILL' },
  { key: 'stat_luck', label: 'LUCK' },
  { key: 'stat_move', label: 'MOVE' },
  { key: 'stat_body', label: 'BODY' },
  { key: 'stat_emp',  label: 'EMP'  },
];

const profile = {
  handle: '', role: '', bio: '', avatar_url: '',
  stat_int: 5, stat_ref: 5, stat_tech: 5, stat_cool: 5,
  stat_will: 5, stat_luck: 5, stat_move: 5, stat_body: 5,
  stat_emp: 5, humanity_current: 50,
};

// ── AVATAR ────────────────────────────────────────────────────────────────────

function setAvatarDisplay(url) {
  const existing = avatarBox.querySelector('img');
  if (existing) existing.remove();
  if (url) {
    silhouette.hidden = true;
    avatarBox.classList.add('has-image');
    const img = document.createElement('img');
    img.src = url;
    img.alt = '';
    avatarBox.appendChild(img);
    avatarLabel.textContent = '[ CLICK TO CHANGE ]';
  } else {
    silhouette.hidden = false;
    avatarBox.classList.remove('has-image');
    avatarLabel.textContent = '[ CLICK TO SET IMAGE ]';
  }
}

function promptAvatar() {
  const url = window.prompt('IMAGE URL:', profile.avatar_url);
  if (url === null) return;
  profile.avatar_url = url.trim();
  setAvatarDisplay(profile.avatar_url);
}

// ── STATS GRID ────────────────────────────────────────────────────────────────

function wireStatsGrid() {
  document.getElementById('stats-grid').addEventListener('click', e => {
    const btn = e.target.closest('.stat-btn');
    if (!btn) return;
    const { key, delta } = btn.dataset;
    profile[key] = Math.min(10, Math.max(1, profile[key] + Number(delta)));
    document.getElementById(`sv-${key}`).textContent = profile[key];
    if (key === 'stat_emp') {
      const max = profile.stat_emp * 10;
      if (profile.humanity_current > max) profile.humanity_current = max;
      updateHumanityUI();
    }
  });
}

function syncStatDisplays() {
  STATS.forEach(({ key }) => {
    const el = document.getElementById(`sv-${key}`);
    if (el) el.textContent = profile[key];
  });
}

// ── HUMANITY ──────────────────────────────────────────────────────────────────

function humanityState(current, max) {
  if (current <= 0)           return { label: 'CYBERPSYCHO', cls: 'state-cyberpsycho' };
  const pct = max > 0 ? current / max : 0;
  if (pct < 0.20)             return { label: 'CRITICAL',    cls: 'state-critical'    };
  if (pct < 0.50)             return { label: 'FRACTURED',   cls: 'state-fractured'   };
  if (pct < 0.80)             return { label: 'STRESSED',    cls: 'state-stressed'    };
  if (pct < 1.00)             return { label: 'STABLE',      cls: 'state-stable'      };
  return                             { label: 'INTACT',      cls: 'state-intact'      };
}

function updateHumanityUI() {
  const max = profile.stat_emp * 10;
  const cur = Math.min(Math.max(0, profile.humanity_current), max);
  const pct = max > 0 ? (cur / max) * 100 : 0;
  const state = humanityState(cur, max);

  const bar = document.getElementById('humanity-bar');
  bar.style.width = `${pct}%`;
  bar.className = `humanity-bar ${state.cls}`;

  document.getElementById('humanity-current-val').textContent = cur;
  document.getElementById('humanity-max-val').textContent = max;
  document.getElementById('emp-effective').textContent = Math.max(0, Math.floor(cur / 10));

  const stateEl = document.getElementById('humanity-state');
  stateEl.textContent = state.label;
  stateEl.className = `humanity-state-badge ${state.cls}`;
}

async function adjustHumanity(delta) {
  const step = parseInt(document.getElementById('humanity-step').value, 10) || 1;
  const max = profile.stat_emp * 10;
  profile.humanity_current = Math.min(max, Math.max(0, profile.humanity_current + delta * step));
  updateHumanityUI();
  try { await saveProfile(profile); } catch (_) {}
}

async function resetHumanity() {
  profile.humanity_current = profile.stat_emp * 10;
  updateHumanityUI();
  try { await saveProfile(profile); } catch (_) {}
}

// ── LOAD / SAVE ───────────────────────────────────────────────────────────────

async function loadProfile() {
  try {
    const res = await fetchProfile();
    if (!res.ok) return;
    const data = await res.json();
    Object.assign(profile, data);
    handleInput.value = data.handle || '';
    roleSelect.value  = data.role   || '';
    bioArea.value     = data.bio    || '';
    setAvatarDisplay(data.avatar_url ?? '');
    syncStatDisplays();
    updateHumanityUI();
  } catch (_) {}
}

async function onSubmit(e) {
  e.preventDefault();
  profile.handle = handleInput.value.trim();
  profile.role   = roleSelect.value;
  profile.bio    = bioArea.value.trim();
  saveBtn.disabled = true;
  try {
    const res = await saveProfile(profile);
    saveBtn.textContent = res.ok ? '◈ RECORD COMMITTED ◈' : '⚠ SAVE FAILED';
  } catch (_) {
    saveBtn.textContent = '⚠ CONNECTION LOST';
  }
  saveBtn.disabled = false;
  setTimeout(() => { saveBtn.textContent = '◈ COMMIT TO RECORD ◈'; }, 2000);
}

export function initProfile() {
  wireStatsGrid();
  updateHumanityUI();
  profileForm.addEventListener('submit', onSubmit);
  avatarBox.addEventListener('click', promptAvatar);
  avatarBox.addEventListener('keydown', e => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); promptAvatar(); }
  });
  document.getElementById('humanity-lose-btn').addEventListener('click', () => adjustHumanity(-1));
  document.getElementById('humanity-restore-btn').addEventListener('click', () => adjustHumanity(1));
  document.getElementById('humanity-full-btn').addEventListener('click', resetHumanity);
  loadProfile();
}
