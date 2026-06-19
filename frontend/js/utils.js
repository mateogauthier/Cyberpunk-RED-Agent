export const escHtml = s =>
  s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

export const delay = ms => new Promise(r => setTimeout(r, ms));
