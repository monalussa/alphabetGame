<script lang="ts">
  import { GAMES } from './game-registry';
  import type { GameModule } from '../core/games/game-module';

  let activeGame: GameModule | undefined = $state();

  function startFirstGame(): void {
    activeGame = GAMES[0];
  }
</script>

<main>
  {#if activeGame}
    <activeGame.component />
  {:else}
    <h1>Alphabet Game</h1>
    <button type="button" class="start" aria-label="Jouer" onclick={startFirstGame}>▶</button>
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
  }

  main {
    min-height: 100vh;
    display: grid;
    place-items: center;
    align-content: center;
    gap: 2rem;
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
</style>
