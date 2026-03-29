// ── Theme ──────────────────────────────────────
const html = document.documentElement;
const saved = localStorage.getItem('theme') || 'light';
html.setAttribute('data-theme', saved);

document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.getElementById('themeToggle');
  if (toggle) {
    toggle.addEventListener('click', () => {
      const current = html.getAttribute('data-theme');
      const next = current === 'light' ? 'dark' : 'light';
      html.setAttribute('data-theme', next);
      localStorage.setItem('theme', next);
    });
  }

  // ── Search autocomplete ───────────────────────
  const input = document.getElementById('globalSearch');
  const suggestions = document.getElementById('searchSuggestions');

  if (input && suggestions) {
    let timer = null;

    input.addEventListener('input', () => {
      clearTimeout(timer);
      const q = input.value.trim();
      if (q.length < 2) { suggestions.classList.remove('visible'); return; }

      timer = setTimeout(async () => {
        try {
          const res = await fetch(`/api/search-suggest?q=${encodeURIComponent(q)}`);
          const data = await res.json();
          if (data.length === 0) { suggestions.classList.remove('visible'); return; }
          suggestions.innerHTML = data.map(item => `
            <div class="suggestion-item" onclick="window.location='${item.url}'">
              <span class="suggestion-badge ${item.type}">${item.type}</span>
              <span>${item.text}</span>
            </div>
          `).join('');
          suggestions.classList.add('visible');
        } catch (e) {
          suggestions.classList.remove('visible');
        }
      }, 250);
    });

    document.addEventListener('click', (e) => {
      if (!e.target.closest('.search-wrap')) suggestions.classList.remove('visible');
    });
  }

  // ── Vote button ───────────────────────────────
  const voteBtn = document.getElementById('voteBtn');
  if (voteBtn) {
    voteBtn.addEventListener('click', async () => {
      const appId = voteBtn.dataset.appId;
      try {
        const res = await fetch(`/application/${appId}/vote`, { method: 'POST' });
        const data = await res.json();
        voteBtn.classList.toggle('voted', data.voted);
        const countEl = document.getElementById('voteCount');
        if (countEl) countEl.textContent = data.vote_count;
        voteBtn.querySelector('.vote-label').textContent = data.voted ? 'Upvoted' : 'Upvote';
      } catch (e) {
        console.error('Vote failed', e);
      }
    });
  }

  // ── Comment like buttons ──────────────────────
  document.querySelectorAll('.comment-like-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const commentId = btn.dataset.commentId;
      try {
        const res = await fetch(`/comment/${commentId}/like`, { method: 'POST' });
        const data = await res.json();
        btn.querySelector('.like-count').textContent = data.likes;
      } catch (e) {}
    });
  });

  // ── Reply toggle ──────────────────────────────
  document.querySelectorAll('.reply-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const commentId = btn.dataset.commentId;
      const form = document.getElementById(`replyForm-${commentId}`);
      if (form) form.classList.toggle('visible');
    });
  });

  // ── Upload preview ────────────────────────────
  const imageInput = document.getElementById('imageInput');
  const imagePreview = document.getElementById('imagePreview');
  if (imageInput && imagePreview) {
    imageInput.addEventListener('change', () => {
      const file = imageInput.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = e => {
          imagePreview.src = e.target.result;
          imagePreview.style.display = 'block';
        };
        reader.readAsDataURL(file);
      }
    });
  }

  // ── Domain → Topic filter (Add Application) ───
  const domainSelect = document.getElementById('domainSelect');
  const topicSelect = document.getElementById('topicSelect');
  if (domainSelect && topicSelect) {
    domainSelect.addEventListener('change', async () => {
      const domainId = domainSelect.value;
      topicSelect.innerHTML = '<option value="">Loading...</option>';
      if (!domainId) { topicSelect.innerHTML = '<option value="">Select a domain first</option>'; return; }
      const res = await fetch(`/api/topics-by-domain/${domainId}`);
      const topics = await res.json();
      topicSelect.innerHTML = topics.length
        ? topics.map(t => `<option value="${t.id}">${t.name}</option>`).join('')
        : '<option value="">No topics in this domain</option>';
    });
  }

  // ── Report modal ──────────────────────────────
  const reportBtn = document.getElementById('reportBtn');
  const reportModal = document.getElementById('reportModal');
  const closeReport = document.getElementById('closeReport');
  if (reportBtn && reportModal) {
    reportBtn.addEventListener('click', () => reportModal.style.display = 'flex');
    closeReport.addEventListener('click', () => reportModal.style.display = 'none');
    reportModal.addEventListener('click', (e) => { if (e.target === reportModal) reportModal.style.display = 'none'; });
  }

  // ── Auto-dismiss flashes ──────────────────────
  document.querySelectorAll('.flash').forEach(el => {
    setTimeout(() => el.remove(), 5000);
  });
});
