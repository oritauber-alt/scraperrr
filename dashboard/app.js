/* ── scraperrr ── app.js ─────────────────────────────────────────── */

const API_BASE = '';
const SAVED_KEY = 'scraperrr_saved';
const REFRESH_MS = 24 * 60 * 60 * 1000;

const SOURCE = {
  bens_bites: { color: '#C084FC', bg: 'rgba(192,132,252,0.1)', label: "Ben's Bites",    badgeClass: 'badge-bens'    },
  ai_rundown:  { color: '#60A5FA', bg: 'rgba(96,165,250,0.1)',  label: 'The AI Rundown', badgeClass: 'badge-rundown' },
  reddit:      { color: '#FB923C', bg: 'rgba(251,146,60,0.1)',  label: 'Reddit',         badgeClass: 'badge-reddit'  },
};

const TITLES = {
  all:        ['All Articles',        "Today's AI intelligence"],
  bens_bites: ["Ben's Bites",         'Newsletter · AI builders'],
  ai_rundown: ['The AI Rundown',      'Daily AI news briefing'],
  reddit:     ['Reddit',              'Top posts from AI communities'],
  saved:      ['Saved Articles',      'Your bookmarked reads'],
};

// ── State ─────────────────────────────────────────────────────────
let allArticles  = [];
let saved        = {};    // id → { saved_at, article }
let activeFilter = 'all';
let pillFilter   = 'all';
let isLoading    = false;

// ── DOM ────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const sidebarNav  = $('sidebarNav');
const grid        = $('articleGrid');
const heroWrap    = $('heroWrap');
const heroCard    = $('heroCard');
const heroEl      = $('heroCard');
const emptyState  = $('emptyState');
const emptyTitle  = $('emptyTitle');
const emptySub    = $('emptySub');
const pillsRow    = $('pillsRow');
const lastUpdated = $('lastUpdated');
const refreshBtn  = $('refreshBtn');
const refreshIcon = $('refreshIcon').querySelector ? $('refreshIcon') : document.querySelector('#refreshBtn svg');
const statusDot   = $('statusDot');
const statusLabel = $('statusLabel');
const pageTitle   = $('pageTitle');
const pageSubtitle= $('pageSubtitle');
const toast       = $('toast');
const countAll    = $('countAll');
const countBens   = $('countBens');
const countRundown= $('countRundown');
const countReddit = $('countReddit');
const countSaved  = $('countSaved');

// ── Saved ─────────────────────────────────────────────────────────
function loadSaved() {
  try { saved = JSON.parse(localStorage.getItem(SAVED_KEY) || '{}'); }
  catch { saved = {}; }
}

function persistSaved() {
  localStorage.setItem(SAVED_KEY, JSON.stringify(saved));
}

function toggleSave(article) {
  if (saved[article.id]) {
    delete saved[article.id];
    showToast('Removed from saved');
  } else {
    saved[article.id] = { saved_at: new Date().toISOString(), article };
    showToast('Article saved ◈');
  }
  persistSaved();
  updateCounts();
  renderView();
}

function updateCounts() {
  const counts = { bens_bites: 0, ai_rundown: 0, reddit: 0 };
  allArticles.forEach(a => { if (counts[a.source] !== undefined) counts[a.source]++; });

  // HeroBlock live stat
  const hbTotal = document.getElementById('hbTotal');
  if (hbTotal) hbTotal.textContent = allArticles.length || '—';

  countAll.textContent     = allArticles.length || '—';
  countBens.textContent    = counts.bens_bites || '—';
  countRundown.textContent = counts.ai_rundown || '—';
  countReddit.textContent  = counts.reddit || '—';

  const sv = Object.keys(saved).length;
  if (sv > 0) {
    countSaved.textContent = sv;
    countSaved.style.display = 'inline-block';
  } else {
    countSaved.style.display = 'none';
  }
}

// ── Filter ────────────────────────────────────────────────────────
function getArticles() {
  let base;
  if (activeFilter === 'saved') {
    base = Object.values(saved)
      .sort((a, b) => new Date(b.saved_at) - new Date(a.saved_at))
      .map(s => s.article);
  } else {
    base = activeFilter === 'all'
      ? allArticles
      : allArticles.filter(a => a.source === activeFilter);
  }

  if (activeFilter !== 'saved' && pillFilter !== 'all') {
    base = base.filter(a => a.source === pillFilter);
  }

  return base;
}

