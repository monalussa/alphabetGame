<script lang="ts">
  import type { AssetUrls } from '../core/content/asset-urls';
  import type { PackEntry, PackLetter } from '../core/content/types';

  interface Props {
    letter: PackLetter;
    entry: PackEntry;
    packCode: string;
    urls: AssetUrls;
  }

  let { letter, entry, packCode, urls }: Props = $props();

  const imageUrl = $derived.by(() => {
    if (!entry.image) return undefined;
    return entry.kind === 'character'
      ? urls.character(packCode, entry.image)
      : urls.image(entry.image);
  });
  const initialLength = $derived(entry.kind === 'word' ? letter.letter.length : 0);
  const initial = $derived(entry.text.slice(0, initialLength));
  const rest = $derived(entry.text.slice(initialLength));
</script>

<figure class="card" data-testid="entry-card" data-kind={entry.kind}>
  {#if imageUrl}
    <img class="picture" src={imageUrl} alt="" draggable="false" />
  {:else if entry.emoji}
    <span class="emoji" aria-hidden="true">{entry.emoji}</span>
  {:else}
    <span class="big-letter" aria-hidden="true">{letter.display}</span>
  {/if}
  <figcaption>
    {#if entry.kind === 'word'}
      <span class="word"><span class="initial">{initial}</span>{rest}</span>
    {:else}
      <span class="character-name">{entry.text}</span>
      {#if entry.caption}<span class="caption">{entry.caption}</span>{/if}
    {/if}
  </figcaption>
</figure>

<style>
  .card {
    margin: 0;
    display: grid;
    justify-items: center;
    gap: 1.5rem;
    animation: pop-in 350ms cubic-bezier(0.34, 1.56, 0.64, 1);
  }

  .picture {
    width: min(55vh, 70vw);
    height: min(55vh, 70vw);
    user-select: none;
  }

  .emoji {
    font-size: min(40vh, 55vw);
    line-height: 1;
  }

  .big-letter {
    font-size: min(38vh, 45vw);
    font-weight: 800;
    line-height: 1;
    color: var(--color-accent);
    text-shadow: 0.04em 0.04em 0 var(--color-text);
  }

  figcaption {
    display: grid;
    justify-items: center;
    gap: 0.5rem;
    text-align: center;
  }

  .word,
  .character-name {
    font-size: clamp(3rem, 10vh, 6rem);
    font-weight: 800;
    letter-spacing: 0.02em;
  }

  .initial {
    color: var(--color-accent);
  }

  .caption {
    font-size: clamp(1.4rem, 4vh, 2.2rem);
  }

  @keyframes pop-in {
    from {
      transform: scale(0.3) rotate(-8deg);
      opacity: 0;
    }
    to {
      transform: scale(1) rotate(0);
      opacity: 1;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .card {
      animation: none;
    }
  }
</style>
