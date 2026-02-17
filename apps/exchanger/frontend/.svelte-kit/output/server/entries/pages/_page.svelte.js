import { Z as attr_class, _ as ensure_array_like, a5 as attr_style, a0 as stringify, $ as attr, a1 as bind_props } from "../../chunks/index2.js";
import { o as onDestroy } from "../../chunks/index-server.js";
import { f as formatDateTime } from "../../chunks/formatters.js";
import { e as escape_html, f as fallback } from "../../chunks/context.js";
function TaskPipeline($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let tasks = [];
    function getRateLimitCountdown(until) {
      if (!until) return null;
      const end = new Date(until).getTime();
      const now = Date.now();
      const remaining = Math.max(0, Math.ceil((end - now) / 1e3));
      return remaining > 0 ? `${remaining}s` : null;
    }
    onDestroy(() => {
    });
    $$renderer2.push(`<div class="bg-slate-800 p-4 rounded-lg shadow-lg border border-slate-700"><div class="flex items-center justify-between mb-4"><h2 class="text-xl font-bold text-white">Tasks</h2> <span class="flex items-center gap-1.5 text-xs"><span${attr_class(`w-2 h-2 rounded-full ${stringify("bg-red-500")}`)}></span> <span class="text-slate-400">${escape_html("Reconnecting")}</span></span></div> `);
    if (tasks.length === 0) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="animate-pulse space-y-4"><!--[-->`);
      const each_array = ensure_array_like(Array(3));
      for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
        each_array[$$index];
        $$renderer2.push(`<div class="h-12 bg-slate-700 rounded"></div>`);
      }
      $$renderer2.push(`<!--]--></div>`);
    } else {
      $$renderer2.push("<!--[!-->");
      if (tasks.length === 0) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div class="flex items-center justify-center py-8 text-slate-500"><span class="text-sm">No active tasks</span></div>`);
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`<div class="space-y-4"><!--[-->`);
        const each_array_1 = ensure_array_like(tasks);
        for (let $$index_1 = 0, $$length = each_array_1.length; $$index_1 < $$length; $$index_1++) {
          let task = each_array_1[$$index_1];
          const countdown = getRateLimitCountdown(task.rate_limit_until);
          $$renderer2.push(`<div class="bg-slate-900 p-4 rounded border border-slate-700"><div class="flex justify-between items-center mb-2"><span class="font-semibold text-white">${escape_html(task.name)}</span> <span class="text-xs text-slate-400">Last: ${escape_html(formatDateTime(task.last_run) || "Never")}</span></div> `);
          if (task.status === "running") {
            $$renderer2.push("<!--[-->");
            $$renderer2.push(`<div class="mb-2"><div class="h-2 bg-slate-700 rounded-full overflow-hidden"><div${attr_class("h-full bg-blue-500 transition-all duration-300", void 0, { "animate-pulse": countdown })}${attr_style(`width: ${stringify(task.progress ?? 0)}%`)}></div></div></div> <div class="flex justify-between items-center text-xs"><span class="text-slate-400">`);
            if (countdown) {
              $$renderer2.push("<!--[-->");
              $$renderer2.push(`<span class="text-amber-400">Rate limited: ${escape_html(countdown)}</span>`);
            } else {
              $$renderer2.push("<!--[!-->");
              $$renderer2.push(`${escape_html(task.message)}`);
            }
            $$renderer2.push(`<!--]--></span> <span class="text-blue-400 font-mono">${escape_html(task.progress ?? 0)}%</span></div>`);
          } else {
            $$renderer2.push("<!--[!-->");
            $$renderer2.push(`<div class="flex justify-between items-center"><span class="text-xs text-slate-400 truncate max-w-[70%]">${escape_html(task.message)}</span> <span${attr_class(`text-xs px-2 py-1 rounded ${task.status === "error" ? "bg-red-900 text-red-200" : task.status === "done" ? "bg-green-900 text-green-200" : "bg-slate-800 text-slate-400"}`)}>${escape_html(task.status)}</span></div>`);
          }
          $$renderer2.push(`<!--]--></div>`);
        }
        $$renderer2.push(`<!--]--></div>`);
      }
      $$renderer2.push(`<!--]-->`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
function CalendarHeatmap($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let maxValue, days;
    let coverage = fallback($$props["coverage"], () => ({}), true);
    let favoritesCount = fallback($$props["favoritesCount"], 0);
    let missingSymbols = fallback($$props["missingSymbols"], () => ({}), true);
    function getPast365Days(data) {
      const d = [];
      const today = /* @__PURE__ */ new Date();
      const gridStart = new Date(today);
      gridStart.setDate(today.getDate() - 370);
      for (let i = 0; i < 371; i++) {
        const current = new Date(gridStart);
        current.setDate(gridStart.getDate() + i);
        const offset = current.getTimezoneOffset() * 6e4;
        const localDate = new Date(current.getTime() - offset);
        const dateStr = localDate.toISOString().split("T")[0];
        d.push({
          date: dateStr,
          month: current.getMonth(),
          day: current.getDate(),
          value: data[dateStr] || 0
        });
      }
      return d;
    }
    function getColor(val) {
      if (val === 0) return "bg-slate-700";
      if (favoritesCount > 0) {
        if (val >= favoritesCount) return "bg-green-500";
        return "bg-yellow-500";
      }
      if (maxValue === 1) return "bg-green-500";
      const ratio = val / maxValue;
      if (ratio < 0.8) return "bg-yellow-500";
      return "bg-green-500";
    }
    maxValue = Math.max(...Object.values(coverage), 1);
    days = getPast365Days(coverage);
    $$renderer2.push(`<div class="bg-slate-800 rounded-lg shadow-lg p-4 border border-slate-700 overflow-x-auto"><div class="flex items-center justify-between mb-2"><h3 class="text-slate-200 font-bold text-sm">Data Coverage</h3> <div class="flex items-center gap-2 text-xs text-slate-400"><span class="flex items-center gap-1"><span class="w-3 h-3 bg-slate-700 rounded-sm"></span> Missing</span> <span class="flex items-center gap-1"><span class="w-3 h-3 bg-yellow-500 rounded-sm"></span> Partial</span> <span class="flex items-center gap-1"><span class="w-3 h-3 bg-green-500 rounded-sm"></span> Complete</span></div></div> <div class="flex gap-1"><!--[-->`);
    const each_array = ensure_array_like(Array(53));
    for (let weekIndex = 0, $$length = each_array.length; weekIndex < $$length; weekIndex++) {
      each_array[weekIndex];
      $$renderer2.push(`<div class="flex flex-col gap-1"><!--[-->`);
      const each_array_1 = ensure_array_like(Array(7));
      for (let dayIndex = 0, $$length2 = each_array_1.length; dayIndex < $$length2; dayIndex++) {
        each_array_1[dayIndex];
        const day = days[weekIndex * 7 + dayIndex];
        $$renderer2.push(`<div${attr_class(`w-3 h-3 rounded-sm ${stringify(getColor(day.value))} hover:ring-1 hover:ring-white transition-all duration-75 cursor-default`)} role="img"${attr("aria-label", `${stringify(day.date)}: ${stringify(day.value)} rates`)}></div>`);
      }
      $$renderer2.push(`<!--]--></div>`);
    }
    $$renderer2.push(`<!--]--></div></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]-->`);
    bind_props($$props, { coverage, favoritesCount, missingSymbols });
  });
}
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let healthStatus = "loading";
    let favorites = [];
    let coverage = {};
    let missingSymbols = {};
    let providers = [];
    $$renderer2.push(`<div class="bg-slate-950 text-slate-100 p-8"><header class="flex items-center justify-between mb-8"><h1 class="text-3xl font-bold text-white">Status</h1> <div class="flex items-center gap-2 bg-slate-900 px-4 py-2 rounded-full border border-slate-800"><div${attr_class(`w-3 h-3 rounded-full ${"bg-slate-500 animate-pulse"}`)}></div> <span class="text-sm font-medium uppercase tracking-wider">${escape_html(healthStatus)}</span></div></header> <div class="mb-8">`);
    CalendarHeatmap($$renderer2, { coverage, missingSymbols, favoritesCount: favorites.length });
    $$renderer2.push(`<!----></div> <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">`);
    TaskPipeline($$renderer2);
    $$renderer2.push(`<!----> <div class="bg-slate-900 rounded-xl border border-slate-800 p-4"><h3 class="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Providers</h3> <div class="space-y-2"><!--[-->`);
    const each_array = ensure_array_like(providers);
    for (let $$index_1 = 0, $$length = each_array.length; $$index_1 < $$length; $$index_1++) {
      let provider = each_array[$$index_1];
      $$renderer2.push(`<div class="flex flex-col sm:flex-row sm:items-center justify-between py-3 px-4 bg-slate-800/50 rounded-lg gap-3 transition-colors hover:bg-slate-800/70"><div class="flex flex-col gap-2"><span class="text-sm font-medium text-white">${escape_html(provider.name)}</span> `);
      if (Object.keys(provider.symbol_counts_by_type).length > 0) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div class="flex flex-wrap gap-2"><!--[-->`);
        const each_array_1 = ensure_array_like(Object.entries(provider.symbol_counts_by_type));
        for (let $$index = 0, $$length2 = each_array_1.length; $$index < $$length2; $$index++) {
          let [type, count] = each_array_1[$$index];
          $$renderer2.push(`<div class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-slate-700/30 border border-slate-700/50"><span class="text-slate-200 mr-1.5 font-semibold">${escape_html(count)}</span> <span class="text-slate-400 uppercase tracking-wider">${escape_html(type)}</span></div>`);
        }
        $$renderer2.push(`<!--]--></div>`);
      } else {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--></div> <div class="flex items-center gap-3 shrink-0 self-end sm:self-auto"><span class="text-xs text-slate-500"><span class="text-slate-300 font-semibold">${escape_html(provider.symbol_count)}</span> total</span> `);
      if (provider.symbol_count > 0) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div class="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.4)]"></div>`);
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push(`<div class="w-2 h-2 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.4)]" title="No symbols configured"></div>`);
      }
      $$renderer2.push(`<!--]--></div></div>`);
    }
    $$renderer2.push(`<!--]--></div></div></div></div>`);
  });
}
export {
  _page as default
};
