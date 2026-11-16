<script lang="ts">
  import { onMount } from 'svelte';
  import type { PackEntry, PackLetter } from '../../core/content/types';
  import { EntryRotation } from '../../core/game/entry-rotation';
  import { pickRandom } from '../../core/game/random';
  import type { GameProps } from '../../core/games/game-module';
  import { buildKeyMap, classifyKey } from '../../core/input/keyboard';
  import EntryCard from '../../ui/EntryCard.svelte';
  import FunBurst from '../../ui/FunBurst.svelte';

  const MIN_SEQUENCE_MS = 700;
  const FUN_SYMBOLS = ['🎉', '💫', '⭐', '🌈', '🎈', '✨', '🫧', '🎊'];
  const BACKGROUNDS = ['#fff1d6', '#e3f4fd', '#e9f7e1', '#fde7ef', '#efe7fb', '#fff8c9'];
  const BROWSER_KEYS = /^(Escape|F\d{1,2})$/;

  type Shown =
    | { kind: 'entry'; id: number; letter: PackLetter; entry: PackEntry }
    | { kind: 'fun'; id: number; symbol: string };

  let { pack, services }: GameProps = $props();

  const keyMap = $derived(buildKeyMap(pack));
  const lettersById = $derived(new Map(pack.letters.map((letter) => [letter.id, letter])));
  const rotation = new EntryRotation();
  let shown: Shown | undefined = $state();
  let showCount = 0;

  const background = $derived.by(() => {
    if (shown?.kind !== 'entry') return BACKGROUNDS[0];
    const index = pack.letters.indexOf(shown.letter);
    return BACKGROUNDS[index % BACKGROUNDS.length];
  });

  function wait(milliseconds: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, milliseconds));
  }

  async function playClips(urls: string[]): Promise<void> {
    try {
      await services.audio.playSequence(urls);
    } catch (error) {
      console.warn('Audio could not be played', error);
    }
  }

  function clipsFor(letter: PackLetter, entry: PackEntry): string[] {
    const clipIds = entry.kind === 'word' ? [letter.audio, entry.audio] : [entry.audio];
    return clipIds.filter((id) => id !== null).map((id) => services.urls.clip(pack.code, id));
  }

  async function showLetter(letter: PackLetter): Promise<void> {
    const entry = rotation.next(letter);
    if (!entry) return;
    shown = { kind: 'entry', id: ++showCount, letter, entry };
    await Promise.all([playClips(clipsFor(letter, entry)), wait(MIN_SEQUENCE_MS)]);
  }

  async function showFun(): Promise<void> {
    shown = { kind: 'fun', id: ++showCount, symbol: pickRandom(FUN_SYMBOLS) ?? '✨' };
    const sound = pickRandom(pack.funSounds);
    const clips = sound ? [services.urls.funSound(sound)] : [];
    await Promise.all([playClips(clips), wait(MIN_SEQUENCE_MS)]);
  }

  function handleKeydown(event: KeyboardEvent): void {
    const isShortcut = event.ctrlKey || event.metaKey || event.altKey;
    if (!isShortcut && !BROWSER_KEYS.test(event.key)) event.preventDefault();

    const action = classifyKey(event, keyMap, pack.locale);
    if (action.type === 'ignored') return;
    const letter = action.type === 'letter' ? lettersById.get(action.letterId) : undefined;
    void services.lock.run(() => (letter ? showLetter(letter) : showFun()));
  }

  onMount(() => {
    const clipUrls = pack.letters.flatMap((letter) =>
      letter.entries.flatMap((entry) => clipsFor(letter, entry)),
    );
    services.audio.preload([...new Set(clipUrls)]);
  });
</script>

<svelte:window onkeydown={handleKeydown} />

<section class="stage" style:background-color={background} data-testid="smash-game">
  {#if shown?.kind === 'entry'}
    {#key shown.id}
      <EntryCard
        letter={shown.letter}
        entry={shown.entry}
        packCode={pack.code}
        urls={services.urls}
      />
    {/key}
  {:else if shown?.kind === 'fun'}
    {#key shown.id}
      <FunBurst symbol={shown.symbol} />
    {/key}
  {:else}
    <p class="hint" aria-live="polite">{services.t('game.smash.hint')}</p>
  {/if}
</section>

<style>
  .stage {
    position: fixed;
    inset: 0;
    display: grid;
    place-items: center;
    transition: background-color 400ms ease;
    user-select: none;
  }

  .hint {
    font-size: clamp(2rem, 7vh, 4rem);
    font-weight: 800;
    text-align: center;
    animation: breathe 2.4s ease-in-out infinite;
  }

  @keyframes breathe {
    50% {
      transform: scale(1.06);
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .hint {
      animation: none;
    }
  }
</style>
