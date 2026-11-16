import { describe, expect, it, vi } from 'vitest';
import { AudioPlaybackError, AudioPlayer, type AudioClip } from '../../src/core/audio/audio-player';

class FakeClip implements AudioClip {
  volume = 1;
  currentTime = 5;
  readonly url: string;
  readonly pause = vi.fn();
  playResult: Promise<void> = Promise.resolve();
  readonly #listeners = new Map<string, Set<() => void>>();

  constructor(url: string) {
    this.url = url;
  }

  play(): Promise<void> {
    return this.playResult;
  }

  addEventListener(type: string, listener: () => void): void {
    const listeners = this.#listeners.get(type) ?? new Set();
    listeners.add(listener);
    this.#listeners.set(type, listeners);
  }

  removeEventListener(type: string, listener: () => void): void {
    this.#listeners.get(type)?.delete(listener);
  }

  emit(type: 'ended' | 'error'): void {
    [...(this.#listeners.get(type) ?? [])].forEach((listener) => listener());
  }
}

function createPlayer(): { player: AudioPlayer; clips: Map<string, FakeClip> } {
  const clips = new Map<string, FakeClip>();
  const player = new AudioPlayer((url) => {
    const clip = new FakeClip(url);
    clips.set(url, clip);
    return clip;
  });
  return { player, clips };
}

describe('AudioPlayer', () => {
  it('resolves when the clip ends and restarts it from the beginning', async () => {
    const { player, clips } = createPlayer();

    const playing = player.play('/a.mp3');
    clips.get('/a.mp3')?.emit('ended');

    await expect(playing).resolves.toBeUndefined();
    expect(clips.get('/a.mp3')?.currentTime).toBe(0);
  });

  it('stops the previous clip when a new one starts', async () => {
    const { player, clips } = createPlayer();
    const first = player.play('/a.mp3');

    const second = player.play('/b.mp3');

    await expect(first).resolves.toBeUndefined();
    expect(clips.get('/a.mp3')?.pause).toHaveBeenCalled();
    clips.get('/b.mp3')?.emit('ended');
    await second;
  });

  it('rejects when the clip fails to load', async () => {
    const { player, clips } = createPlayer();

    const playing = player.play('/missing.mp3');
    clips.get('/missing.mp3')?.emit('error');

    await expect(playing).rejects.toBeInstanceOf(AudioPlaybackError);
  });

  it('rejects when the browser refuses to play', async () => {
    const player = new AudioPlayer((url) => {
      const clip = new FakeClip(url);
      clip.playResult = Promise.reject(new Error('NotAllowedError'));
      return clip;
    });

    await expect(player.play('/a.mp3')).rejects.toBeInstanceOf(AudioPlaybackError);
  });

  it('reuses one clip per url', () => {
    const factory = vi.fn((url: string) => new FakeClip(url));
    const player = new AudioPlayer(factory);

    player.preload(['/a.mp3', '/a.mp3']);
    void player.play('/a.mp3');

    expect(factory).toHaveBeenCalledOnce();
  });

  it('plays a sequence in order', async () => {
    const { player, clips } = createPlayer();

    const sequence = player.playSequence(['/a.mp3', '/b.mp3']);
    await vi.waitFor(() => expect(clips.has('/a.mp3')).toBe(true));
    clips.get('/a.mp3')?.emit('ended');
    await vi.waitFor(() => expect(clips.has('/b.mp3')).toBe(true));
    clips.get('/b.mp3')?.emit('ended');

    await expect(sequence).resolves.toBeUndefined();
  });

  it.each([
    [1.5, 1],
    [-0.2, 0],
    [0.4, 0.4],
  ])('clamps volume %s to %s', (input, expected) => {
    const { player } = createPlayer();

    player.volume = input;

    expect(player.volume).toBe(expected);
  });
});
