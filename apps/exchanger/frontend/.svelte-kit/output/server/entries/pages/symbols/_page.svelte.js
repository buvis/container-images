import { Z as attr_class, a0 as stringify, _ as ensure_array_like, a1 as bind_props } from "../../../chunks/index2.js";
import { S as SearchInput } from "../../../chunks/SearchInput.js";
import { e as escape_html } from "../../../chunks/context.js";
function FilterPills($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let { options, selected = /* @__PURE__ */ new Set() } = $$props;
    function getName(opt) {
      return typeof opt === "string" ? opt : opt.name;
    }
    function getCount(opt) {
      return typeof opt === "string" ? void 0 : opt.count;
    }
    let totalCount = options.reduce((sum, opt) => sum + (getCount(opt) ?? 0), 0);
    let hasAnyCounts = options.some((opt) => getCount(opt) !== void 0);
    $$renderer2.push(`<div class="flex flex-wrap gap-2"><button type="button"${attr_class(`px-3 py-1.5 text-sm font-medium rounded-lg border transition-colors ${stringify(selected.size === 0 ? "bg-slate-700 border-slate-600 text-white" : "bg-slate-900 border-slate-700 text-slate-400 hover:text-slate-200 hover:border-slate-600")}`)}>All `);
    if (hasAnyCounts) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<span class="ml-1 text-xs text-slate-500">(${escape_html(totalCount)})</span>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></button> <!--[-->`);
    const each_array = ensure_array_like(options);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let opt = each_array[$$index];
      const name = getName(opt);
      const count = getCount(opt);
      $$renderer2.push(`<button type="button"${attr_class(`px-3 py-1.5 text-sm font-medium rounded-lg border transition-colors ${stringify(selected.has(name) ? "bg-slate-700 border-slate-600 text-white" : "bg-slate-900 border-slate-700 text-slate-400 hover:text-slate-200 hover:border-slate-600")}`)}>${escape_html(name)} `);
      if (count !== void 0) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<span class="ml-1 text-xs text-slate-500">(${escape_html(count)})</span>`);
      } else {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--></button>`);
    }
    $$renderer2.push(`<!--]--></div>`);
    bind_props($$props, { selected });
  });
}
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let searchFiltered, typeOptions, providerOptions, filtered;
    let symbols = [];
    let favorites = [];
    let providers = [];
    let selectedProviders = /* @__PURE__ */ new Set();
    let search = "";
    let selectedTypes = /* @__PURE__ */ new Set();
    searchFiltered = symbols.filter((s) => !search || s.symbol.toLowerCase().includes(search.toLowerCase()) || s.name.toLowerCase().includes(search.toLowerCase()));
    typeOptions = (() => {
      const base = searchFiltered.filter((s) => selectedProviders.size === 0 || selectedProviders.has(s.provider));
      return [
        {
          name: "forex",
          count: base.filter((s) => s.type === "forex").length
        },
        {
          name: "crypto",
          count: base.filter((s) => s.type === "crypto").length
        }
      ];
    })();
    providerOptions = (() => {
      const base = searchFiltered.filter((s) => selectedTypes.size === 0 || selectedTypes.has(s.type));
      return providers.map((p) => ({
        name: p.name,
        count: base.filter((s) => s.provider === p.name).length
      }));
    })();
    filtered = symbols.filter((s) => {
      const matchesProvider = selectedProviders.size === 0 || selectedProviders.has(s.provider);
      const matchesType = selectedTypes.size === 0 || selectedTypes.has(s.type);
      const matchesSearch = !search || s.symbol.toLowerCase().includes(search.toLowerCase()) || s.name.toLowerCase().includes(search.toLowerCase());
      return matchesProvider && matchesType && matchesSearch;
    });
    filtered.reduce(
      (acc, s) => {
        const key = s.provider;
        if (!acc[key]) acc[key] = [];
        acc[key].push(s);
        return acc;
      },
      {}
    );
    new Set(favorites.map((f) => `${f.provider}:${f.provider_symbol}`));
    let $$settled = true;
    let $$inner_renderer;
    function $$render_inner($$renderer3) {
      $$renderer3.push(`<div class="bg-slate-950 text-slate-200 p-6"><header class="mb-6"><h1 class="text-3xl font-bold text-white mb-4">Symbols</h1> <div class="flex flex-col gap-4">`);
      SearchInput($$renderer3, {
        placeholder: "Search symbols...",
        get value() {
          return search;
        },
        set value($$value) {
          search = $$value;
          $$settled = false;
        }
      });
      $$renderer3.push(`<!----> <div class="flex flex-col sm:flex-row gap-4 items-start sm:items-center">`);
      FilterPills($$renderer3, {
        options: typeOptions,
        get selected() {
          return selectedTypes;
        },
        set selected($$value) {
          selectedTypes = $$value;
          $$settled = false;
        }
      });
      $$renderer3.push(`<!----> <div class="hidden sm:block w-px h-6 bg-slate-800"></div> <div class="flex-1">`);
      FilterPills($$renderer3, {
        options: providerOptions,
        get selected() {
          return selectedProviders;
        },
        set selected($$value) {
          selectedProviders = $$value;
          $$settled = false;
        }
      });
      $$renderer3.push(`<!----></div></div></div></header> `);
      {
        $$renderer3.push("<!--[-->");
        $$renderer3.push(`<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"><!--[-->`);
        const each_array = ensure_array_like(Array(9));
        for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
          each_array[$$index];
          $$renderer3.push(`<div class="bg-slate-900 p-4 rounded-lg border border-slate-800 animate-pulse h-20"></div>`);
        }
        $$renderer3.push(`<!--]--></div>`);
      }
      $$renderer3.push(`<!--]--></div>`);
    }
    do {
      $$settled = true;
      $$inner_renderer = $$renderer2.copy();
      $$render_inner($$inner_renderer);
    } while (!$$settled);
    $$renderer2.subsume($$inner_renderer);
  });
}
export {
  _page as default
};
