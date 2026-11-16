import type { Component } from 'svelte';

/** Contract every game implements; games are listed in src/app/game-registry.ts. */
export interface GameModule {
  readonly id: string;
  readonly titleKey: string;
  readonly component: Component;
}
