import { fetchProfile, saveProfile } from './api.js';

const profileForm = document.getElementById('profile-form');
const handleInput = document.getElementById('profile-handle');
const roleSelect  = document.getElementById('profile-role');
const bioArea     = document.getElementById('profile-bio');
const saveBtn     = document.getElementById('profile-save-btn');
const avatarBox   = document.getElementById('profile-avatar');
const avatarLabel = document.getElementById('avatar-label');
const silhouette  = avatarBox.querySelector('.silhouette-svg');

const profile = { handle: '', role: '', bio: '', avatar_url: '' };

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

async function loadProfile() {
  try {
    const res = await fetchProfile();
    if (!res.ok) return;
    const data = await res.json();
    Object.assign(profile, data);
    if (data.handle)     handleInput.value = data.handle;
    if (data.role)       roleSelect.value  = data.role;
    if (data.bio)        bioArea.value     = data.bio;
    setAvatarDisplay(data.avatar_url ?? '');
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
  profileForm.addEventListener('submit', onSubmit);
  avatarBox.addEventListener('click', promptAvatar);
  avatarBox.addEventListener('keydown', e => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); promptAvatar(); }
  });
  loadProfile();
}
