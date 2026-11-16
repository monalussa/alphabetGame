---
name: secure-static-frontend
description: Security rules and review checklist for alphabetGame's static Svelte frontend. Load before writing or reviewing any code in src/, config/, index.html, vite.config.ts or CI.
---

# Secure static frontend

alphabetGame has no backend, so attacks come through **dependencies**, **content rendered unsafely**,
**leaked secrets** and **weakened headers**. Every change must keep all of these closed.

## Rules

1. **Render text, never HTML.** Use `{text}` in Svelte. Forbidden: `{@html}`, `innerHTML`, `outerHTML`,
   `insertAdjacentHTML`, `document.write`, `eval`, `new Function`, string `setTimeout`. ESLint enforces these;
   never disable the rule.
2. **Same origin only.** No `http(s)://` URLs in `src/`. Fonts, images and audio live in the repo.
   `fetch` only relative paths under `/packs/` or `/audio/`.
3. **CSP is fixed.** `config/security-headers.ts` is the single source. Never add `unsafe-inline`,
   `unsafe-eval`, `data:`, `blob:`, wildcards or other hosts. Do not set inline `style="…"` from strings via
   `setAttribute`; use Svelte `style:` directives or classes. `build.assetsInlineLimit` stays `0`.
4. **Content is data, not code.** Loaded JSON is validated (schema at build, type guards at runtime).
   Unknown fields are ignored, missing fields fail safely (show nothing, log a warning).
5. **Paths from content are ids, not URLs.** Build file paths from validated ASCII ids
   (`^[a-z0-9_]+$`) — never concatenate raw content strings into URLs.
6. **Storage.** `localStorage` only for language and volume, wrapped in try/catch, values validated on read.
7. **No tracking.** No analytics, ads, cookies, third-party embeds or fingerprinting APIs.
8. **Dependencies.** Prefer zero runtime dependencies. Any new package needs: a reason, an exact version,
   a check of its maintainers and weekly downloads, and a clean `npm audit`.
9. **Secrets.** Never in code, logs or the bundle. Nothing from `.env` may be imported by `src/`
   (Vite exposes only `VITE_*` vars — never create one holding a secret).
10. **CI.** Workflow `permissions: contents: read`, actions pinned to full commit SHAs, `persist-credentials: false`.

## Review checklist (security-reviewer ticks every line)

- [ ] No new HTML sinks or eslint-disable comments for security rules
- [ ] No external URLs, CDNs, remote fonts or third-party scripts
- [ ] `config/security-headers.ts` unchanged or only stricter; unit test still passes
- [ ] Content parsing validates input; ids checked before building paths
- [ ] No secrets in diff (`gitleaks git --redact`), no `.env` files staged
- [ ] New dependencies justified, exact-pinned, `npm audit --omit=dev` clean
- [ ] Workflow changes keep least privilege and SHA pinning
- [ ] e2e smoke test still asserts no console errors (CSP violations) and no external requests
