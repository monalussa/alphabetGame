# alphabetGame

Static browser app for kids learning letters (FR first, then HR, EN). A key press shows a
letter character or a word picture and plays its sound. No backend. Non-profit, public.

## Stack

- Svelte 5 + TypeScript (strict) + Vite. Node version in `.nvmrc` (use `nvm use`).
- Python 3.12 + uv for build-time tools in `tools/` (content validation, TTS audio) — Phase 2.
- Tests: Vitest (`tests/unit`), Playwright against the production build (`tests/e2e`).

## Architecture (enforced by eslint-plugin-boundaries)

```
src/app/     composition root: main.ts, App.svelte, game-registry.ts  → may import everything
src/games/*  one folder per game                                       → ui, core (never another game)
src/ui/      shared Svelte components                                  → ui, core
src/core/    plain TS services: content, audio, input, sequencer, i18n → core only
content/     data only: concepts, language packs, images, manifests, schemas
config/      build-time config (security headers)
```

- Adding a language = adding data under `content/languages/<code>/`, never code. See skill `add-language`.
- Adding a game = a new `src/games/<id>/` folder + one line in `src/app/game-registry.ts`. See skill `add-game`.
- Pictures belong to language-neutral _concepts_ and are shared by all languages.

## Hard rules

- Never render HTML strings: no `{@html}`, `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`.
- No external URLs at runtime. Everything self-hosted (fonts, images, audio). No CDNs, analytics, ads, cookies.
- Never weaken `config/security-headers.ts` (no `unsafe-inline`, `unsafe-eval`, `data:`, wildcards).
- No new dependency without a written reason in the PR; prefer zero runtime dependencies. Exact versions only.
- Never read, print or commit `.env`. Secrets only via environment variables in build tools.
- Images: approved licenses only, with a manifest record (skill `image-licensing`).
  Letter characters are our own originals — never imitate _Les Alphas_ or any existing characters.
- Child-appropriate content only: concrete, friendly, picturable words.

## Code style

- Named constants, no magic numbers. Guard clauses, small functions, max 3 nesting levels.
- Booleans: `is/has/should/can` prefixes. No comments unless the WHY is non-obvious.
- Tests: Arrange-Act-Assert, one behavior per test, descriptive names, fake timers (no sleeps).

## Commands

- `npm run dev` · `npm run verify` (format, lint, typecheck, unit tests, build) · `npm run test:e2e`
- Definition of done: `npm run verify` and `npm run test:e2e` pass, security-reviewer has no blocking findings.

## Git workflow

- `main` is protected; only the human owner merges. Never push to `main`, never force-push.
- One branch + worktree per writing agent: `feat/<x>`, `content/<lang>`, `images/<batch>`, `art/<lang>-characters`.
- Reviewer agents (security-reviewer, license-reviewer) are read-only and report; they never commit.
