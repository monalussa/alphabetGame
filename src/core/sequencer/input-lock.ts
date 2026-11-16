export const MAX_SEQUENCE_MS = 4000;

export type Sequence = () => Promise<void>;

/**
 * Lets one sequence (animation + audio) run at a time. Input arriving while a
 * sequence plays is dropped, never queued, so smashing keys cannot pile up sounds.
 * The timeout releases the lock even if audio never fires its 'ended' event.
 */
export class InputLock {
  readonly #maxSequenceMs: number;
  #isBusy = false;

  constructor(maxSequenceMs: number = MAX_SEQUENCE_MS) {
    if (!Number.isFinite(maxSequenceMs) || maxSequenceMs <= 0) {
      throw new RangeError(`maxSequenceMs must be a positive number, got ${maxSequenceMs}`);
    }
    this.#maxSequenceMs = maxSequenceMs;
  }

  get isBusy(): boolean {
    return this.#isBusy;
  }

  /** Runs the sequence if idle. Returns false when the input was dropped. */
  async run(sequence: Sequence): Promise<boolean> {
    if (this.#isBusy) return false;
    this.#isBusy = true;

    let timer: ReturnType<typeof setTimeout> | undefined;
    const timeout = new Promise<void>((resolve) => {
      timer = setTimeout(resolve, this.#maxSequenceMs);
    });

    try {
      await Promise.race([sequence(), timeout]);
      return true;
    } finally {
      clearTimeout(timer);
      this.#isBusy = false;
    }
  }
}
