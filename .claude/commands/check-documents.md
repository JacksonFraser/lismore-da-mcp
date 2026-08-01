---
description: Validate documents/ — real PDFs, no error pages, correct LEP edition, indexed
allowed-tools: Bash(.venv/bin/python scripts/check_documents.py:*), Bash(file:*), Bash(ls:*), Read
---

Run the document validator and act on what it finds:

```
!.venv/bin/python scripts/check_documents.py $ARGUMENTS
```

(Pass `--new` to check only files git reports as added or modified.)

## Why this exists

Everything under `documents/` is committed and published, and the document tools search PDF text —
so a file that is secretly an error page surfaces as *an answer to a planning question*. Fifteen
such files were committed once under names promising real content and had to be deleted; see
`documents/DOCUMENT_INDEX.md`. The checker also catches the LEP 2000 / LEP 2012 mix-up described in
`SCRAPER.md` §6, which publishes superseded controls as current.

## Interpreting the output

**A failing file is not automatically junk.** Diagnose before deleting:

- *"almost no text in the opening pages"* — council publications often lead with a wholly graphical
  cover. Open it and look past page 1 before concluding anything. This exact check wrongly rejected
  the genuine 60-page 2026-27 fee schedule once.
- *"text refers to LEP 2000 but the filename does not"* — usually real. Confirm by looking at the
  zone codes in its own text: `2(a) Residential` / `3(a) Business` are LEP 2000; `R2` / `E2` are
  LEP 2012. If it is the superseded edition, rename it to `…-lep2000.pdf`, add it to
  `LEP_2000_DOCUMENTS` in `src/lismore_da_mcp/data/instruments.py`, and correct its
  `DOCUMENT_INDEX.md` row — do not delete it, since for some chapters no 2012 edition exists.
- *"not in DOC_CATEGORIES"* — the file is unreachable by every tool. Either move it to a searched
  category or add the category to `config.DOC_CATEGORIES` (and rebuild the index).
- *"no entry in DOCUMENT_INDEX.md"* — add one, with what the document is and where it came from.

After any change that adds or moves a document, rebuild the search index:

```
PYTHONPATH=src .venv/bin/python -m lismore_da_mcp.index
```

Report what you found, what you changed, and anything you judged a false positive and why.
