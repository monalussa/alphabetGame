import type { PackEntry, PackLetter } from '../content/types';

/** Each press of the same letter shows its next entry: character → word 1 → word 2 → … → again. */
export class EntryRotation {
  readonly #positions = new Map<string, number>();

  next(letter: PackLetter): PackEntry | undefined {
    if (letter.entries.length === 0) return undefined;
    const position = this.#positions.get(letter.id) ?? 0;
    this.#positions.set(letter.id, (position + 1) % letter.entries.length);
    return letter.entries[position];
  }

  reset(): void {
    this.#positions.clear();
  }
}
