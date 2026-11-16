import type { AssetUrls } from './asset-urls';
import { parseLanguagePack, parsePackIndex } from './parse-pack';
import type { LanguagePack, PackIndex } from './types';

export class PackLoadError extends Error {
  constructor(url: string, cause: unknown) {
    super(`Could not load ${url}`, { cause });
    this.name = 'PackLoadError';
  }
}

async function fetchJson(url: string, fetchImpl: typeof fetch): Promise<unknown> {
  let response: Response;
  try {
    response = await fetchImpl(url, { credentials: 'omit' });
  } catch (error) {
    throw new PackLoadError(url, error);
  }
  if (!response.ok) throw new PackLoadError(url, new Error(`HTTP ${response.status}`));
  return response.json();
}

export async function loadPackIndex(
  urls: AssetUrls,
  fetchImpl: typeof fetch = fetch,
): Promise<PackIndex> {
  return parsePackIndex(await fetchJson(urls.packIndex(), fetchImpl));
}

export async function loadLanguagePack(
  code: string,
  urls: AssetUrls,
  fetchImpl: typeof fetch = fetch,
): Promise<LanguagePack> {
  return parseLanguagePack(await fetchJson(urls.pack(code), fetchImpl));
}