// ── Time ──────────────────────────────────────────────────────────
function timeAgo(iso) {
  if (!iso) return '';
  const s = Math.floor((Date.now() - new Date(iso)) / 1000);
  if (s < 60)    return 'just now';
  if (s < 3600)  return `${Math.floor(s/60)}m ago`;
  if (s < 86400) return `${Math.floor(s/3600)}h ago`;
  return `${Math.floor(s/86400)}d ago`;
}

// ── Render ────────────────────────────────────────────────────────
function renderView() {
  const articles = getArticles();

  // Hero
  const showHero = activeFilter !== 'saved' && articles.length > 0;
  if (showHero) {
    heroWrap.style.display = 'block';
    pillsRow.style.display = 'flex';
    renderHero(articles[0]);
    renderGrid(articles.slice(1));
  } else {
    heroWrap.style.display = 'none';
    pillsRow.style.display = activeFilter === 'saved' ? 'none' : 'flex';
    renderGrid(articles);
  }
}

function renderHero(article) {
  if (!article) return;
  const src = SOURCE[article.source] || SOURCE.bens_bites;
  const badgeClass = src.badgeClass;

  heroEl.innerHTML = `
    ${article.image_url
      ? `<img class="hero-bg" src="${esc(article.image_url)}" alt="" onerror="this.style.display='none'">`
      : ''
    }
    <div class="hero-gradient"></div>
    <div class="hero-body">
      <div class="hero-badges">
        <span class="badge ${badgeClass}">${esc(article.source_label || src.label)}</span>
        ${article.is_new ? '<span class="badge badge-new">New</span>' : ''}
      </div>
      <a class="hero-title" href="${esc(article.url)}" target="_blank" rel="noopener noreferrer">
        ${escHtml(article.title)}
      </a>
      ${article.summary
        ? `<p class="hero-summary">${escHtml(article.summary)}</p>`
        : ''
      }
      <div class="hero-footer">
        <span class="hero-time">${timeAgo(article.published_at)}</span>
        <a class="hero-cta" href="${esc(article.url)}" target="_blank" rel="noopener noreferrer">
          Read article →
        </a>
      </div>
    </div>`;
}

function renderGrid(articles) {
  grid.innerHTML = '';
  emptyState.style.display = 'none';

  if (articles.length === 0) {
    emptyState.style.display = 'flex';
    if (activeFilter === 'saved') {
      emptyTitle.textContent = 'No saved articles yet';
      emptySub.textContent   = 'Bookmark articles to save them here.';
    } else if (articles.length === 0 && allArticles.length === 0) {
      emptyTitle.textContent = 'Nothing new in the last 24 hours';
      emptySub.textContent   = 'Check back soon — the web will have new things to say.';
    } else {
      emptyTitle.textContent = `No articles from this source today`;
      emptySub.textContent   = 'Try another source or check back later.';
    }
    return;
  }

  const frag = document.createDocumentFragment();
  articles.forEach(a => frag.appendChild(makeCard(a)));
  grid.appendChild(frag);
}

function makeCard(article) {
  const src = SOURCE[article.source] || { color: '#BFF549', badgeClass: 'badge-new', label: article.source };
  const isSaved = !!saved[article.id];

  const card = document.createElement('div');
  card.className = 'card';
  card.dataset.id = article.id;

  card.innerHTML = `
    <div class="card-accent" style="background:${src.color}"></div>
    ${article.image_url
      ? `<img class="card-image" src="${esc(article.image_url)}" alt="" loading="lazy" onerror="this.style.display='none'">`
      : ''
    }
    <div class="card-body">
      <div class="card-header">
        <div class="card-badges">
          <span class="badge ${src.badgeClass}">${escHtml(article.source_label || src.label)}</span>
          ${article.is_new ? '<span class="badge badge-new">New</span>' : ''}
        </div>
        <button class="save-btn ${isSaved ? 'saved' : ''}" data-id="${esc(article.id)}" title="${isSaved ? 'Remove' : 'Save'}">
          ${bookmarkSvg(isSaved)}
        </button>
      </div>
      <a class="card-title" href="${esc(article.url)}" target="_blank" rel="noopener noreferrer">
        ${escHtml(article.title)}
      </a>
      ${article.summary
        ? `<p class="card-summary">${escHtml(article.summary)}</p>`
        : ''
      }
      <div class="card-footer">
        <span class="card-time">${timeAgo(article.published_at)}</span>
        <a class="card-read" href="${esc(article.url)}" target="_blank" rel="noopener noreferrer">Read →</a>
      </div>
    </div>`;

  card.querySelector('.save-btn').addEventListener('click', e => {
    e.stopPropagation();
    const btn = e.currentTarget;
    btn.classList.add('pop');
    btn.addEventListener('animationend', () => btn.classList.remove('pop'), { once: true });
    toggleSave(article);
  });

  return card;
}

