import { Z as attr_class, _ as ensure_array_like, $ as attr, a0 as stringify, a1 as bind_props, a2 as store_get, a3 as unsubscribe_stores, a4 as head } from "../../chunks/index2.js";
import { p as page } from "../../chunks/stores.js";
import { e as escape_html } from "../../chunks/context.js";
const favicon = "data:image/svg+xml,%3csvg%20xmlns='http://www.w3.org/2000/svg'%20width='107'%20height='128'%20viewBox='0%200%20107%20128'%3e%3ctitle%3esvelte-logo%3c/title%3e%3cpath%20d='M94.157%2022.819c-10.4-14.885-30.94-19.297-45.792-9.835L22.282%2029.608A29.92%2029.92%200%200%200%208.764%2049.65a31.5%2031.5%200%200%200%203.108%2020.231%2030%2030%200%200%200-4.477%2011.183%2031.9%2031.9%200%200%200%205.448%2024.116c10.402%2014.887%2030.942%2019.297%2045.791%209.835l26.083-16.624A29.92%2029.92%200%200%200%2098.235%2078.35a31.53%2031.53%200%200%200-3.105-20.232%2030%2030%200%200%200%204.474-11.182%2031.88%2031.88%200%200%200-5.447-24.116'%20style='fill:%23ff3e00'/%3e%3cpath%20d='M45.817%20106.582a20.72%2020.72%200%200%201-22.237-8.243%2019.17%2019.17%200%200%201-3.277-14.503%2018%2018%200%200%201%20.624-2.435l.49-1.498%201.337.981a33.6%2033.6%200%200%200%2010.203%205.098l.97.294-.09.968a5.85%205.85%200%200%200%201.052%203.878%206.24%206.24%200%200%200%206.695%202.485%205.8%205.8%200%200%200%201.603-.704L69.27%2076.28a5.43%205.43%200%200%200%202.45-3.631%205.8%205.8%200%200%200-.987-4.371%206.24%206.24%200%200%200-6.698-2.487%205.7%205.7%200%200%200-1.6.704l-9.953%206.345a19%2019%200%200%201-5.296%202.326%2020.72%2020.72%200%200%201-22.237-8.243%2019.17%2019.17%200%200%201-3.277-14.502%2017.99%2017.99%200%200%201%208.13-12.052l26.081-16.623a19%2019%200%200%201%205.3-2.329%2020.72%2020.72%200%200%201%2022.237%208.243%2019.17%2019.17%200%200%201%203.277%2014.503%2018%2018%200%200%201-.624%202.435l-.49%201.498-1.337-.98a33.6%2033.6%200%200%200-10.203-5.1l-.97-.294.09-.968a5.86%205.86%200%200%200-1.052-3.878%206.24%206.24%200%200%200-6.696-2.485%205.8%205.8%200%200%200-1.602.704L37.73%2051.72a5.42%205.42%200%200%200-2.449%203.63%205.79%205.79%200%200%200%20.986%204.372%206.24%206.24%200%200%200%206.698%202.486%205.8%205.8%200%200%200%201.602-.704l9.952-6.342a19%2019%200%200%201%205.295-2.328%2020.72%2020.72%200%200%201%2022.237%208.242%2019.17%2019.17%200%200%201%203.277%2014.503%2018%2018%200%200%201-8.13%2012.053l-26.081%2016.622a19%2019%200%200%201-5.3%202.328'%20style='fill:%23fff'/%3e%3c/svg%3e";
function Sidebar($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    let { isOpen = false } = $$props;
    function isActive(href) {
      const [path, query] = href.split("?");
      if (store_get($$store_subs ??= {}, "$page", page).url.pathname !== path) return false;
      if (!query) return true;
      const params = new URLSearchParams(query);
      for (const [key, value] of params) {
        if (store_get($$store_subs ??= {}, "$page", page).url.searchParams.get(key) !== value) return false;
      }
      return true;
    }
    const navItems = [
      {
        section: "Overview",
        items: [
          { label: "Status", href: "/" },
          { label: "Market", href: "/market" }
        ]
      },
      {
        section: "Tools",
        items: [
          { label: "Symbols", href: "/symbols" },
          { label: "Rates", href: "/rates" },
          { label: "Converter", href: "/converter" },
          { label: "Chain Converter", href: "/converter/multi" },
          { label: "Compare", href: "/compare" }
        ]
      },
      {
        section: "Administration",
        items: [
          { label: "Backfill", href: "/admin?tab=backfill" },
          { label: "Symbols", href: "/admin?tab=symbols" },
          { label: "Backups", href: "/admin?tab=backups" }
        ]
      }
    ];
    $$renderer2.push(`<aside${attr_class(`fixed inset-y-0 left-0 z-50 w-64 bg-[#1E293B] border-r border-slate-700 text-white transition-transform duration-300 ease-in-out lg:static lg:translate-x-0 ${stringify(isOpen ? "translate-x-0" : "-translate-x-full")}`)}><div class="flex h-16 items-center justify-between px-6 border-b border-slate-700"><span class="text-xl font-bold tracking-tight">Exchanger</span> <button class="lg:hidden p-1 rounded hover:bg-slate-700" aria-label="Close sidebar"><svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg></button></div> <nav class="p-4 space-y-6 overflow-y-auto h-[calc(100vh-4rem)]"><!--[-->`);
    const each_array = ensure_array_like(navItems);
    for (let $$index_1 = 0, $$length = each_array.length; $$index_1 < $$length; $$index_1++) {
      let group = each_array[$$index_1];
      $$renderer2.push(`<div><h3 class="mb-2 px-2 text-xs font-semibold uppercase tracking-wider text-slate-400">${escape_html(group.section)}</h3> <ul class="space-y-1"><!--[-->`);
      const each_array_1 = ensure_array_like(group.items);
      for (let $$index = 0, $$length2 = each_array_1.length; $$index < $$length2; $$index++) {
        let item = each_array_1[$$index];
        $$renderer2.push(`<li><a${attr("href", item.href)}${attr_class(`block rounded-md px-2 py-2 text-sm font-medium transition-colors hover:bg-slate-700/50 hover:text-white ${stringify(isActive(item.href) ? "bg-slate-700 text-white" : "text-slate-300")}`)}>${escape_html(item.label)}</a></li>`);
      }
      $$renderer2.push(`<!--]--></ul></div>`);
    }
    $$renderer2.push(`<!--]--></nav></aside> `);
    if (isOpen) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm lg:hidden transition-opacity duration-300" role="button" tabindex="0" aria-label="Close sidebar"></div>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]-->`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
    bind_props($$props, { isOpen });
  });
}
function _layout($$renderer, $$props) {
  let { children } = $$props;
  let isSidebarOpen = false;
  let $$settled = true;
  let $$inner_renderer;
  function $$render_inner($$renderer2) {
    head("12qhfyh", $$renderer2, ($$renderer3) => {
      $$renderer3.push(`<link rel="icon"${attr("href", favicon)}/>`);
    });
    $$renderer2.push(`<div class="flex min-h-screen bg-[#0F172A] text-slate-100">`);
    Sidebar($$renderer2, {
      get isOpen() {
        return isSidebarOpen;
      },
      set isOpen($$value) {
        isSidebarOpen = $$value;
        $$settled = false;
      }
    });
    $$renderer2.push(`<!----> <div class="flex-1 flex flex-col min-w-0"><header class="lg:hidden flex items-center h-16 px-4 border-b border-slate-800 bg-[#1E293B]"><button class="text-white p-2 -ml-2 rounded-md hover:bg-slate-700/50" aria-label="Open sidebar"><svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path></svg></button> <span class="ml-4 font-bold text-lg">Exchanger</span></header> <main class="flex-1 p-4 lg:p-8">`);
    children($$renderer2);
    $$renderer2.push(`<!----></main></div></div>`);
  }
  do {
    $$settled = true;
    $$inner_renderer = $$renderer.copy();
    $$render_inner($$inner_renderer);
  } while (!$$settled);
  $$renderer.subsume($$inner_renderer);
}
export {
  _layout as default
};
