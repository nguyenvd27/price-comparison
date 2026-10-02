import { DATA_BASE } from "./config.js";
import { bestDiff, bestItemDiff, formatDiff, legacyRedirect } from "./logic.js";

// Link cũ của trang iPhone (trước khi tách trang) vẫn mở đúng bảng giá.
const redirect = legacyRedirect(location.search);
if (redirect) location.replace(redirect);

async function loadJson(name) {
  const res = await fetch(`${DATA_BASE}${name}?t=${Date.now()}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`${name}: HTTP ${res.status}`);
  return res.json();
}

async function showIphoneSummary() {
  const el = document.querySelector("#iphone-summary");
  try {
    const [catalog, latest] = await Promise.all([loadJson("catalog.json"), loadJson("latest.json")]);
    const best = bestDiff(catalog, latest, "pm", new Date());
    if (!best) return;
    el.textContent = `💰 18 Pro Max lãi tới ${formatDiff(best.diff)} yên so với Apple`;
    el.classList.add(best.diff >= 0 ? "pos" : "neg");
    el.hidden = false;
  } catch {
    // Không tải được dữ liệu thì thẻ vẫn bấm được, chỉ không có dòng tóm tắt.
  }
}

async function showPokemonSummary() {
  const el = document.querySelector("#pokemon-summary");
  try {
    const [catalog, latest] = await Promise.all([loadJson("pokemon/catalog.json"), loadJson("pokemon/latest.json")]);
    const best = bestItemDiff(catalog, latest, new Date());
    if (!best) return;
    el.textContent = `💰 ${best.item.name} lãi tới ${formatDiff(best.diff)} yên so với giá gốc`;
    el.classList.add(best.diff >= 0 ? "pos" : "neg");
    el.hidden = false;
  } catch {
    // Không tải được dữ liệu thì thẻ vẫn bấm được, chỉ không có dòng tóm tắt.
  }
}

if (!redirect) {
  showIphoneSummary();
  showPokemonSummary();
}
