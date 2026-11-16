<script lang="ts">
  interface Props {
    symbol: string;
  }

  let { symbol }: Props = $props();
</script>

<span class="burst" data-testid="fun-burst" aria-hidden="true">{symbol}</span>

<style>
  .burst {
    font-size: min(45vh, 60vw);
    line-height: 1;
    animation: wobble 700ms ease-out;
  }

  @keyframes wobble {
    0% {
      transform: scale(0.2) rotate(0);
    }
    40% {
      transform: scale(1.15) rotate(15deg);
    }
    70% {
      transform: scale(0.95) rotate(-10deg);
    }
    100% {
      transform: scale(1) rotate(0);
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .burst {
      animation: none;
    }
  }
</style>
