import { WEEKDAY_FULL, WEEKDAY_VI, chartSeries, formatYen, isWeekend, jstDate, weekdayStats } from "./logic.js";

let lineChart = null;
let barChart = null;

// Tô nền cam nhạt cho Thứ 7 và Chủ nhật để dễ thấy giá cuối tuần.
const weekendShade = {
  id: "weekendShade",
  beforeDatasetsDraw(chart) {
    const { ctx, chartArea, scales } = chart;
    const labels = chart.data.labels;
    const step = labels.length > 1 ? scales.x.getPixelForValue(1) - scales.x.getPixelForValue(0) : chartArea.width;
    ctx.save();
    ctx.fillStyle = "rgba(255, 167, 38, 0.14)";
    labels.forEach((date, i) => {
      if (!isWeekend(date)) return;
      const x = scales.x.getPixelForValue(i);
      ctx.fillRect(x - step / 2, chartArea.top, step, chartArea.bottom - chartArea.top);
    });
    ctx.restore();
  },
};

export function renderCharts(data, state) {
  const today = jstDate(new Date());
  renderLine(data, state, today);
  renderWeekday(data, state, today);
}

function renderLine({ catalog, daily }, state, today) {
  const { labels, datasets } = chartSeries(daily, catalog, state.chartCap, state.range, today);
  const apple = catalog.variants.find((v) => v.capacity === state.chartCap)?.apple_price ?? null;
  const shopName = (id) => catalog.shops.find((s) => s.id === id)?.name ?? id;

  lineChart?.destroy();
  lineChart = new Chart(document.querySelector("#line-chart"), {
    type: "line",
    data: {
      labels,
      datasets: [
        ...datasets.map((s) => ({
          label: s.label,
          data: s.data,
          shops: s.shops,
          borderColor: s.hex,
          backgroundColor: s.hex,
          borderWidth: 2,
          pointRadius: 3,
          spanGaps: true,
          tension: 0,
        })),
        {
          label: "Giá Apple",
          data: labels.map(() => apple),
          borderColor: "#9ca3af",
          borderDash: [6, 4],
          borderWidth: 1.5,
          pointRadius: 0,
          pointHitRadius: 0,
        },
      ],
    },
    options: {
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      scales: {
        x: { ticks: { callback: (_, i) => labels[i].slice(5).replace("-", "/") } },
        y: { ticks: { callback: (v) => `${Math.round(v / 1000)}k` } },
      },
      plugins: {
        // Không hiện chú thích chữ: mỗi đường đã mang đúng màu của máy.
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: (items) => items[0]?.label ?? "",
            label: (ctx) => {
              if (!ctx.dataset.shops) return `Giá Apple: ¥${formatYen(ctx.parsed.y)}`;
              const shop = ctx.dataset.shops[ctx.dataIndex];
              return `¥${formatYen(ctx.parsed.y)}${shop ? ` · ${shopName(shop)}` : ""}`;
            },
          },
        },
      },
    },
    plugins: [weekendShade],
  });
}

function renderWeekday({ catalog, daily }, state, today) {
  const variant = catalog.variants.find((v) => v.capacity === state.chartCap && v.color === state.chartColor);
  const stats = variant ? weekdayStats(daily, variant.id, today) : { ready: false, needDays: 14 };
  const empty = document.querySelector("#weekday-empty");
  const canvas = document.querySelector("#weekday-chart");
  const tip = document.querySelector("#weekday-tip");

  barChart?.destroy();
  barChart = null;
  if (!stats.ready) {
    empty.hidden = false;
    empty.textContent = `Đang thu thập dữ liệu (cần thêm ${stats.needDays} ngày)`;
    canvas.parentElement.hidden = true;
    tip.textContent = "";
    return;
  }

  empty.hidden = true;
  canvas.parentElement.hidden = false;
  barChart = new Chart(canvas, {
    type: "bar",
    data: {
      labels: WEEKDAY_VI,
      datasets: [{
        data: stats.deltas,
        backgroundColor: stats.deltas.map((v) => ((v ?? 0) >= 0 ? "#2e7d32" : "#c62828")),
        borderRadius: 4,
      }],
    },
    options: {
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.parsed.y >= 0 ? "+" : "−"}¥${formatYen(Math.abs(ctx.parsed.y))} so với trung bình tuần`,
          },
        },
      },
      scales: { y: { ticks: { callback: (v) => `${v >= 0 ? "+" : ""}${(v / 1000).toFixed(1)}k` } } },
    },
  });
  tip.textContent = `Nên bán: ${WEEKDAY_FULL[stats.best]}, trung bình cao hơn ${WEEKDAY_FULL[stats.worst]} khoảng ¥${formatYen(stats.gap)}`;
}
