---
name: letter-characters
description: Style guide and originality rules for alphabetGame's own letter characters ("Madame A", "Monsieur B"). Load before drawing or reviewing any character.
---

# Letter characters

Inspired by the _idea_ of letters as friendly characters (as used in French maternelle), but every
character is **our own original design**. Never copy or imitate _Les Alphas_ (Éditions Récréalire):
not their names, shapes, stories or art.

## Concept

Each letter becomes a character, either:

- shaped like one of its approved words — S as a snake (serpent), O as an orange, Z with zebra stripes, or
- simply the letter with a cute or funny face (big eyes, smile, hat, bow, moustache).
  Name: FR "Madame A" / "Monsieur B" (vowels Madame, consonants Monsieur is fine, alternate if it reads better);
  Y is "Monsieur I grec". Line: "Je suis Monsieur S, je fais sssss !" (include the letter sound for consonants).

## Style

- Canvas `viewBox="0 0 256 256"`, letter fills about 70% of it, centered.
- Thick rounded outlines: stroke `#2B2B2B`, width 8, `stroke-linecap/linejoin: round`.
- Palette: `#FF7A59` coral, `#FFC93C` sun, `#4FC3F7` sky, `#7BD389` leaf, `#B388EB` lilac, `#FFFFFF`, `#2B2B2B`.
- Eyes: white circles r=18 with `#2B2B2B` pupils r=8. Simple shapes, flat colors, no gradients or text.
- The letter must stay clearly readable — the child learns its shape.

## SVG rules

Plain hand-written SVG: no `<script>`, event handlers, `<foreignObject>`, external `href`, embedded
images or fonts. File: `content/languages/<lang>/characters/char_<id>.svg`. Under 8 KB each.

## Review

The owner approves all letters on `characters/_review.html`; the license-reviewer checks originality.
