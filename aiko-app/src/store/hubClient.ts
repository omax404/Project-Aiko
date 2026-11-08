/**
 * aiko-app/src/store/hubClient.ts
 * Neural Hub endpoint discovery and zero-trust token retrieval.
 */

function getConfiguredHubUrl(): string {
  if (
    typeof window !== 'undefined' &&
    window.location.hostname !== 'localhost' &&
    window.location.hostname !== '127.0.0.1'
  ) {
    if (!window.location.port || window.location.port !== '1422') {
      return window.location.origin;
    }
  }
  const envPort = (import.meta as any).env?.VITE_AIKO_PORT;
  if (envPort) {
    return `http://127.0.0.1:${envPort}`;
  }
  return 'http://127.0.0.1:8000';
}

let hubUrl = getConfiguredHubUrl();
let wsToken: string | null = null;

export const getHubUrl = (): string => hubUrl;
export const setHubUrl = (url: string): void => {
  hubUrl = url;
};
export const getCachedToken = (): string | null => wsToken;
export const setCachedToken = (token: string | null): void => {
  wsToken = token;
};

/** Get the desktop owner token through Tauri IPC, or a limited browser token. */
export async function fetchLocalToken(): Promise<string | null> {
  if (typeof window !== 'undefined' && !!(window as any).__TAURI__) {
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      return await invoke<string>('get_local_auth_token');
    } catch (e) {
      console.warn('[Aiko] Could not retrieve desktop auth token:', e);
    }
  }
  try {
    const res = await fetch(`${hubUrl}/token`, { cache: 'no-store' });
    if (res.ok) {
      const json = await res.json();
      return json.token as string;
    }
  } catch (e) {
    console.warn('[Aiko] Could not fetch local auth token:', e);
  }
  return null;
}

/** Probe the supported Neural Hub port range and reuse the active endpoint. */
export async function findActiveHubUrl(): Promise<string> {
  const defaultUrl = hubUrl || getHubUrl();

  try {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), 600);
    const res = await fetch(`${defaultUrl}/status`, { signal: controller.signal });
    clearTimeout(id);
    if (res.ok) return defaultUrl;
  } catch (_) {}

  for (let port = 8000; port < 8050; port++) {
    const candidate = `http://127.0.0.1:${port}`;
    if (candidate === defaultUrl) continue;
    try {
      const controller = new AbortController();
      const id = setTimeout(() => controller.abort(), 400);
      const res = await fetch(`${candidate}/status`, { signal: controller.signal });
      clearTimeout(id);
      if (res.ok) {
        console.log(`[Aiko] Neural Hub automatically discovered on port ${port}`);
        return candidate;
      }
    } catch (_) {}
  }
  return defaultUrl;
}

export async function resolveHubUrl(): Promise<string> {
  hubUrl = await findActiveHubUrl();
  return hubUrl;
}

/** Build Authorization headers with the local JWT token for API calls. */
export async function getAuthHeaders(
  extraHeaders: Record<string, string> = {},
  forceRefresh = false
): Promise<Record<string, string>> {
  if (!wsToken || forceRefresh) {
    hubUrl = await findActiveHubUrl();
    wsToken = await fetchLocalToken();
  }
  const headers: Record<string, string> = { ...extraHeaders };
  if (wsToken) {
    headers['Authorization'] = `Bearer ${wsToken}`;
  }
  return headers;
}
