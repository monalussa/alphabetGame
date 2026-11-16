import { describe, expect, it, vi } from 'vitest';
import { createAssetUrls } from '../../src/core/content/asset-urls';
import { PackLoadError, loadLanguagePack } from '../../src/core/content/load-pack';

describe('createAssetUrls', () => {
  const urls = createAssetUrls('/');

  it('builds same-origin paths for every asset type', () => {
    expect(urls.pack('fr')).toBe('/packs/fr.json');
    expect(urls.clip('fr', 'word_ananas')).toBe('/packs/fr/audio/word_ananas.mp3');
    expect(urls.character('fr', 'char_a')).toBe('/packs/fr/characters/char_a.svg');
    expect(urls.image('pineapple')).toBe('/images/pineapple.svg');
    expect(urls.funSound('fun_boing')).toBe('/sounds/fun_boing.mp3');
  });

  it('respects a base path without trailing slash', () => {
    expect(createAssetUrls('/alphabet').pack('hr')).toBe('/alphabet/packs/hr.json');
  });

  it.each(['../x', 'a/b', '', 'x'.repeat(41)])('refuses unsafe id %j', (id) => {
    expect(() => urls.clip('fr', id)).toThrow(/Refusing/);
  });

  it('refuses an invalid language code', () => {
    expect(() => urls.pack('../fr')).toThrow(/Refusing/);
  });
});

describe('loadLanguagePack', () => {
  const urls = createAssetUrls('/');

  it('wraps HTTP errors in PackLoadError', async () => {
    const fetchStub = vi.fn<typeof fetch>().mockResolvedValue(new Response('', { status: 404 }));

    await expect(loadLanguagePack('fr', urls, fetchStub)).rejects.toBeInstanceOf(PackLoadError);
  });

  it('wraps network failures in PackLoadError', async () => {
    const fetchStub = vi.fn<typeof fetch>().mockRejectedValue(new TypeError('offline'));

    await expect(loadLanguagePack('fr', urls, fetchStub)).rejects.toBeInstanceOf(PackLoadError);
  });

  it('never sends credentials', async () => {
    const fetchStub = vi.fn<typeof fetch>().mockResolvedValue(new Response('{}'));

    await loadLanguagePack('fr', urls, fetchStub).catch(() => undefined);

    expect(fetchStub).toHaveBeenCalledWith('/packs/fr.json', { credentials: 'omit' });
  });
});
