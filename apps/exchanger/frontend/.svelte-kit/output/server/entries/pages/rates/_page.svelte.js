import "clsx";
import { C as CalendarPicker } from "../../../chunks/CalendarPicker.js";
import { _ as ensure_array_like, Z as attr_class, a1 as bind_props, a0 as stringify, a5 as attr_style } from "../../../chunks/index2.js";
import { e as escape_html, f as fallback } from "../../../chunks/context.js";
import { S as SearchInput } from "../../../chunks/SearchInput.js";
import "chart.js/auto";
import { o as onDestroy } from "../../../chunks/index-server.js";
function SegmentedControl($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let { options, value = "" } = $$props;
    function getLabel(opt) {
      return typeof opt === "string" ? opt.charAt(0).toUpperCase() + opt.slice(1) : opt.label;
    }
    function getValue(opt) {
      return typeof opt === "string" ? opt : opt.value;
    }
    $$renderer2.push(`<div class="flex bg-slate-900 rounded-lg p-1 border border-slate-700"><!--[-->`);
    const each_array = ensure_array_like(options);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let opt = each_array[$$index];
      const optValue = getValue(opt);
      $$renderer2.push(`<button type="button"${attr_class(`px-4 py-1.5 text-sm font-medium rounded transition-colors ${stringify(value === optValue ? "bg-slate-700 text-white" : "text-slate-400 hover:text-slate-200")}`)}>${escape_html(getLabel(opt))}</button>`);
    }
    $$renderer2.push(`<!--]--></div>`);
    bind_props($$props, { value });
  });
}
function SymbolList($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let favoriteKeys, filteredRates;
    let rates = fallback($$props["rates"], () => [], true);
    let favorites = fallback($$props["favorites"], () => [], true);
    let selectedSymbol = fallback($$props["selectedSymbol"], null);
    let activeType = fallback($$props["activeType"], "forex");
    let search = "";
    function isFavorite(rate) {
      return favoriteKeys.has(`${rate.provider}:${rate.provider_symbol}`);
    }
    favoriteKeys = new Set(favorites.map((f) => `${f.provider}:${f.provider_symbol}`));
    filteredRates = rates.filter((r) => r.symbol.toLowerCase().includes(search.toLowerCase()));
    let $$settled = true;
    let $$inner_renderer;
    function $$render_inner($$renderer3) {
      $$renderer3.push(`<div class="bg-slate-800 rounded-lg shadow-lg flex flex-col h-full overflow-hidden border border-slate-700"><div class="p-4 border-b border-slate-700 space-y-3">`);
      SegmentedControl($$renderer3, {
        options: ["forex", "crypto"],
        get value() {
          return activeType;
        },
        set value($$value) {
          activeType = $$value;
          $$settled = false;
        }
      });
      $$renderer3.push(`<!----> `);
      SearchInput($$renderer3, {
        placeholder: "Search symbol...",
        get value() {
          return search;
        },
        set value($$value) {
          search = $$value;
          $$settled = false;
        }
      });
      $$renderer3.push(`<!----></div> <div class="flex-1 overflow-y-auto p-2 space-y-1">`);
      const each_array = ensure_array_like(filteredRates);
      if (each_array.length !== 0) {
        $$renderer3.push("<!--[-->");
        for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
          let rate = each_array[$$index];
          $$renderer3.push(`<div role="button" tabindex="0"${attr_class(`w-full flex items-center justify-between p-2 rounded hover:bg-slate-700 transition-colors group cursor-pointer ${stringify(selectedSymbol === rate.symbol ? "bg-slate-700 ring-1 ring-slate-500" : "")}`)}><span class="font-bold text-slate-200">${escape_html(rate.symbol)}</span> <div class="flex items-center gap-3"><span class="font-mono text-slate-300">${escape_html(rate.rate.toFixed(4))}</span> <button class="text-slate-500 hover:text-yellow-400 transition-colors p-1" aria-label="Toggle favorite"><svg xmlns="http://www.w3.org/2000/svg"${attr_class(`h-5 w-5 ${stringify(isFavorite(rate) ? "text-yellow-400 fill-current" : "fill-none stroke-current")}`)} viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"></path></svg></button></div></div>`);
        }
      } else {
        $$renderer3.push("<!--[!-->");
        $$renderer3.push(`<div class="text-center text-slate-500 py-4 text-sm">No rates found</div>`);
      }
      $$renderer3.push(`<!--]--></div></div>`);
    }
    do {
      $$settled = true;
      $$inner_renderer = $$renderer2.copy();
      $$render_inner($$inner_renderer);
    } while (!$$settled);
    $$renderer2.subsume($$inner_renderer);
    bind_props($$props, { rates, favorites, selectedSymbol, activeType });
  });
}
function RateChart($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let symbol = fallback($$props["symbol"], null);
    let history = fallback($$props["history"], () => [], true);
    let isLoading = fallback($$props["isLoading"], false);
    let activeRange = fallback($$props["activeRange"], "30d");
    const ranges = [
      { label: "7D", value: "7d", days: 7 },
      { label: "30D", value: "30d", days: 30 },
      { label: "3M", value: "3m", days: 90 },
      { label: "6M", value: "6m", days: 180 },
      { label: "1Y", value: "1y", days: 365 },
      { label: "3Y", value: "3y", days: 1095 },
      { label: "5Y", value: "5y", days: 1825 },
      { label: "10Y", value: "10y", days: 3650 }
    ];
    onDestroy(() => {
    });
    ({
      labels: history.map((h) => h.date),
      datasets: [
        {
          label: symbol || "Rate",
          fill: true,
          tension: 0.3,
          backgroundColor: "rgba(59, 130, 246, 0.1)",
          borderColor: "rgb(59, 130, 246)",
          pointRadius: 0,
          pointHitRadius: 10,
          data: history.map((h) => h.rate)
        }
      ]
    });
    $$renderer2.push(`<div class="bg-slate-800 rounded-lg shadow-lg p-4 h-full flex flex-col border border-slate-700"><div class="flex justify-between items-center mb-4"><h2 class="text-xl font-bold text-slate-200">${escape_html(symbol ? `${symbol} History` : "Select a symbol")}</h2> <div class="flex bg-slate-900 rounded-lg p-1"><!--[-->`);
    const each_array = ensure_array_like(ranges);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let range = each_array[$$index];
      $$renderer2.push(`<button${attr_class(`px-3 py-1 text-xs font-medium rounded transition-colors ${stringify(activeRange === range.value ? "bg-slate-700 text-white shadow" : "text-slate-400 hover:text-slate-200")}`)}>${escape_html(range.label)}</button>`);
    }
    $$renderer2.push(`<!--]--></div></div> <div class="flex-1 relative min-h-[300px]">`);
    if (isLoading) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="absolute inset-0 flex items-center justify-center bg-slate-800/50 z-10"><div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div></div>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <div class="w-full h-full"${attr_style("", { display: symbol && history.length > 0 ? "block" : "none" })}><canvas></canvas></div> `);
    if (!symbol) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="absolute inset-0 flex items-center justify-center text-slate-500">Select a symbol to view history</div>`);
    } else {
      $$renderer2.push("<!--[!-->");
      if (history.length === 0 && !isLoading) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div class="absolute inset-0 flex items-center justify-center text-slate-500">No data available</div>`);
      } else {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]-->`);
    }
    $$renderer2.push(`<!--]--></div></div>`);
    bind_props($$props, { symbol, history, isLoading, activeRange });
  });
}
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let selectedDate = (/* @__PURE__ */ new Date()).toISOString().split("T")[0];
    let selectedSymbol = null;
    let activeType = "forex";
    let rates = [];
    let favorites = [];
    let history = [];
    let loadingHistory = false;
    let currentRange = "30d";
    parseInt(selectedDate.split("-")[0]);
    $$renderer2.push(`<div class="bg-slate-950 text-slate-200 p-6 flex flex-col gap-6"><header class="mb-4"><h1 class="text-3xl font-bold text-white">Rates</h1></header> <div class="flex flex-col lg:flex-row gap-6 flex-1 min-h-0"><div class="w-full lg:w-96 flex flex-col gap-6">`);
    CalendarPicker($$renderer2, { selectedDate });
    $$renderer2.push(`<!----> <div class="flex-1 min-h-[400px]">`);
    SymbolList($$renderer2, { rates, favorites, selectedSymbol, activeType });
    $$renderer2.push(`<!----></div></div> <div class="flex-1 min-h-[500px]">`);
    RateChart($$renderer2, {
      symbol: selectedSymbol,
      history,
      isLoading: loadingHistory,
      activeRange: currentRange
    });
    $$renderer2.push(`<!----></div></div></div>`);
  });
}
export {
  _page as default
};
