// TaskFlow — Main JS

document.addEventListener('DOMContentLoaded', function () {

  // ── Auto-dismiss alerts ──────────────────────────────────────
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.opacity = '0';
      alert.style.transform = 'translateX(20px)';
      alert.style.transition = 'all 0.4s ease';
      setTimeout(() => alert.remove(), 400);
    }, 4000);

    const closeBtn = alert.querySelector('.alert-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 300);
      });
    }
  });

  // ── Active nav item ──────────────────────────────────────────
  const currentPath = window.location.pathname;
  document.querySelectorAll('.nav-item').forEach(item => {
    const href = item.getAttribute('href');
    if (href && currentPath.startsWith(href) && href !== '/') {
      item.classList.add('active');
    }
  });

  // ── Progress bars animate on load ───────────────────────────
  document.querySelectorAll('.progress-fill').forEach(bar => {
    const targetWidth = bar.style.width || bar.dataset.width;
    if (targetWidth) {
      bar.style.width = '0%';
      requestAnimationFrame(() => {
        setTimeout(() => {
          bar.style.width = targetWidth;
        }, 100);
      });
    }
  });

  // ── Filter chips ─────────────────────────────────────────────
  document.querySelectorAll('.filter-chip[data-filter]').forEach(chip => {
    chip.addEventListener('click', function () {
      const filterGroup = this.dataset.filterGroup;
      const value = this.dataset.filter;
      const url = new URL(window.location);

      if (this.classList.contains('active')) {
        url.searchParams.delete(filterGroup);
      } else {
        url.searchParams.set(filterGroup, value);
      }

      window.location = url.toString();
    });
  });

  // ── Modal close on backdrop ──────────────────────────────────
  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', function (e) {
      if (e.target === this) {
        this.style.display = 'none';
      }
    });
  });

  // ── Delete confirm modal ─────────────────────────────────────
  window.confirmDelete = function (taskId, taskTitle) {
    const overlay = document.getElementById('deleteModal');
    if (overlay) {
      document.getElementById('deleteModalTitle').textContent = `Delete "${taskTitle}"?`;
      document.getElementById('deleteForm').action = `/tasks/${taskId}/delete/`;
      overlay.style.display = 'flex';
    }
  };

  window.closeModal = function (id) {
    const el = document.getElementById(id);
    if (el) el.style.display = 'none';
  };

  // ── Quick status update (AJAX) ───────────────────────────────
  document.querySelectorAll('.quick-status-btn').forEach(btn => {
    btn.addEventListener('click', async function (e) {
      e.stopPropagation();
      const taskId = this.dataset.taskId;
      const newStatus = this.dataset.status;
      const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value
        || getCookie('csrftoken');

      try {
        const res = await fetch(`/tasks/${taskId}/status/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
          },
          body: JSON.stringify({ status: newStatus })
        });

        if (res.ok) {
          window.location.reload();
        }
      } catch (err) {
        console.error('Status update failed', err);
      }
    });
  });

  // ── Category quick-add modal ─────────────────────────────────
  window.openCategoryModal = function () {
    document.getElementById('categoryModal').style.display = 'flex';
  };

  // ── Category AJAX form ───────────────────────────────────────
  const catForm = document.getElementById('categoryForm');
  if (catForm) {
    catForm.addEventListener('submit', async function (e) {
      e.preventDefault();
      const formData = new FormData(this);
      const csrfToken = getCookie('csrftoken');

      try {
        const res = await fetch('/tasks/categories/create/', {
          method: 'POST',
          headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': csrfToken },
          body: formData
        });

        const data = await res.json();
        if (data.success) {
          const select = document.querySelector('select[name="category"]');
          if (select) {
            const opt = new Option(data.name, data.id, false, true);
            select.append(opt);
          }
          document.getElementById('categoryModal').style.display = 'none';
          catForm.reset();
          showToast(`Category "${data.name}" created!`, 'success');
        }
      } catch (err) {
        console.error(err);
      }
    });
  }

  // ── Tooltip helper ───────────────────────────────────────────
  window.showToast = function (msg, type = 'info') {
    const container = document.querySelector('.messages-container') || (() => {
      const d = document.createElement('div');
      d.className = 'messages-container';
      document.body.appendChild(d);
      return d;
    })();

    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `<span>${msg}</span><button class="alert-close">×</button>`;
    container.appendChild(alert);

    setTimeout(() => {
      alert.style.opacity = '0';
      setTimeout(() => alert.remove(), 400);
    }, 3500);

    alert.querySelector('.alert-close').onclick = () => alert.remove();
  };

  // ── CSRF Cookie helper ───────────────────────────────────────
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (const cookie of cookies) {
        const trimmed = cookie.trim();
        if (trimmed.startsWith(name + '=')) {
          cookieValue = decodeURIComponent(trimmed.slice(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  // ── Animate stat counters ────────────────────────────────────
  document.querySelectorAll('.stat-value[data-target]').forEach(el => {
    const target = parseInt(el.dataset.target, 10);
    const duration = 800;
    const step = target / (duration / 16);
    let current = 0;

    const timer = setInterval(() => {
      current = Math.min(current + step, target);
      el.textContent = Math.floor(current);
      if (current >= target) clearInterval(timer);
    }, 16);
  });

});
