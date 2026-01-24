export interface TaskState {
    name: string;
    status: string;
    message: string;
    last_run: string | null;
    error: string | null;
    per_symbol: Record<string, number> | null;
    rows_written: number | null;
    symbols_added: number | null;
    progress: number | null;
    progress_detail: string | null;
    rate_limit_until: string | null;
}

export interface SymbolItem {
    symbol: string;  // normalized symbol
    name: string;
    provider: string;
    type: string;
    provider_symbol: string;  // provider-specific
}

export interface MultiProviderSymbol {
    symbol: string;  // normalized symbol
    providers: string[];
}

export interface Rate {
    symbol: string;  // normalized symbol
    base: string;
    date: string;
    rate: number;
    provider: string;
    type: 'forex' | 'crypto';
    provider_symbol: string;  // provider-specific
}

export interface ProviderStatus {
    name: string;
    healthy: boolean;
    symbol_count: number;
    symbol_counts_by_type: Record<string, number>;
}

export interface Favorite {
    provider: string;
    provider_symbol: string;
}

export interface BackupInfo {
    filename: string;
    timestamp: string;
}

const API_BASE = '/api';

function deriveBase(symbol: string): string {
    const slashIndex = symbol.indexOf('/');
    if (slashIndex !== -1 && slashIndex < symbol.length - 1) {
        return symbol.slice(slashIndex + 1);
    }
    if (symbol.length > 3) {
        return symbol.slice(-3);
    }
    return symbol;
}

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
    const response = await fetch(url, options);
    if (!response.ok) {
        // Try to extract detail from JSON error response
        let detail: string | undefined;
        try {
            const error = await response.json();
            // detail can be string (HTTPException) or array (validation errors)
            if (typeof error.detail === 'string') {
                detail = error.detail;
            } else if (Array.isArray(error.detail)) {
                // FastAPI validation errors: [{loc, msg, type}, ...]
                detail = error.detail.map((e: { msg?: string }) => e.msg ?? '').join('; ');
            } else if (error.detail) {
                detail = JSON.stringify(error.detail);
            }
        } catch {
            // JSON parse failed, use generic message
        }
        throw new Error(detail ?? `API request failed: ${response.status} ${response.statusText}`);
    }
    return response.json();
}

export async function getSymbols(): Promise<SymbolItem[]> {
    return fetchJson(`${API_BASE}/symbols/list`);
}

export async function getMultiProviderSymbols(): Promise<MultiProviderSymbol[]> {
    return fetchJson(`${API_BASE}/symbols/multi-provider`);
}

export async function getSymbolsByNormalized(normalizedSymbol: string): Promise<SymbolItem[]> {
    return fetchJson(`${API_BASE}/symbols/by-normalized/${encodeURIComponent(normalizedSymbol)}`);
}

export async function getHealth(): Promise<{ status: string }> {
    return fetchJson(`${API_BASE}/health`);
}

export interface FrontendConfig {
    dashboard_history_days: number;
}

export async function getConfig(): Promise<FrontendConfig> {
    return fetchJson(`${API_BASE}/config`);
}

export async function getTaskStatus(): Promise<TaskState[]> {
    const data = await fetchJson<Record<string, Omit<TaskState, 'name'>>>(`${API_BASE}/task_status`);
    return Object.entries(data).map(([name, state]) => ({
        name,
        ...state
    }));
}

export async function getRate(
    date: string,
    symbol: string,
    provider: string = 'all'
): Promise<{ rate: number } | { rates: Record<string, number | null> }> {
    const params = new URLSearchParams({ date, symbol, provider });
    return fetchJson(`${API_BASE}/rates?${params.toString()}`);
}

export async function getRates(
    date: string,
    provider?: string,
    type?: 'forex' | 'crypto'
): Promise<Rate[]> {
    const params = new URLSearchParams({ date, provider: provider ?? 'all' });
    const items = await fetchJson<Array<{ symbol: string; provider_symbol: string; rate: number; provider: string; type: 'forex' | 'crypto' }>>(
        `${API_BASE}/rates/list?${params.toString()}`
    );
    const filtered = type ? items.filter((item) => item.type === type) : items;
    return filtered.map((item) => ({
        symbol: item.symbol,
        base: deriveBase(item.provider_symbol),
        date,
        rate: item.rate,
        provider: item.provider,
        type: item.type,
        provider_symbol: item.provider_symbol
    }));
}

