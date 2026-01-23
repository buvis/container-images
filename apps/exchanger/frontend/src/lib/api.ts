export interface TaskState {
    name: string;
    schedule: string;
    next_run: string | null;
    last_run: string | null;
    status: string;
    error: string | null;
}

export interface Rate {
    symbol: string;
    base: string;
    date: string;
    rate: number;
    provider: string;
}

export interface ProviderStatus {
    name: string;
    healthy: boolean;
    symbol_count: number;
}

export interface BackupInfo {
    filename: string;
    timestamp: string;
}

const API_BASE = '/api';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
    const response = await fetch(url, options);
    if (!response.ok) {
        throw new Error(`API request failed: ${response.status} ${response.statusText}`);
    }
    return response.json();
}

export async function getHealth(): Promise<{ status: string }> {
    return fetchJson(`${API_BASE}/health`);
}

export async function getTaskStatus(): Promise<TaskState[]> {
    return fetchJson(`${API_BASE}/task_status`);
}

export async function getRates(date: string, provider?: string): Promise<Rate[]> {
    const params = new URLSearchParams({ date });
    if (provider) params.append('provider', provider);
    return fetchJson(`${API_BASE}/rates?${params.toString()}`);
}

export async function getRatesHistory(
    symbol: string,
    fromDate: string,
    toDate: string,
    provider?: string
): Promise<{ date: string; rate: number | null }[]> {
    const params = new URLSearchParams({ symbol, from_date: fromDate, to_date: toDate });
    if (provider) params.append('provider', provider);
    return fetchJson(`${API_BASE}/rates/history?${params.toString()}`);
}

export async function getCoverage(year: number, provider?: string): Promise<Record<string, number>> {
    const params = new URLSearchParams({ year: year.toString() });
    if (provider) params.append('provider', provider);
    return fetchJson(`${API_BASE}/rates/coverage?${params.toString()}`);
}

export async function getFavorites(): Promise<string[]> {
    return fetchJson(`${API_BASE}/favorites`);
}

export async function addFavorite(symbol: string): Promise<void> {
    await fetchJson(`${API_BASE}/favorites`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol })
    });
}

export async function removeFavorite(symbol: string): Promise<void> {
    await fetchJson(`${API_BASE}/favorites/${symbol}`, {
        method: 'DELETE'
    });
}

export async function getProvidersStatus(): Promise<ProviderStatus[]> {
    return fetchJson(`${API_BASE}/providers/status`);
}

export async function triggerBackfill(provider: string, length: number, symbols?: string[]): Promise<void> {
    const params = new URLSearchParams({ provider, length: length.toString() });
    if (symbols?.length) params.append('symbols', symbols.join(','));
    await fetchJson(`${API_BASE}/backfill?${params.toString()}`, {
        method: 'POST'
    });
}

export async function populateSymbols(provider: string): Promise<void> {
    await fetchJson(`${API_BASE}/populate_symbols?provider=${encodeURIComponent(provider)}`, {
        method: 'POST'
    });
}

export async function getBackups(): Promise<string[]> {
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
