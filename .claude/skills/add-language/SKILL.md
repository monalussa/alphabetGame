---
name: add-language
description: Step-by-step guide to add a new language pack to alphabetGame with data only, no code changes. Load before adding or extending a language.
---

# Adding a language

A language is data only. If you find yourself changing `src/`, stop and report — the architecture needs fixing instead.

1. Copy `content/languages/_template/` to `content/languages/<code>/` (ISO 639-1, e.g. `hr`).
2. `pack.json`: name, `ttsVoice`, full `alphabet` in order (including digraphs such as `dž`, `lj`, `nj`),
   `skipLetters`, `funKeys` (keys on that keyboard layout without an entry), `digraphs` (letter → key sequence).
3. Word list approved by the owner in `content/words-review.txt` → `letters.json` (1 character + 3 words per letter).
   Reuse existing concepts; add a concept (and its picture via image-scout) only when none fits.
4. Character names and lines in that language (HR "Gospođa A" / "Gospodin B"), drawn by letter-artist.
5. `ui.json`: translate every key present in the French `ui.json`.
6. Native-speaker review of words, lines and UI strings.
7. Run the content validator and audio generation, then `npm run verify` and the e2e tests.
