# alphabetGame

Browser app for kids learning letters (French, Croatian, English): press a key, meet the letter's
character, see a picture and hear the word. Static site, no tracking, works offline (planned).

## Play it (this computer only)
```sh
./scripts/play.sh            # opens http://127.0.0.1:8080 in your browser; Ctrl+C to stop
./scripts/play.sh --rebuild  # rebuild first after changes
```
Click ▶, then press letters. To leave the game, hold the ⚙ button for 3 seconds.

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
Status: French playable — keyboard game with OpenMoji pictures and Piper voice. HR and EN come next, step by step.
