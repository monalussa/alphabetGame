<script lang="ts" module>
  export const HOLD_DURATION_MS = 3000;
</script>

<script lang="ts">
  import { onDestroy } from 'svelte';

  interface Props {
    label: string;
    onUnlock: () => void;
  }

  let { label, onUnlock }: Props = $props();
  let timer: ReturnType<typeof setTimeout> | undefined;
  let isHolding = $state(false);

  function startHold(event: PointerEvent): void {
    event.preventDefault();
    cancelHold();
    isHolding = true;
    timer = setTimeout(() => {
      isHolding = false;
      onUnlock();
    }, HOLD_DURATION_MS);
  }

  function cancelHold(): void {
    clearTimeout(timer);
    timer = undefined;
    isHolding = false;
  }

  onDestroy(cancelHold);
</script>

<button
  type="button"
  class="gate"
  class:is-holding={isHolding}
  aria-label={label}
  title={label}
  tabindex="-1"
  style:--hold-duration="{HOLD_DURATION_MS}ms"
  onpointerdown={startHold}
  onpointerup={cancelHold}
  onpointerleave={cancelHold}
  onpointercancel={cancelHold}
>
  <span aria-hidden="true">⚙</span>
</button>

<style>
  .gate {
    position: fixed;
    top: 1rem;
    right: 1rem;
    width: 3.5rem;
    height: 3.5rem;
    border-radius: 50%;
    border: 3px solid var(--color-text);
    background: white;
    font-size: 1.8rem;
    cursor: pointer;
    opacity: 0.55;
    touch-action: none;
  }

  .gate.is-holding {
    opacity: 1;
    animation: fill var(--hold-duration) linear forwards;
  }

  @keyframes fill {
    from {
      box-shadow: inset 0 0 0 0 var(--color-accent);
    }
    to {
      box-shadow: inset 0 0 0 1.75rem var(--color-accent);
    }
  }
</style>
