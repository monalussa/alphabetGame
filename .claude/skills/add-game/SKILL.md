---
name: add-game
description: How to add a new game module (e.g. "first letter", drag and drop) to alphabetGame without touching other games or content. Load before creating anything in src/games/.
---

# Adding a game

1. Create `src/games/<id>/` with `index.ts` exporting a `GameModule`
   (`src/core/games/game-module.ts`): `{ id, titleKey, component }`.
2. Register it with one line in `src/app/game-registry.ts`.
3. Add the title string `game.<id>.title` to every language's `ui.json`.
4. Use only `src/core` services (content API, AudioPlayer, InputLock, i18n) and `src/ui` components.
   Never import from another game; if two games need the same thing, move it to `ui/` or `core/`.
5. Never hardcode words, letters or language logic in a game — read everything from the loaded pack,
   so the game works for every language automatically.
6. All input that starts a sound goes through `InputLock.run(...)`.
7. Add unit tests for game logic and one e2e test for the main flow.

ESLint (`boundaries/dependencies`) fails the build if layering is broken.
