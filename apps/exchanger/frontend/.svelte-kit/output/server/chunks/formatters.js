function formatDateTime(date) {
  if (!date) return null;
  try {
    const d = new Date(date);
    if (isNaN(d.getTime())) return date;
    return d.toLocaleString(void 0, {
      year: "numeric",
      month: "numeric",
      day: "numeric",
      hour: "numeric",
      minute: "numeric",
      second: "numeric"
    });
  } catch (e) {
    return date;
  }
}
const CRYPTO_CURRENCIES = /* @__PURE__ */ new Set([
  "BTC",
  "ETH",
  "XRP",
  "LTC",
  "BCH",
  "DOGE",
  "ADA",
  "DOT",
  "SOL",
  "AVAX",
  "MATIC",
  "LINK",
  "UNI",
  "ATOM",
  "XLM",
  "ALGO",
  "VET",
  "FIL",
  "TRX",
  "ETC",
  "XMR",
  "AAVE",
  "MKR",
  "COMP",
  "SNX",
  "SUSHI",
  "YFI",
  "CRV",
  "BAL",
  "REN"
]);
function isCrypto(currency) {
  return CRYPTO_CURRENCIES.has(currency.toUpperCase());
}
export {
  formatDateTime as f,
  isCrypto as i
};