export async function getRatesHistory(
    symbol: string,
    fromDate: string,
    toDate: string,
    provider?: string,
    providerSymbol?: string
): Promise<{ date: string; rate: number | null }[]> {
    const params = new URLSearchParams({ symbol, from_date: fromDate, to_date: toDate });
    if (provider) params.append('provider', provider);
    if (providerSymbol) params.append('provider_symbol', providerSymbol);
    return fetchJson(`${API_BASE}/rates/history?${params.toString()}`);
}

export async function getCoverage(year: number, provider?: string, symbols?: string[]): Promise<Record<string, number>> {
    const params = new URLSearchParams({ year: year.toString() });
    if (provider) params.append('provider', provider);
    if (symbols?.length) params.append('symbols', symbols.join(','));
    return fetchJson(`${API_BASE}/rates/coverage?${params.toString()}`);
}

export async function getMissingSymbols(year: number, symbols: string[], provider?: string): Promise<Record<string, string[]>> {
    if (!symbols.length) return {};
    const params = new URLSearchParams({ year: year.toString(), symbols: symbols.join(',') });
    if (provider) params.append('provider', provider);
    return fetchJson(`${API_BASE}/rates/missing?${params.toString()}`);
}

export async function getFavorites(): Promise<Favorite[]> {
    return fetchJson(`${API_BASE}/favorites`);
}

export async function addFavorite(provider: string, providerSymbol: string): Promise<void> {
    await fetchJson(`${API_BASE}/favorites`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, provider_symbol: providerSymbol })
    });
}

export async function removeFavorite(provider: string, providerSymbol: string): Promise<void> {
    await fetchJson(`${API_BASE}/favorites/${encodeURIComponent(provider)}/${encodeURIComponent(providerSymbol)}`, {
        method: 'DELETE'
    });
}

export async function getProvidersStatus(): Promise<ProviderStatus[]> {
    return fetchJson(`${API_BASE}/providers/status`);
}

export interface ScheduledResponse {
    scheduled: boolean;
    message: string;
    started?: string[];
    already_running?: string[];
}

export async function triggerBackfill(provider: string, length: number, symbols?: string[]): Promise<ScheduledResponse> {
    const params = new URLSearchParams({ provider, length: length.toString() });
    if (symbols?.length) params.append('symbols', symbols.join(','));
    return fetchJson(`${API_BASE}/backfill?${params.toString()}`, {
        method: 'POST'
    });
}

export async function populateSymbols(provider: string): Promise<void> {
    await fetchJson(`${API_BASE}/populate_symbols?provider=${encodeURIComponent(provider)}`, {
        method: 'POST'
    });
}

export async function getBackups(): Promise<BackupInfo[]> {
    return fetchJson(`${API_BASE}/backups`);
}

export async function createBackup(): Promise<{ filename: string }> {
    return fetchJson(`${API_BASE}/backup`, {
        method: 'POST'
    });
}

export async function restoreBackup(timestamp: string): Promise<void> {
    await fetchJson(`${API_BASE}/restore?timestamp=${encodeURIComponent(timestamp)}`, {
        method: 'POST'
    });
}

export interface ChainRate {
    from_rate: number | null;
    from_provider: string;
    from_symbol: string;
    from_inverted: boolean;
    to_rate: number | null;
    to_provider: string;
    to_symbol: string;
    to_inverted: boolean;
    combined_rate: number | null;
    intermediate: string;
}

export async function getChainRate(
    date: string,
    fromCurrency: string,
    intermediate: string,
    toCurrency: string,
    fromProvider: string,
    toProvider: string
): Promise<ChainRate> {
    const params = new URLSearchParams({
        date,
        from_currency: fromCurrency,
        intermediate,
        to_currency: toCurrency,
        from_provider: fromProvider,
        to_provider: toProvider
    });
    return fetchJson(`${API_BASE}/rates/chain?${params.toString()}`);
}