function bookmarkSvg(filled) {
  return filled
    ? `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>`
    : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>`;
}

// ── Mobile sidebar toggle ────────────────────────────────────────
const sidebar         = document.querySelector('.sidebar');
const menuBtn         = document.getElementById('menuBtn');
const sidebarBackdrop = document.getElementById('sidebarBackdrop');

function openSidebar() {
  sidebar.classList.add('open');
  sidebarBackdrop.classList.add('visible');
  document.body.style.overflow = 'hidden';
}

function closeSidebar() {
  sidebar.classList.remove('open');
  sidebarBackdrop.classList.remove('visible');
  document.body.style.overflow = '';
}

menuBtn?.addEventListener('click', openSidebar);
sidebarBackdrop?.addEventListener('click', closeSidebar);

// ── Sidebar nav ───────────────────────────────────────────────────
document.querySelectorAll('.nav-item').forEach(btn => {
  btn.addEventListener('click', () => {
    activeFilter = btn.dataset.source;
    pillFilter   = 'all';
    document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.pill').forEach(p => p.classList.toggle('active', p.dataset.source === 'all'));
    const [title, sub] = TITLES[activeFilter] || TITLES.all;
    pageTitle.textContent    = title;
    pageSubtitle.textContent = sub;
    renderView();
    // Close drawer on mobile after selection
    closeSidebar();
  });
});

// ── Pills ─────────────────────────────────────────────────────────
document.getElementById('pillsRow').addEventListener('click', e => {
  const pill = e.target.closest('.pill');
  if (!pill) return;
  pillFilter = pill.dataset.source;
  document.querySelectorAll('.pill').forEach(p => p.classList.toggle('active', p === pill));
  renderView();
});

// ── Refresh ───────────────────────────────────────────────────────
refreshBtn.addEventListener('click', () => fetchArticles(true));
document.getElementById('heroRefreshBtn')?.addEventListener('click', () => fetchArticles(true));
setInterval(() => fetchArticles(true), REFRESH_MS);

// Update relative times every minute
setInterval(() => {
  document.querySelectorAll('[data-ts]').forEach(el => {
    el.textContent = timeAgo(el.dataset.ts);
  });
}, 60000);

// ── API ───────────────────────────────────────────────────────────
async function fetchArticles(force = false) {
  if (isLoading) return;
  isLoading = true;

  const icon = document.querySelector('#refreshBtn svg');
  if (icon) icon.classList.add('spinning');
  statusDot.className   = 'status-dot loading';
  statusLabel.textContent = 'Syncing...';

  const url = force ? `${API_BASE}/api/articles/refresh` : `${API_BASE}/api/articles`;

  try {
    const r = await fetch(url);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const data = await r.json();

    allArticles = data.articles || [];

    // Mark new vs seen
    const seen = new Set(JSON.parse(sessionStorage.getItem('s_seen') || '[]'));
    let newCount = 0;
    allArticles.forEach(a => {
      if (!seen.has(a.id)) { a.is_new = true; newCount++; }
      else { a.is_new = false; }
    });
    sessionStorage.setItem('s_seen', JSON.stringify(allArticles.map(a => a.id)));

    updateCounts();
    renderView();

    // Status
    statusDot.className     = 'status-dot ok';
    statusLabel.textContent = timeAgo(data.fetched_at);
    lastUpdated.textContent = `Updated ${timeAgo(data.fetched_at)}`;

    if (force && newCount > 0) showToast(`${newCount} new article${newCount > 1 ? 's' : ''}`);
    else if (force)            showToast('Already up to date');

  } catch (err) {
    console.error(err);
    statusDot.className     = 'status-dot error';
    statusLabel.textContent = 'Failed to load';
    showToast('Could not reach the server');
  } finally {
    isLoading = false;
    if (icon) icon.classList.remove('spinning');
  }
}

// ── Toast ─────────────────────────────────────────────────────────
let toastTimer;
function showToast(msg) {
  toast.textContent = msg;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 2800);
}

// ── Security ──────────────────────────────────────────────────────
function escHtml(s) {
  const d = document.createElement('div');
  d.appendChild(document.createTextNode(s || ''));
  return d.innerHTML;
}

function esc(s) {
  return (s || '').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

// ── Init ──────────────────────────────────────────────────────────
loadSaved();
updateCounts();
fetchArticles(false);
