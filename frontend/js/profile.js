import { fetchProfile, saveProfile } from './api.js';

const profileForm = document.getElementById('profile-form');
const handleInput = document.getElementById('profile-handle');
const roleSelect  = document.getElementById('profile-role');
const bioArea     = document.getElementById('profile-bio');
const saveBtn     = document.getElementById('profile-save-btn');

const profile = { handle: '', role: '', bio: '' };

async function loadProfile() {
  try {
    const res = await fetchProfile();
    if (!res.ok) return;
    const data = await res.json();
    Object.assign(profile, data);
    if (data.handle) handleInput.value = data.handle;
    if (data.role)   roleSelect.value  = data.role;
    if (data.bio)    bioArea.value     = data.bio;
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
  loadProfile();
}
