/** Runtime language pack, produced by `alphabet-content build` (tools/src/alphabet_tools/pack_builder.py). */

export const PACK_SCHEMA_VERSION = 1;

export type EntryKind = 'character' | 'word';

export interface PackEntry {
  readonly kind: EntryKind;
  readonly id: string;
  readonly text: string;
  readonly caption: string | null;
  readonly image: string | null;
  readonly emoji: string | null;
  readonly audio: string | null;
}

export interface PackLetter {
  readonly id: string;
  readonly letter: string;
  readonly display: string;
  readonly keys: readonly string[];
  readonly isPlayable: boolean;
  readonly audio: string | null;
  readonly entries: readonly PackEntry[];
}

export interface LanguagePack {
  readonly schemaVersion: typeof PACK_SCHEMA_VERSION;
  readonly code: string;
  readonly name: string;
  readonly locale: string;
  readonly ui: Readonly<Record<string, string>>;
  readonly funSounds: readonly string[];
  readonly letters: readonly PackLetter[];
}

export interface LanguageSummary {
  readonly code: string;
  readonly name: string;
}

export interface PackIndex {
  readonly schemaVersion: typeof PACK_SCHEMA_VERSION;
  readonly languages: readonly LanguageSummary[];
}
