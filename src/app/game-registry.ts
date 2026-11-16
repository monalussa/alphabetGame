import type { GameModule } from '../core/games/game-module';
import { smashGame } from '../games/smash';

export const GAMES: readonly GameModule[] = [smashGame];
