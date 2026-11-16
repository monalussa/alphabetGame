import { describe, expect, it } from 'vitest';
import type { LanguagePack, PackEntry, PackLetter } from '../../src/core/content/types';
import { EntryRotation } from '../../src/core/game/entry-rotation';
import { pickRandom } from '../../src/core/game/random';
import { createTranslator } from '../../src/core/i18n/translate';
import { buildKeyMap, classifyKey, type KeyPress } from '../../src/core/input/keyboard';

function entry(id: string): PackEntry {
  return { kind: 'word', id, text: id, caption: null, image: null, emoji: '🍎', audio: null };
}

function letter(id: string, entries: PackEntry[], keys = [id]): PackLetter {
  return {
    id,
    letter: id,
    display: id,
    keys,
    isPlayable: entries.length > 0,
    audio: null,
    entries,
  };
}

const PACK: LanguagePack = {
  schemaVersion: 1,
  code: 'fr',
  name: 'Français',
  locale: 'fr-FR',
  ui: { 'start.play': 'Jouer' },
  funSounds: [],
  letters: [
    letter('a', [entry('ananas'), entry('avion')]),
    letter('w', []),
    letter('ch', [entry('cokolada')], ['č']),
  ],
};

function press(key: string, extra: Partial<KeyPress> = {}): KeyPress {
  return { key, repeat: false, ctrlKey: false, metaKey: false, altKey: false, ...extra };
}

describe('classifyKey', () => {
  const keyMap = buildKeyMap(PACK);

  it.each([
    ['a', 'a'],
    ['A', 'a'],
    ['č', 'ch'],
    ['Č', 'ch'],
  ])('maps key %s to letter %s', (key, letterId) => {
    expect(classifyKey(press(key), keyMap, 'fr-FR')).toEqual({ type: 'letter', letterId });
  });

  it.each(['w', 'é', '1', ' ', '?'])('turns non-playable key %j into a fun sound', (key) => {
    expect(classifyKey(press(key), keyMap, 'fr-FR')).toEqual({ type: 'fun' });
  });

  it.each(['Shift', 'Enter', 'Tab', 'Dead', 'F5', 'ArrowLeft'])('ignores named key %s', (key) => {
    expect(classifyKey(press(key), keyMap, 'fr-FR')).toEqual({ type: 'ignored' });
  });

  it.each([{ repeat: true }, { ctrlKey: true }, { metaKey: true }, { altKey: true }])(
    'ignores held keys and shortcuts %o',
    (extra) => {
      expect(classifyKey(press('a', extra), keyMap, 'fr-FR')).toEqual({ type: 'ignored' });
    },
  );
});

describe('EntryRotation', () => {
  it('cycles through entries and starts over', () => {
    const rotation = new EntryRotation();
    const a = PACK.letters[0] as PackLetter;

    const shown = [1, 2, 3].map(() => rotation.next(a)?.id);

    expect(shown).toEqual(['ananas', 'avion', 'ananas']);
  });

  it('keeps a separate position per letter', () => {
    const rotation = new EntryRotation();
    const [a, , ch] = PACK.letters as PackLetter[];
    rotation.next(a as PackLetter);

    expect(rotation.next(ch as PackLetter)?.id).toBe('cokolada');
    expect(rotation.next(a as PackLetter)?.id).toBe('avion');
  });

  it('returns nothing for a letter without entries', () => {
    expect(new EntryRotation().next(PACK.letters[1] as PackLetter)).toBeUndefined();
  });
});

describe('pickRandom', () => {
  it('returns undefined for an empty list', () => {
    expect(pickRandom([])).toBeUndefined();
  });

  it.each([
    [0, 'x'],
    [0.99, 'z'],
    [1, 'x'],
  ])('maps random %s to %s', (value, expected) => {
    expect(pickRandom(['x', 'y', 'z'], () => value)).toBe(expected);
  });
});

describe('createTranslator', () => {
  it('returns the string or the key when missing', () => {
    const t = createTranslator(PACK);

    expect([t('start.play'), t('missing.key')]).toEqual(['Jouer', 'missing.key']);
  });
});
