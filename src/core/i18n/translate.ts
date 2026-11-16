import type { LanguagePack } from '../content/types';

/** Looks up a UI string; falls back to the key so a missing string is visible, never blank. */
export function createTranslator(pack: LanguagePack): (key: string) => string {
  return (key) => pack.ui[key] ?? key;
}
