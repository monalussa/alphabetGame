/** Minimal surface of HTMLAudioElement the player needs (lets tests use a fake). */
export interface AudioClip {
  volume: number;
  currentTime: number;
  play(): Promise<void>;
  pause(): void;
  addEventListener(type: 'ended' | 'error', listener: () => void): void;
  removeEventListener(type: 'ended' | 'error', listener: () => void): void;
}

export type AudioClipFactory = (url: string) => AudioClip;

export const DEFAULT_VOLUME = 0.9;

export class AudioPlaybackError extends Error {
  constructor(url: string) {
    super(`Could not play ${url}`);
    this.name = 'AudioPlaybackError';
  }
}

function createBrowserClip(url: string): AudioClip {
  const audio = new Audio(url);
  audio.preload = 'auto';
  return audio;
}

/** Plays one clip at a time; starting a clip stops the previous one. */
export class AudioPlayer {
  readonly #createClip: AudioClipFactory;
  readonly #clips = new Map<string, AudioClip>();
  #current: { clip: AudioClip; finish: () => void } | undefined;
  #volume = DEFAULT_VOLUME;

  constructor(createClip: AudioClipFactory = createBrowserClip) {
    this.#createClip = createClip;
  }

  set volume(value: number) {
    this.#volume = Math.min(1, Math.max(0, value));
  }

  get volume(): number {
    return this.#volume;
  }

  preload(urls: readonly string[]): void {
    urls.forEach((url) => this.#getClip(url));
  }

  stop(): void {
    const current = this.#current;
    this.#current = undefined;
    if (!current) return;
    current.clip.pause();
    current.finish();
  }

  /** Resolves when the clip ends or is stopped; rejects if it cannot be played. */
  play(url: string): Promise<void> {
    this.stop();
    const clip = this.#getClip(url);
    clip.volume = this.#volume;
    clip.currentTime = 0;

    return new Promise<void>((resolve, reject) => {
      const cleanUp = (): void => {
        clip.removeEventListener('ended', onEnded);
        clip.removeEventListener('error', onError);
        if (this.#current?.clip === clip) this.#current = undefined;
      };
      const onEnded = (): void => {
        cleanUp();
        resolve();
      };
      const onError = (): void => {
        cleanUp();
        reject(new AudioPlaybackError(url));
      };
      clip.addEventListener('ended', onEnded);
      clip.addEventListener('error', onError);
      this.#current = { clip, finish: onEnded };
      clip.play().catch(onError);
    });
  }

  /** Plays clips one after another; stops at the first that fails. */
  async playSequence(urls: readonly string[]): Promise<void> {
    for (const url of urls) await this.play(url);
  }

  #getClip(url: string): AudioClip {
    let clip = this.#clips.get(url);
    if (!clip) {
      clip = this.#createClip(url);
      this.#clips.set(url, clip);
    }
    return clip;
  }
}
