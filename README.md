# alphabetGame

Browser app for kids learning letters (French, Croatian, English): press a key, meet the letter's
character, see a picture and hear the word. Static site, no tracking, works offline (planned).

## Setup

```sh
nvm use            # Node version from .nvmrc
npm ci             # also installs the git pre-commit hook (needs gitleaks)
npm run dev
```

## Checks

```sh
npm run verify     # format, lint, typecheck, unit tests, build
npm run test:e2e   # Playwright against the production build
```

See `CLAUDE.md` for architecture and rules, `SECURITY.md` for the threat model.
Status: Phase 2 (content pipeline). FR + EN audio generated with Piper; HR waiting for recordings.
