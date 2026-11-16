import type { GameModule } from '../../core/games/game-module';
import SmashGame from './SmashGame.svelte';

export const smashGame: GameModule = {
  id: 'smash',
  titleKey: 'game.smash.title',
  component: SmashGame,
};
