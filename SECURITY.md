# Security

## Threat model

alphabetGame is a static site for children: no backend, no accounts, no cookies, no analytics,
no requests to other origins. The realistic risks are:

| Risk                                    | Mitigation                                                                                                                   |
| --------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Malicious or compromised npm package    | Few dependencies, exact versions, committed lockfile, `npm ci --ignore-scripts` in CI, audits in CI, Dependabot              |
| XSS through content (word lists, names) | Content rendered as text only; `{@html}`, `innerHTML` and friends are lint errors; content validated by JSON Schema at build |
| Leaked TTS API key                      | Key lives only in `.env` (gitignored) and is used only by build tools; gitleaks in pre-commit hook and CI                    |
| Embedding / clickjacking, tracking      | Strict CSP (`'self'` only, no `unsafe-*`), `frame-ancestors 'none'`, `Referrer-Policy: no-referrer`                          |
| Unlicensed images                       | License manifest + license-reviewer agent + build-time validator                                                             |

Security headers are defined once in `config/security-headers.ts`. The build injects the CSP
as a `<meta>` tag and emits `dist/_headers` for hosts that support it (Netlify, Cloudflare Pages).
GitHub Pages cannot set headers, so only the meta CSP applies there (no `frame-ancestors`).

## Dependency audit policy

- Runtime dependencies (shipped to the browser): **any** advisory fails CI.
- Dev/build tooling: **high or critical** fails CI. Moderate/low advisories in tooling that never
  processes untrusted input are recorded below and re-checked when Dependabot proposes updates.

### Accepted advisories (dev tooling only)

| Date       | Package                                          | Advisory                                | Why accepted                                                               |
| ---------- | ------------------------------------------------ | --------------------------------------- | -------------------------------------------------------------------------- |
| 2026-11-16 | `deepmerge` (via `@sveltejs/vite-plugin-svelte`) | GHSA-gcqx-w48m-w2h4 prototype poisoning | Only merges our own build config; no fix released                          |
| 2026-11-16 | `minimatch` (via `typescript-eslint`)            | GHSA-g3hv-75wg-m249 ReDoS               | Only matches our own lint glob patterns; fix requires a breaking downgrade |

## Reporting

Please report vulnerabilities privately via GitHub Security Advisories on this repository.
