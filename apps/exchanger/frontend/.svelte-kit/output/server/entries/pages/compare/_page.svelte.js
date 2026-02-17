import { $ as attr, _ as ensure_array_like } from "../../../chunks/index2.js";
import { C as CalendarPicker } from "../../../chunks/CalendarPicker.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let allHistory, allRates;
    let search = "";
    let selectedDate = (/* @__PURE__ */ new Date()).toISOString().split("T")[0];
    let variantData = {};
    allHistory = Object.values(variantData).flatMap((d) => d.history);
    allRates = allHistory.map((h) => h.rate).filter((r) => r !== null);
    allRates.length ? Math.min(...allRates) : 0;
    allRates.length ? Math.max(...allRates) : 1;
    $$renderer2.push(`<div class="bg-slate-950 text-slate-200 p-6"><header class="mb-8"><h1 class="text-3xl font-bold text-white">Compare</h1></header> <div class="flex flex-col lg:flex-row gap-6"><div class="w-full lg:w-80 flex-shrink-0 flex flex-col gap-4">`);
    CalendarPicker($$renderer2, { selectedDate });
    $$renderer2.push(`<!----> <div class="bg-slate-900 rounded-xl border border-slate-800 p-4"><input type="text"${attr("value", search)} placeholder="Search symbols..." class="w-full px-3 py-2 mb-4 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-slate-500"/> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="space-y-2"><!--[-->`);
      const each_array = ensure_array_like(Array(5));
      for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
        each_array[$$index];
        $$renderer2.push(`<div class="h-12 bg-slate-800 rounded animate-pulse"></div>`);
      }
      $$renderer2.push(`<!--]--></div>`);
    }
    $$renderer2.push(`<!--]--></div></div> <div class="flex-1">`);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="bg-slate-900 rounded-xl border border-slate-800 p-8 text-center text-slate-500">Select a symbol to compare rates across providers.</div>`);
    }
    $$renderer2.push(`<!--]--></div></div></div>`);
  });
}
export {
  _page as default
};
