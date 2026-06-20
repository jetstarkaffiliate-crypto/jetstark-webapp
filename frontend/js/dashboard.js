import { affiliate, payouts, orders, sanitizeHtml } from './api.js';

export async function loadAffiliateDashboard() {
  try {
    const stats = await affiliate.getAnalytics();
    const setText = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };

    setText('total-clicks', stats.total_clicks.toLocaleString());
    setText('total-conversions', stats.total_conversions.toLocaleString());
    setText('conversion-rate', `${stats.conversion_rate}%`);
    setText('total-earnings', `₦${Number(stats.total_earnings).toLocaleString()}`);
    setText('pending-payout', `₦${Number(stats.pending_payout).toLocaleString()}`);
  } catch (err) {
    console.error('Failed to load dashboard:', err);
  }
}

export async function loadAffiliateLinks() {
  const tbody = document.getElementById('linksTableBody');
  if (!tbody) return;

  try {
    const links = await affiliate.listLinks();

    if (!links.length) {
      tbody.innerHTML = '<tr><td colspan="7"><div class="empty-state"><p>No links generated yet</p></div></td></tr>';
      return;
    }

    tbody.innerHTML = links.map(link => `
      <tr>
        <td>${sanitizeHtml(link.product_name || 'Unknown')}</td>
        <td><div class="link-url">${sanitizeHtml(link.url)}</div></td>
        <td class="stat-number">${link.clicks}</td>
        <td class="stat-number">${link.conversions}</td>
        <td>${link.clicks > 0 ? ((link.conversions / link.clicks) * 100).toFixed(2) : '0.00'}%</td>
        <td>₦${Number(link.earnings).toLocaleString()}</td>
        <td>
          <button class="copy-btn" data-copy="${sanitizeHtml(link.url)}">Copy</button>
          <button class="delete-btn" data-delete="${link.id}">Delete</button>
        </td>
      </tr>
    `).join('');

    tbody.querySelectorAll('.copy-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const url = window.location.origin + btn.dataset.copy;
        navigator.clipboard.writeText(url).then(() => {
          btn.textContent = 'Copied!';
          setTimeout(() => btn.textContent = 'Copy', 2000);
        });
      });
    });

    tbody.querySelectorAll('.delete-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        if (!confirm('Delete this affiliate link?')) return;
        try {
          await affiliate.deleteLink(btn.dataset.delete);
          loadAffiliateLinks();
        } catch (err) {
          alert(err.message);
        }
      });
    });
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7">Error: ${sanitizeHtml(err.message)}</td></tr>`;
  }
}

export async function loadPayouts() {
  const container = document.getElementById('payout-history');
  if (!container) return;

  try {
    const balance = await payouts.getBalance();
    const payoutList = await payouts.list();

    document.getElementById('available-balance').textContent = `₦${Number(balance.available_balance).toLocaleString()}`;
    document.getElementById('total-earned').textContent = `₦${Number(balance.total_earned).toLocaleString()}`;

    if (!payoutList.length) {
      container.innerHTML = '<div class="empty-state"><p>No payout requests yet</p></div>';
      return;
    }

    container.innerHTML = payoutList.map(p => `
      <article class="order-card">
        <div class="order-card-header">
          <div>
            <h3>₦${Number(p.amount).toLocaleString()}</h3>
            <p>${new Date(p.requested_at).toLocaleDateString()}</p>
          </div>
          <span class="badge badge-${p.status}">${p.status}</span>
        </div>
        <div class="order-summary-row">
          <span>Note</span><strong>${sanitizeHtml(p.note || '—')}</strong>
        </div>
      </article>
    `).join('');
  } catch (err) {
    container.innerHTML = `<p>Error: ${sanitizeHtml(err.message)}</p>`;
  }
}
