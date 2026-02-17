import "clsx";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let favoriteKeys, selectedSymbolData, symbolParts;
    let symbols = [];
    let favorites = [];
    let selectedSymbol = "";
    (/* @__PURE__ */ new Date()).toISOString().split("T")[0];
    function isFavorite(s) {
      return favoriteKeys.has(`${s.provider}:${s.provider_symbol}`);
    }
    function getSymbolParts(symbol) {
      if (symbol.includes("/")) {
        const [from, to] = symbol.split("/");
        return { from, to };
      }
      if (symbol.length === 6) {
        return { from: symbol.slice(0, 3), to: symbol.slice(3) };
      }
      return { from: symbol, to: "?" };
    }
    favoriteKeys = new Set(favorites.map((f) => `${f.provider}:${f.provider_symbol}`));
    symbols.filter((s) => isFavorite(s));
    symbols.filter((s) => !isFavorite(s));
    selectedSymbolData = symbols.find((s) => s.symbol === selectedSymbol);
    selectedSymbolData?.type === "crypto" ? "crypto" : "forex";
    symbolParts = getSymbolParts(selectedSymbol);
    symbolParts.from;
    symbolParts.to;
    $$renderer2.push(`<div class="bg-slate-950 text-slate-200 p-6"><header class="mb-8"><div class="flex items-center justify-between"><h1 class="text-3xl font-bold text-white">Converter</h1> <a href="/converter/multi" class="text-sm text-slate-400 hover:text-cyan-400 transition-colors flex items-center gap-1">Chain Converter <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clip-rule="evenodd"></path></svg></a></div></header> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="max-w-xl mx-auto"><div class="bg-slate-900 p-8 rounded-xl border border-slate-800 animate-pulse h-64"></div></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
export {
  _page as default
};
