<script lang="ts">
  import { onMount } from 'svelte';
  import { AudioPlayer } from '../core/audio/audio-player';
  import { createAssetUrls } from '../core/content/asset-urls';
  import { loadLanguagePack, loadPackIndex } from '../core/content/load-pack';
  import type { LanguagePack } from '../core/content/types';
  import { enterKioskMode, exitKioskMode } from '../core/device/kiosk';
  import type { GameServices } from '../core/games/game-module';
  import { createTranslator } from '../core/i18n/translate';
  import { InputLock } from '../core/sequencer/input-lock';
  import ParentGate from '../ui/ParentGate.svelte';
  import { GAMES } from './game-registry';

  const LOAD_ERROR_MESSAGE = 'Oups ! Recharge la page.';
  const urls = createAssetUrls(import.meta.env.BASE_URL);
  const audio = new AudioPlayer();

  type Phase = 'loading' | 'start' | 'playing' | 'error';

  let phase: Phase = $state('loading');
  let pack: LanguagePack | undefined = $state();
  const game = GAMES[0];

  const services: GameServices | undefined = $derived(
    pack ? { urls, audio, lock: new InputLock(), t: createTranslator(pack) } : undefined,
  );

  async function loadDefaultLanguage(): Promise<void> {
    try {
      const index = await loadPackIndex(urls);
      const [firstLanguage] = index.languages;
      if (!firstLanguage) throw new Error('No published language');
      pack = await loadLanguagePack(firstLanguage.code, urls);
      document.documentElement.lang = pack.code;
      document.title = pack.ui['app.title'] ?? document.title;
      phase = 'start';
    } catch (error) {
      console.error('Language pack could not be loaded', error);
      phase = 'error';
    }
  }

  async function startGame(): Promise<void> {
    phase = 'playing';
    await enterKioskMode();
  }

  async function leaveGame(): Promise<void> {
    audio.stop();
    phase = 'start';
    await exitKioskMode();
  }

  function preventContextMenu(event: MouseEvent): void {
    if (phase === 'playing') event.preventDefault();
  }

  onMount(loadDefaultLanguage);
</script>

<svelte:window oncontextmenu={preventContextMenu} />

<main>
  {#if phase === 'playing' && pack && services && game}
    <game.component {pack} {services} />
    <ParentGate label={services.t('parent.hold')} onUnlock={leaveGame} />
  {:else if phase === 'start' && services}
    <h1>{services.t('app.title')}</h1>
    <button type="button" class="start" aria-label={services.t('start.play')} onclick={startGame}>
      ▶
    </button>
  {:else if phase === 'error'}
    <p class="error" role="alert">{LOAD_ERROR_MESSAGE}</p>
  {/if}
</main>

<style>
  :global(:root) {
    --color-background: #fff8e7;
    --color-text: #2b2b2b;
    --color-accent: #ff7a59;
    color-scheme: light;
  }

  :global(body) {
    margin: 0;
    min-height: 100vh;
    background: var(--color-background);
    color: var(--color-text);
    font-family: system-ui, sans-serif;
    overflow: hidden;
  }

  main {
    min-height: 100vh;
    display: grid;
    place-items: center;
    align-content: center;
    gap: 2rem;
  }

  h1 {
    font-size: clamp(2.5rem, 8vw, 5rem);
    margin: 0;
  }

  .start {
    width: 10rem;
    height: 10rem;
    border: none;
    border-radius: 50%;
    background: var(--color-accent);
    color: white;
    font-size: 4rem;
    cursor: pointer;
  }

  .start:focus-visible {
    outline: 4px solid var(--color-text);
    outline-offset: 4px;
  }

  .error {
    font-size: 2rem;
  }
</style>
