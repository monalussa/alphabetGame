---
name: image-licensing
description: Which image licenses alphabetGame accepts, how to record provenance in the manifest, and the review checklist. Load before finding, adding or reviewing any picture or sound.
---

# Image and sound licensing

alphabetGame is published publicly (non-profit). Every asset needs a license that allows that.

## Approved

- CC0 / public domain
- CC BY 4.0 — attribution on the credits page
- CC BY-SA 4.0 — attribution, and our modified versions stay CC BY-SA
- OFL (fonts), MIT / Apache-2.0 (icon sets)
- Our own originals (letter characters)

## Not allowed

- Any NC or ND variant, "free for personal use", "editorial use only"
- Sites with custom terms that forbid redistribution (many "free stock" sites)
- Google Images / Pinterest results, anything without a clear original source page
- Anything resembling copyrighted characters (_Les Alphas_, cartoon or brand characters)

## Preferred sources

OpenMoji (CC BY-SA 4.0) as the default style · Twemoji graphics (CC BY 4.0) · Openclipart (CC0) ·
Kenney (CC0) · Wikimedia Commons (check each file's own license) · freesound.org filtered to CC0 (sounds).

## Manifest record (`content/images/manifest.json`, one per file)

```json
{
  "imageId": "pineapple",
  "file": "pineapple.svg",
  "sourceUrl": "https://openmoji.org/library/emoji-1F34D/",
  "author": "OpenMoji",
  "license": "CC-BY-SA-4.0",
  "licenseUrl": "https://creativecommons.org/licenses/by-sa/4.0/",
  "modified": false,
  "reviewedBy": null,
  "reviewedAt": null
}
```

`license` uses SPDX ids. `reviewedBy`/`reviewedAt` are filled only after license-reviewer approval.
The build fails for any file without an approved, reviewed record.

## Workflow (commands run from `tools/`)

1. Map concepts to OpenMoji hexcodes in `content/images/sources/openmoji.json` (pinned release commit).
2. `uv run alphabet-content images fetch` — downloads into `content/images/_incoming/` (gitignored);
   every file must pass the SVG safety check or it is rejected.
3. Own drawings: write the SVG into `_incoming/` and add a pending record with `"sourceUrl": "own-work"`.
4. `uv run alphabet-content images preview` — contact sheet `_incoming/preview.html`. **Show it to the owner
   before approving** (the owner wants to see samples before anything is added in bulk).
5. `uv run alphabet-content images approve <ids…> | --all --reviewer "<who>"` — moves files, writes the
   manifest record and links the concept. `alphabet-content validate` re-checks every SVG.

Chosen style: **OpenMoji** (owner's choice, 2026-11-16). Keep new pictures consistent with it.

## SVG safety

Downloaded SVGs are untrusted. Before review, remove `<script>`, `on*=` attributes, `<foreignObject>`,
and any `href`/`xlink:href` that is not a local `#fragment`. Never execute downloaded files.

## Review checklist

- [ ] License on the source page matches the record and is on the approved list
- [ ] Author and source URL correct; source is the original publisher
- [ ] SVG is clean (no scripts, handlers, external references)
- [ ] Child-appropriate and clearly shows the concept
- [ ] Style fits the set
