const HEADERS = { 'Content-Type': 'application/json' };

export const chatRequest  = (message, history) =>
  fetch('/chat', { method: 'POST', headers: HEADERS, body: JSON.stringify({ message, history }) });

export const fetchNews    = () => fetch('/news');
export const generateNews = () => fetch('/news', { method: 'POST' });
export const fetchMarket    = () => fetch('/market');
export const generateMarket = () => fetch('/market', { method: 'POST' });
export const fetchGigs      = () => fetch('/gigs');
export const generateGig    = () => fetch('/gigs', { method: 'POST' });
export const fetchGreeting  = () => fetch('/greeting');
export const fetchProfile   = () => fetch('/profile');

export const saveProfile  = profile =>
  fetch('/profile', { method: 'POST', headers: HEADERS, body: JSON.stringify(profile) });
