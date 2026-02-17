import { a2 as store_get, $ as attr, _ as ensure_array_like, Z as attr_class, a0 as stringify, a3 as unsubscribe_stores } from "../../../chunks/index2.js";
import { p as page } from "../../../chunks/stores.js";
import { f as formatDateTime } from "../../../chunks/formatters.js";
import { e as escape_html } from "../../../chunks/context.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let activeTab, currentProviderSymbols;
    let backfillProvider = "cnb";
    let backfillLength = 30;
    let availableSymbols = [];
    let selectedBackfillSymbols = [];
    let symbolSearchTerm = "";
    let taskStatuses = [];
    let symbolsProvider = "cnb";
    let backups = [];
    let selectedBackup = null;
    activeTab = ["backfill", "symbols", "backups"].includes(store_get($$store_subs ??= {}, "$page", page).url.searchParams.get("tab") || "") ? store_get($$store_subs ??= {}, "$page", page).url.searchParams.get("tab") : "backfill";
    currentProviderSymbols = availableSymbols.filter((s) => s.provider === backfillProvider);
    currentProviderSymbols.filter((s) => {
      const term = symbolSearchTerm.toLowerCase();
      const matchesSearch = s.provider_symbol.toLowerCase().includes(term) || s.name.toLowerCase().includes(term);
      const notSelected = !selectedBackfillSymbols.find((sel) => sel.provider_symbol === s.provider_symbol);
      return matchesSearch && notSelected;
    }).slice(0, 50);
    $$renderer2.push(`<div class="bg-slate-950 text-slate-200 p-6"><header class="mb-8"><h1 class="text-3xl font-bold text-white">${escape_html(
      // Clear selection on provider change
      activeTab.charAt(0).toUpperCase() + activeTab.slice(1)
    )}</h1></header> <div class="max-w-4xl mx-auto"><div class="bg-slate-900 border border-slate-800 rounded-xl p-6">`);
    if (activeTab === "backfill") {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="space-y-6"><div class="grid grid-cols-1 md:grid-cols-2 gap-4"><div class="space-y-2"><label for="backfill-provider" class="block text-sm font-medium text-slate-300">Provider</label> `);
      $$renderer2.select(
        {
          id: "backfill-provider",
          value: backfillProvider,
          class: "w-full bg-slate-800 border border-slate-700 rounded p-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
        },
        ($$renderer3) => {
          $$renderer3.option({ value: "cnb" }, ($$renderer4) => {
            $$renderer4.push(`CNB`);
          });
          $$renderer3.option({ value: "fcs" }, ($$renderer4) => {
            $$renderer4.push(`FCS`);
          });
        }
      );
      $$renderer2.push(`</div> <div class="space-y-2"><label for="backfill-length" class="block text-sm font-medium text-slate-300">Length (days)</label> <input id="backfill-length" type="number" min="1" max="3650"${attr("value", backfillLength)} class="w-full bg-slate-800 border border-slate-700 rounded p-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"/></div> <div class="col-span-1 md:col-span-2 space-y-2 relative"><label for="backfill-symbols" class="block text-sm font-medium text-slate-300">Symbols (optional)</label> <div class="w-full bg-slate-800 border border-slate-700 rounded p-2 text-white min-h-[42px] relative focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-transparent"><div class="flex flex-wrap gap-2"><!--[-->`);
      const each_array = ensure_array_like(selectedBackfillSymbols);
      for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
        let symbol = each_array[$$index];
        $$renderer2.push(`<span class="bg-blue-900/50 border border-blue-700 text-blue-200 px-2 py-0.5 rounded text-sm flex items-center gap-1">${escape_html(symbol.provider_symbol)} <button class="hover:text-white ml-1 text-blue-400 font-bold leading-none">×</button></span>`);
      }
      $$renderer2.push(`<!--]--> <input id="backfill-symbols" type="text"${attr("placeholder", selectedBackfillSymbols.length > 0 ? "" : "Search symbols...")}${attr("value", symbolSearchTerm)} class="bg-transparent border-none outline-none flex-1 min-w-[120px] text-white placeholder-slate-500 text-sm py-1"/></div></div> `);
      {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--></div></div> <button class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium transition-colors">Trigger Backfill</button> `);
      {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--> `);
      {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--> `);
      if (taskStatuses.length > 0) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<div class="mt-8"><h3 class="text-lg font-medium text-white mb-4">Task Status</h3> <div class="overflow-x-auto"><table class="w-full text-left border-collapse"><thead><tr class="border-b border-slate-600"><th class="p-2 text-slate-400">Name</th><th class="p-2 text-slate-400">Status</th><th class="p-2 text-slate-400">Last Run</th></tr></thead><tbody><!--[-->`);
        const each_array_2 = ensure_array_like(taskStatuses);
        for (let $$index_2 = 0, $$length = each_array_2.length; $$index_2 < $$length; $$index_2++) {
          let task = each_array_2[$$index_2];
          $$renderer2.push(`<tr class="border-b border-slate-700/50 hover:bg-slate-800/30"><td class="p-2">${escape_html(task.name)}</td><td class="p-2"><span${attr_class(`px-2 py-1 rounded text-xs ${stringify(task.status === "running" ? "bg-blue-900 text-blue-300" : "bg-slate-700 text-slate-300")}`)}>${escape_html(task.status)}</span></td><td class="p-2 text-sm text-slate-400">${escape_html(formatDateTime(task.last_run) || "-")}</td></tr>`);
        }
        $$renderer2.push(`<!--]--></tbody></table></div></div>`);
      } else {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--></div>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    if (activeTab === "symbols") {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="space-y-6"><div class="space-y-2 max-w-md"><label for="symbols-provider" class="block text-sm font-medium text-slate-300">Provider</label> `);
      $$renderer2.select(
        {
          id: "symbols-provider",
          value: symbolsProvider,
          class: "w-full bg-slate-800 border border-slate-700 rounded p-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
        },
        ($$renderer3) => {
          $$renderer3.option({ value: "cnb" }, ($$renderer4) => {
            $$renderer4.push(`CNB`);
          });
          $$renderer3.option({ value: "fcs" }, ($$renderer4) => {
            $$renderer4.push(`FCS`);
          });
        }
      );
      $$renderer2.push(`</div> <button class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium transition-colors">Refresh Symbols</button> `);
      {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--> `);
      {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--></div>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    if (activeTab === "backups") {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="space-y-6"><div class="bg-slate-800 p-4 rounded border border-slate-700"><h3 class="text-lg font-medium text-white mb-4">Create</h3> <button class="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded font-medium transition-colors">Create New Backup</button></div> <div class="bg-slate-800 p-4 rounded border border-slate-700"><h3 class="text-lg font-medium text-white mb-4">Restore</h3> <div class="flex gap-4">`);
      $$renderer2.select(
        {
          value: selectedBackup,
          class: "flex-1 bg-slate-900 border border-slate-700 rounded p-2 text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
        },
        ($$renderer3) => {
          if (backups.length === 0) {
            $$renderer3.push("<!--[-->");
            $$renderer3.option({ value: null, disabled: true }, ($$renderer4) => {
              $$renderer4.push(`No backups available`);
            });
          } else {
            $$renderer3.push("<!--[!-->");
            $$renderer3.push(`<!--[-->`);
            const each_array_3 = ensure_array_like(backups);
            for (let $$index_3 = 0, $$length = each_array_3.length; $$index_3 < $$length; $$index_3++) {
              let backup = each_array_3[$$index_3];
              $$renderer3.option({ value: backup }, ($$renderer4) => {
                $$renderer4.push(`${escape_html(backup.filename)} (${escape_html(formatDateTime(backup.timestamp))})`);
              });
            }
            $$renderer3.push(`<!--]-->`);
          }
          $$renderer3.push(`<!--]-->`);
        }
      );
      $$renderer2.push(` <button${attr("disabled", !selectedBackup, true)} class="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded font-medium transition-colors">Restore</button></div></div> `);
      {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--> `);
      {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--> <div class="mt-4"><h3 class="text-sm font-medium text-slate-400 mb-2">Available Backups</h3> <ul class="space-y-1 text-sm text-slate-300"><!--[-->`);
      const each_array_4 = ensure_array_like(backups);
      for (let $$index_4 = 0, $$length = each_array_4.length; $$index_4 < $$length; $$index_4++) {
        let backup = each_array_4[$$index_4];
        $$renderer2.push(`<li class="p-2 hover:bg-slate-800 rounded flex justify-between items-center"><span>${escape_html(backup.filename)}</span> <span class="text-xs text-slate-500">${escape_html(formatDateTime(backup.timestamp))}</span></li>`);
      }
      $$renderer2.push(`<!--]--></ul></div></div>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div></div></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
export {
  _page as default
};
