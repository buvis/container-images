import "clsx";
import { i as isCrypto } from "../../../../chunks/formatters.js";
function _page($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let fromProviders, toProviders, favoriteKeys;
    let symbols = [];
    let favorites = [];
    let fromCurrency = "";
    let intermediateCurrency = "";
    let toCurrency = "";
    let fromProvider = "";
    let toProvider = "";
    (/* @__PURE__ */ new Date()).toISOString().split("T")[0];
    function getProvidersForLeg(base, quote) {
      return [];
    }
    function isFavoriteProvider(base, quote, provider) {
      const direct = `${base}${quote}`;
      const inverted = `${quote}${base}`;
      for (const s of symbols) {
        if ((s.symbol === direct || s.symbol === inverted) && s.provider === provider) {
          if (favoriteKeys.has(`${provider}:${s.provider_symbol}`)) return true;
        }
      }
      return false;
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
    [
      ...new Set(symbols.flatMap((s) => {
        const parts = getSymbolParts(s.symbol);
        return [parts.from, parts.to];
      }))
    ].sort();
    fromProviders = getProvidersForLeg();
    toProviders = getProvidersForLeg();
    favoriteKeys = new Set(favorites.map((f) => `${f.provider}:${f.provider_symbol}`));
    {
      if (fromProviders.length > 0 && !fromProviders.includes(fromProvider)) {
        const fav = fromProviders.find((p) => isFavoriteProvider(fromCurrency, intermediateCurrency, p));
        fromProvider = fav || fromProviders[0];
      }
      if (fromProviders.length === 0) fromProvider = "";
    }
    {
      if (toProviders.length > 0 && !toProviders.includes(toProvider)) {
        const fav = toProviders.find((p) => isFavoriteProvider(intermediateCurrency, toCurrency, p));
        toProvider = fav || toProviders[0];
      }
      if (toProviders.length === 0) toProvider = "";
    }
    isCrypto(fromCurrency) ? "crypto" : "forex";
    $$renderer2.push(`<div class="bg-slate-950 text-slate-200 p-6"><header class="mb-8"><h1 class="text-3xl font-bold text-white">Chain Converter</h1></header> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="max-w-2xl mx-auto"><div class="bg-slate-900 p-8 rounded-xl border border-slate-800 animate-pulse h-96"></div></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
export {
  _page as default
};
