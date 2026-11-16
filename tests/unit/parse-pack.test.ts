import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import {
  PackFormatError,
  parseLanguagePack,
  parsePackIndex,
} from '../../src/core/content/parse-pack';

const BUILT_PACKS_DIR = join(import.meta.dirname, '../../public/packs');

function validPack(): Record<string, unknown> {
  return {
    schemaVersion: 1,
    code: 'fr',
    name: 'Français',
    locale: 'fr-FR',
    ui: { 'start.play': 'Jouer' },
    funSounds: ['fun_boing'],
    letters: [
      {
        id: 'a',
        letter: 'a',
        display: 'A a',
        keys: ['a'],
        isPlayable: true,
        audio: 'letter_a',
        entries: [
          {
            kind: 'word',
            id: 'ananas',
            text: 'ananas',
            caption: null,
            image: null,
            emoji: '🍍',
            audio: 'word_ananas',
          },
        ],
      },
    ],
  };
}

function withFirstEntry(changes: Record<string, unknown>): Record<string, unknown> {
  const pack = validPack();
  const [letter] = pack['letters'] as Record<string, unknown>[];
  const [entry] = letter?.['entries'] as Record<string, unknown>[];
  Object.assign(entry ?? {}, changes);
  return pack;
}

describe('parseLanguagePack', () => {
  it('accepts a valid pack', () => {
    const pack = parseLanguagePack(validPack());

    expect(pack.letters[0]?.entries[0]?.emoji).toBe('🍍');
  });

  it.each(['../../secret', 'word/ananas', 'https://evil.example/x', 'WORD'])(
    'rejects unsafe audio id %s',
    (audio) => {
      expect(() => parseLanguagePack(withFirstEntry({ audio }))).toThrow(PackFormatError);
    },
  );

  it('rejects an unknown entry kind', () => {
    expect(() => parseLanguagePack(withFirstEntry({ kind: 'script' }))).toThrow(
      /unknown entry kind/,
    );
  });

  it('rejects an unsupported schema version', () => {
    expect(() => parseLanguagePack({ ...validPack(), schemaVersion: 2 })).toThrow(
      /unsupported schema version/,
    );
  });

  it.each([null, [], 'pack', 42])('rejects a non-object pack %s', (value) => {
    expect(() => parseLanguagePack(value)).toThrow(PackFormatError);
  });

  it('reports where the problem is', () => {
    expect(() => parseLanguagePack(withFirstEntry({ text: '' }))).toThrow(
      'pack.letters[0].entries[0].text',
    );
  });
});

describe('built content packs', () => {
  it('index and every language pack match the runtime format', () => {
    const index = parsePackIndex(
      JSON.parse(readFileSync(join(BUILT_PACKS_DIR, 'index.json'), 'utf-8')),
    );

    const packs = index.languages.map(({ code }) =>
      parseLanguagePack(JSON.parse(readFileSync(join(BUILT_PACKS_DIR, `${code}.json`), 'utf-8'))),
    );

    expect(index.languages.map(({ code }) => code).sort()).toEqual(
      readdirSync(BUILT_PACKS_DIR)
        .filter((name) => name.endsWith('.json') && name !== 'index.json')
        .map((name) => name.replace('.json', ''))
        .sort(),
    );
    expect(packs.every((pack) => pack.letters.some((letter) => letter.isPlayable))).toBe(true);
  });
});
