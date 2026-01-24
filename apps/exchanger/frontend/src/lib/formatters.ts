export function formatDateTime(date: string | null | undefined): string | null {
    if (!date) return null;
    try {
        const d = new Date(date);
        // invalid date check
        if (isNaN(d.getTime())) return date;

        return d.toLocaleString(undefined, {
            year: 'numeric',
            month: 'numeric',
            day: 'numeric',
            hour: 'numeric',
            minute: 'numeric',
            second: 'numeric',
        });
    } catch (e) {
        return date;
    }
}

const CRYPTO_CURRENCIES = new Set([
    'BTC', 'ETH', 'XRP', 'LTC', 'BCH', 'DOGE', 'ADA', 'DOT', 'SOL', 'AVAX',
    'MATIC', 'LINK', 'UNI', 'ATOM', 'XLM', 'ALGO', 'VET', 'FIL', 'TRX', 'ETC',
    'XMR', 'AAVE', 'MKR', 'COMP', 'SNX', 'SUSHI', 'YFI', 'CRV', 'BAL', 'REN'
]);

/**
 * Get appropriate decimal places for displaying a rate value.
 * Base: crypto=8, forex=4. Adjusted by magnitude.
 */
export function getRateDecimals(rate: number, type: 'forex' | 'crypto'): number {
    const base = type === 'crypto' ? 8 : 4;
    if (rate < 0.0001) return Math.max(base, 6);
    if (rate > 1000) return Math.min(base, 2);
    return base;
}

/**
 * Get appropriate decimal places for displaying conversion result.
 * Fiat currencies get 2, crypto gets 8.
 */
export function getResultDecimals(currency: string): number {
    return CRYPTO_CURRENCIES.has(currency.toUpperCase()) ? 8 : 2;
}

/**
 * Check if a currency code is a cryptocurrency.
 */
export function isCrypto(currency: string): boolean {
    return CRYPTO_CURRENCIES.has(currency.toUpperCase());
}

/**
 * Format a rate value with smart decimal places.
 */
export function formatRate(rate: number | null, type: 'forex' | 'crypto' = 'forex'): string {
    if (rate === null) return 'N/A';
    const decimals = getRateDecimals(rate, type);
    return rate.toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: decimals
    });
}

/**
 * Format a conversion result with appropriate decimals for the target currency.
 */
export function formatResult(value: number | null, targetCurrency: string): string {
    if (value === null) return 'N/A';
    const decimals = getResultDecimals(targetCurrency);
    return value.toLocaleString(undefined, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}
