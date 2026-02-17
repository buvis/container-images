import { $ as attr, a1 as bind_props } from "./index2.js";
function SearchInput($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let { value = "", placeholder = "Search...", debounceMs = 300 } = $$props;
    let inputValue = value;
    $$renderer2.push(`<input type="text"${attr("value", inputValue)}${attr("placeholder", placeholder)} class="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-slate-500 focus:ring-1 focus:ring-slate-500"/>`);
    bind_props($$props, { value });
  });
}
export {
  SearchInput as S
};
