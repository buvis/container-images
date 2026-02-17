import { _ as ensure_array_like, Z as attr_class, a0 as stringify } from "../../../chunks/index2.js";
import "chart.js/auto";
import { e as escape_html } from "../../../chunks/context.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    const ranges = [
      { label: "7D", days: 7 },
      { label: "30D", days: 30 },
      { label: "3M", days: 90 },
      { label: "6M", days: 180 },
      { label: "1Y", days: 365 },
      { label: "3Y", days: 1095 },
      { label: "5Y", days: 1825 },
      { label: "10Y", days: 3650 }
    ];
    let activeRange = 7;
    $$renderer2.push(`<div class="bg-slate-950 text-slate-100 p-8"><header class="flex items-center justify-between mb-8"><h1 class="text-3xl font-bold text-white">Market</h1> <div class="flex bg-slate-900 rounded-lg p-1"><!--[-->`);
    const each_array = ensure_array_like(ranges);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let range = each_array[$$index];
      $$renderer2.push(`<button${attr_class(`px-3 py-1 text-xs font-medium rounded transition-colors ${stringify(activeRange === range.days ? "bg-slate-700 text-white shadow" : "text-slate-400 hover:text-slate-200")}`)}>${escape_html(range.label)}</button>`);
    }
    $$renderer2.push(`<!--]--></div></header> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"><!--[-->`);
      const each_array_1 = ensure_array_like(Array(6));
      for (let $$index_1 = 0, $$length = each_array_1.length; $$index_1 < $$length; $$index_1++) {
        each_array_1[$$index_1];
        $$renderer2.push(`<div class="bg-slate-900 p-6 rounded-xl border border-slate-800 animate-pulse h-32"></div>`);
      }
      $$renderer2.push(`<!--]--></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
export {
  _page as default
};
