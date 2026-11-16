import type { LanguagePack } from '../content/types';

export type KeyAction =
  | { readonly type: 'letter'; readonly letterId: string }
  | { readonly type: 'fun' }
  | { readonly type: 'ignored' };

export interface KeyPress {
  readonly key: string;
  readonly repeat: boolean;
  readonly ctrlKey: boolean;
  readonly metaKey: boolean;
  readonly altKey: boolean;
}

const IGNORED: KeyAction = { type: 'ignored' };
const FUN: KeyAction = { type: 'fun' };

/** Maps every key of a playable letter (lowercase) to its letter id. */
export function buildKeyMap(pack: LanguagePack): ReadonlyMap<string, string> {
  const entries = pack.letters
    .filter((letter) => letter.isPlayable)
    .flatMap((letter) => letter.keys.map((key) => [key, letter.id] as const));
  return new Map(entries);
}

function isSingleCharacter(key: string): boolean {
  return [...key].length === 1;
}

/**
 * Decides what a key press does. Shortcuts and named keys (Shift, Tab, F5, Dead…) are
 * ignored; any other printable key that is not a playable letter plays a fun sound.
 */
export function classifyKey(
  press: KeyPress,
  keyMap: ReadonlyMap<string, string>,
  locale: string,
): KeyAction {
  if (press.repeat || press.ctrlKey || press.metaKey || press.altKey) return IGNORED;
  if (!isSingleCharacter(press.key)) return IGNORED;
  const letterId = keyMap.get(press.key.toLocaleLowerCase(locale));
  return letterId ? { type: 'letter', letterId } : FUN;
}
