import type { Component } from 'svelte';
import type { AudioPlayer } from '../audio/audio-player';
import type { AssetUrls } from '../content/asset-urls';
import type { LanguagePack } from '../content/types';
import type { InputLock } from '../sequencer/input-lock';

export interface GameServices {
  readonly urls: AssetUrls;
  readonly audio: AudioPlayer;
  readonly lock: InputLock;
  readonly t: (key: string) => string;
}

export interface GameProps {
  readonly pack: LanguagePack;
  readonly services: GameServices;
}

/** Contract every game implements; games are listed in src/app/game-registry.ts. */
export interface GameModule {
  readonly id: string;
  readonly titleKey: string;
  readonly component: Component<GameProps>;
}
