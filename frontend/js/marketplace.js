import { products, orders, affiliate, sanitizeHtml } from './api.js';

let currentPage = 1;
let currentTotal = 0;
const PAGE_SIZE = 20;

export async function renderProductGrid(containerId, params = {}, append = false) {
  const container = document.getElementById(containerId);
  if (!container) return;

  try {
    if (!append) currentPage = 1;
    const result = await products.list({ ...params, page: currentPage, page_size: PAGE_SIZE });
    const productList = result.products || [];
    currentTotal = result.total || 0;

    if (!productList.length && !append) {
      container.innerHTML = '<div class="empty-state"><p>No products found</p></div>';
      return;
    }

    const html = productList.map(p => `
      <article class="product-card" onclick="window.location.href='product-detail.html?id=${p.id}'">
        <div class="product-thumbnail">${p.cover_image_url ? `<img src="${sanitizeHtml(p.cover_image_url)}" alt="${sanitizeHtml(p.title)}" loading="lazy">` : '📦'}</div>
        <div class="product-card-body">
          <h3>${sanitizeHtml(p.title)}</h3>
          <p class="product-category">${sanitizeHtml(p.category)}</p>
          <p class="product-description">${sanitizeHtml((p.description || '').substring(0, 100))}</p>
          <div class="product-meta">
            <div class="rating">
              <span class="stars">${'⭐'.repeat(Math.round(p.rating))}</span>
              <span class="reviews">(${p.review_count})</span>
            </div>
            <span class="sales">${p.sales_count} sales</span>
          </div>
        </div>
        <div class="product-footer">
          <span class="price">₦${Number(p.price).toLocaleString()}</span>
          <span class="commission">${p.commission_rate}% commission</span>
          <button class="button button-small" data-add-to-cart="${p.id}">Add to Cart</button>
        </div>
      </article>
    `).join('');

    if (append) {
      container.insertAdjacentHTML('beforeend', html);
    } else {
      container.innerHTML = html;
    }

    const hasMore = currentPage * PAGE_SIZE < currentTotal;
    if (productList.length) currentPage++;
    let loadMoreEl = document.getElementById('load-more-container');
    if (!loadMoreEl) {
      loadMoreEl = document.createElement('div');
      loadMoreEl.id = 'load-more-container';
      loadMoreEl.className = 'load-more-container';
      container.parentNode.appendChild(loadMoreEl);
    }
    loadMoreEl.innerHTML = hasMore
      ? '<button class="button button-secondary" id="load-more-btn">Load More</button>'
      : (currentPage > 1 ? '<p class="load-more-done">All products loaded</p>' : '');
  } catch (err) {
    if (!append) container.innerHTML = `<div class="empty-state"><p>Error loading products: ${sanitizeHtml(err.message)}</p></div>`;
  }
}
