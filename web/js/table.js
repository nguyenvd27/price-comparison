// Phần bảng giá dùng chung cho các trang (iPhone, Pokémon…): tiêu đề cột cửa hàng và cửa sổ xếp hạng.
import { esc, formatDiff, formatShortTime, formatTime, formatYen, isStale, openStatus } from "./logic.js";

export function diffClass(n) {
  return n >= 0 ? "pos" : "neg";
}

export function shopHeader(shop, shopState, now) {
  const status = openStatus(shop, now);
  const stale = shopState && isStale(shopState.last_success_at, now);
  const icon = shop.mail_only ? "📦" : status.open ? "🟢" : "🔴";
  const label = shop.mail_only ? "Mail only" : status.label;
  const statusClass = shop.mail_only ? "mail" : status.open ? "open" : "closed";
  const tip = [shop.mail_only ? "Không xếp hạng, không tính vào Diff" : status.text, shop.note].filter(Boolean).join(" · ");
  return `<th class="shop" title="${esc(tip)}">
    <a href="${esc(shop.url)}" target="_blank" rel="noopener">${esc(shop.name)} ↗</a>
    <span class="time long">${formatTime(shopState?.display_at)}</span>
    <span class="status long ${statusClass}">${icon} ${esc(label)}</span>
    <span class="short">${icon} ${formatShortTime(shopState?.display_at, now)}</span>
    ${stale ? '<span class="stale">⚠ dữ liệu cũ</span>' : ""}
  </th>`;
}

// rows: kết quả của rankOffers(); titleHtml đã được escape bởi trang gọi.
export function renderRankModal(modal, { titleHtml, refLabel, refPrice, rows, shopId }) {
  const picked = rows.find((r) => r.shop.id === shopId);
  if (!picked) return;
  const rankedCount = rows.filter((r) => r.rank).length;
  const rankText = picked.rank
    ? `Hạng ${picked.rank} / ${rankedCount}`
    : picked.shop.mail_only ? "📦 Mail only, không xếp hạng" : "Dữ liệu cũ hoặc lỗi, không xếp hạng";
  const list = rows
    .map((r) => {
      const cls = [r.shop.id === shopId ? "picked" : "", r.usable ? "" : "muted"].join(" ").trim();
      return `<tr class="${cls}">
        <td class="rank">${r.rank ?? (r.usable && r.shop.mail_only ? "📦" : "—")}</td>
        <td class="name"><a href="${esc(r.shop.url)}" target="_blank" rel="noopener">${esc(r.shop.name)} ↗</a></td>
        <td>¥${formatYen(r.price)}</td>
        <td class="${r.usable ? diffClass(r.diff) : ""}">${formatDiff(r.diff)}</td>
      </tr>`;
    })
    .join("");
  modal.querySelector("#modal-body").innerHTML = `
    <div class="modal-head">
      <h2>${titleHtml}</h2>
      <span class="apple">${esc(refLabel)} ¥${formatYen(refPrice)}</span>
      <button type="button" class="close" data-close aria-label="Đóng">✕</button>
    </div>
    <div class="modal-summary">
      <p class="shop-price">${esc(picked.shop.name)} trả <strong>¥${formatYen(picked.price)}</strong></p>
      <p><span class="profit ${diffClass(picked.diff)}">Lãi: ${formatDiff(picked.diff)}</span><span class="rank-badge">${rankText}</span></p>
    </div>
    <table class="rank-table">
      <thead><tr><th>Hạng</th><th>Cửa hàng</th><th>Giá</th><th>Diff</th></tr></thead>
      <tbody>${list}</tbody>
    </table>`;
  modal.showModal();
}

export function bindRankModal(table, modal, onOpen) {
  const open = (event) => {
    const cell = event.target.closest("td.clickable");
    if (cell) onOpen(cell);
  };
  table.addEventListener("click", open);
  table.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      open(event);
    }
  });
  // Đóng khi bấm nút ✕ hoặc bấm ra ngoài khung modal (Esc do <dialog> tự xử lý).
  modal.addEventListener("click", (event) => {
    if (event.target === modal || event.target.closest("[data-close]")) modal.close();
  });
}
