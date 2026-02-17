import { $ as attr, Z as attr_class, _ as ensure_array_like, a0 as stringify, a1 as bind_props } from "./index2.js";
import { f as fallback, e as escape_html } from "./context.js";
function CalendarPicker($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let daysInMonth, firstDayOfMonth, monthName, days, isCurrentMonth;
    let selectedDate = fallback($$props["selectedDate"], () => (/* @__PURE__ */ new Date()).toISOString().split("T")[0], true);
    let currentYear = parseInt(selectedDate.split("-")[0]);
    let currentMonth = parseInt(selectedDate.split("-")[1]) - 1;
    const today = /* @__PURE__ */ new Date();
    const todayStr = today.toISOString().split("T")[0];
    const thisYear = today.getFullYear();
    const thisMonth = today.getMonth();
    Array.from({ length: 11 }, (_, i) => thisYear - 10 + i);
    daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
    firstDayOfMonth = (new Date(currentYear, currentMonth, 1).getDay() + 6) % 7;
    monthName = new Date(currentYear, currentMonth).toLocaleString("default", { month: "long" });
    days = Array.from({ length: daysInMonth }, (_, i) => {
      const day = i + 1;
      const dateStr = new Date(Date.UTC(currentYear, currentMonth, day)).toISOString().split("T")[0];
      return {
        day,
        dateStr,
        isSelected: selectedDate === dateStr,
        isToday: todayStr === dateStr,
        isFuture: dateStr > todayStr
      };
    });
    isCurrentMonth = currentYear === thisYear && currentMonth === thisMonth;
    $$renderer2.push(`<div class="bg-slate-800 p-4 rounded-lg shadow-lg text-slate-200 w-full max-w-sm"><div class="flex justify-between items-center mb-4"><button class="p-1 hover:bg-slate-700 rounded cursor-pointer" aria-label="Previous month">&lt;</button> <div class="flex gap-1 relative"><button class="font-bold hover:bg-slate-700 px-2 py-0.5 rounded cursor-pointer" aria-label="Select month">${escape_html(monthName)}</button> <button class="font-bold hover:bg-slate-700 px-2 py-0.5 rounded cursor-pointer" aria-label="Select year">${escape_html(currentYear)}</button> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div> <button${attr("disabled", isCurrentMonth, true)}${attr_class(`p-1 rounded ${stringify(isCurrentMonth ? "text-slate-600 cursor-not-allowed" : "hover:bg-slate-700 cursor-pointer")}`)} aria-label="Next month">></button></div> <div class="grid grid-cols-7 gap-1 text-center text-sm"><!--[-->`);
    const each_array_2 = ensure_array_like(["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]);
    for (let $$index_2 = 0, $$length = each_array_2.length; $$index_2 < $$length; $$index_2++) {
      let dayName = each_array_2[$$index_2];
      $$renderer2.push(`<div class="text-slate-500 font-medium py-1 text-xs">${escape_html(dayName)}</div>`);
    }
    $$renderer2.push(`<!--]--> <!--[-->`);
    const each_array_3 = ensure_array_like(Array(firstDayOfMonth));
    for (let $$index_3 = 0, $$length = each_array_3.length; $$index_3 < $$length; $$index_3++) {
      each_array_3[$$index_3];
      $$renderer2.push(`<div></div>`);
    }
    $$renderer2.push(`<!--]--> <!--[-->`);
    const each_array_4 = ensure_array_like(days);
    for (let $$index_4 = 0, $$length = each_array_4.length; $$index_4 < $$length; $$index_4++) {
      let d = each_array_4[$$index_4];
      $$renderer2.push(`<button${attr_class(`p-2 rounded-lg transition-all relative ${stringify(d.isFuture ? "text-slate-600 cursor-not-allowed" : "cursor-pointer")} ${stringify(d.isSelected ? "bg-blue-600 text-white font-semibold scale-105 shadow-md z-10" : !d.isFuture ? "hover:bg-slate-700" : "")}`)}${attr("disabled", d.isFuture, true)}>${escape_html(d.day)} `);
      if (d.isToday) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<span${attr_class(`absolute bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full ${stringify(d.isSelected ? "bg-white" : "bg-blue-400")}`)}></span>`);
      } else {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--></button>`);
    }
    $$renderer2.push(`<!--]--></div> <div class="mt-3 pt-3 border-t border-slate-700 flex justify-center"><button class="flex items-center gap-2 text-sm font-medium text-slate-300 bg-slate-700/40 hover:bg-slate-700 hover:text-white px-3 py-1.5 rounded-md border border-slate-600/50 hover:border-slate-500 transition-colors cursor-pointer"><svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg> Today</button></div></div>`);
    bind_props($$props, { selectedDate });
  });
}
export {
  CalendarPicker as C
};
