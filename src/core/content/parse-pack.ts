import {
  PACK_SCHEMA_VERSION,
  type EntryKind,
  type LanguagePack,
  type LanguageSummary,
  type PackEntry,
  type PackIndex,
  type PackLetter,
} from './types';

const SAFE_ID = /^[a-z0-9_]{1,40}$/;
const LANGUAGE_CODE = /^[a-z]{2}$/;
const MAX_TEXT_LENGTH = 200;
const ENTRY_KINDS: readonly EntryKind[] = ['character', 'word'];

export class PackFormatError extends Error {
  constructor(path: string, problem: string) {
    super(`Invalid language pack at ${path}: ${problem}`);
    this.name = 'PackFormatError';
  }
}

type Fields = Record<string, unknown>;

function asObject(value: unknown, path: string): Fields {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    throw new PackFormatError(path, 'expected an object');
  }
  return value as Fields;
}

function asArray(value: unknown, path: string): unknown[] {
  if (!Array.isArray(value)) throw new PackFormatError(path, 'expected an array');
  return value;
}

function asText(value: unknown, path: string): string {
  if (typeof value !== 'string' || value.length === 0 || value.length > MAX_TEXT_LENGTH) {
    throw new PackFormatError(path, 'expected a non-empty string');
  }
  return value;
}

function asOptionalText(value: unknown, path: string): string | null {
  return value === null ? null : asText(value, path);
}

function asMatching(value: unknown, pattern: RegExp, path: string): string {
  const text = asText(value, path);
  if (!pattern.test(text)) throw new PackFormatError(path, `'${text}' is not a valid id`);
  return text;
}

function asOptionalId(value: unknown, path: string): string | null {
  return value === null ? null : asMatching(value, SAFE_ID, path);
}

function asBoolean(value: unknown, path: string): boolean {
  if (typeof value !== 'boolean') throw new PackFormatError(path, 'expected a boolean');
  return value;
}

function checkSchemaVersion(value: unknown, path: string): typeof PACK_SCHEMA_VERSION {
  if (value !== PACK_SCHEMA_VERSION) {
    throw new PackFormatError(path, `unsupported schema version ${String(value)}`);
  }
  return PACK_SCHEMA_VERSION;
}

function parseEntry(value: unknown, path: string): PackEntry {
  const fields = asObject(value, path);
  const kind = fields['kind'];
  if (!ENTRY_KINDS.includes(kind as EntryKind)) {
    throw new PackFormatError(`${path}.kind`, `unknown entry kind ${String(kind)}`);
  }
  return {
    kind: kind as EntryKind,
    id: asMatching(fields['id'], SAFE_ID, `${path}.id`),
    text: asText(fields['text'], `${path}.text`),
    caption: asOptionalText(fields['caption'], `${path}.caption`),
    image: asOptionalId(fields['image'], `${path}.image`),
    emoji: asOptionalText(fields['emoji'], `${path}.emoji`),
    audio: asOptionalId(fields['audio'], `${path}.audio`),
  };
}

function parseLetter(value: unknown, path: string): PackLetter {
  const fields = asObject(value, path);
  return {
    id: asMatching(fields['id'], SAFE_ID, `${path}.id`),
    letter: asText(fields['letter'], `${path}.letter`),
    display: asText(fields['display'], `${path}.display`),
    keys: asArray(fields['keys'], `${path}.keys`).map((key, i) => asText(key, `${path}.keys[${i}]`)),
    isPlayable: asBoolean(fields['isPlayable'], `${path}.isPlayable`),
    audio: asOptionalId(fields['audio'], `${path}.audio`),
    entries: asArray(fields['entries'], `${path}.entries`).map((entry, i) =>
      parseEntry(entry, `${path}.entries[${i}]`),
    ),
  };
}

function parseUi(value: unknown, path: string): Record<string, string> {
  const fields = asObject(value, path);
  return Object.fromEntries(
    Object.entries(fields).map(([key, text]) => [key, asText(text, `${path}.${key}`)]),
  );
}

export function parseLanguagePack(value: unknown): LanguagePack {
  const fields = asObject(value, 'pack');
  return {
    schemaVersion: checkSchemaVersion(fields['schemaVersion'], 'pack.schemaVersion'),
    code: asMatching(fields['code'], LANGUAGE_CODE, 'pack.code'),
    name: asText(fields['name'], 'pack.name'),
    locale: asText(fields['locale'], 'pack.locale'),
    ui: parseUi(fields['ui'], 'pack.ui'),
    funSounds: asArray(fields['funSounds'], 'pack.funSounds').map((id, i) =>
      asMatching(id, SAFE_ID, `pack.funSounds[${i}]`),
    ),
    letters: asArray(fields['letters'], 'pack.letters').map((letter, i) =>
      parseLetter(letter, `pack.letters[${i}]`),
    ),
  };
}

function parseLanguageSummary(value: unknown, path: string): LanguageSummary {
  const fields = asObject(value, path);
  return {
    code: asMatching(fields['code'], LANGUAGE_CODE, `${path}.code`),
    name: asText(fields['name'], `${path}.name`),
  };
}

export function parsePackIndex(value: unknown): PackIndex {
  const fields = asObject(value, 'index');
  return {
    schemaVersion: checkSchemaVersion(fields['schemaVersion'], 'index.schemaVersion'),
    languages: asArray(fields['languages'], 'index.languages').map((language, i) =>
      parseLanguageSummary(language, `index.languages[${i}]`),
    ),
  };
}

export function isSafeId(value: string): boolean {
  return SAFE_ID.test(value);
}

export function isLanguageCode(value: string): boolean {
  return LANGUAGE_CODE.test(value);
}
