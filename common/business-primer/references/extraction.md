# Extraction (Phase 1)

## Documents

| Source | Command |
|---|---|
| DOCX prose | `pandoc file.docx -t plain --wrap=none -o out.txt` |
| DOCX with structure | `pandoc file.docx -t gfm --wrap=none --extract-media=out -o out.md` (also lists image positions) |
| DOCX tables | `python3 scripts/dump_docx_tables.py file.docx > tables.txt` (one line per row, merged cells de-duplicated) |
| PDF | Read natively (pages param for long PDFs) or `pdftotext -layout file.pdf -` |
| XLSX plan | `pandas.read_excel` or `markitdown` |

Keep the original-language text; translate in your own outputs but quote originals.

## Images and diagrams

- Unzip the DOCX (`unzip -o file.docx -d x/`); media is in `x/word/media/`, embedded objects in `x/word/embeddings/`.
- Map each image to its caption using the order in the pandoc `gfm` output (`<img src=...>` lines) and the caption paragraphs near it.
- **Visio (`.vsdx`) or EMF diagrams**: render with the draw.io desktop CLI if present: `/Applications/draw.io.app/Contents/MacOS/draw.io -x -f png -s 2 -o flow.png flow.vsdx` and `-f xml -o flow.drawio`. Extract shape labels from the `.drawio` XML to write the flow as text.
- View important images to check the caption mapping before naming files.
- Save as `docs/brd/flows/` (diagrams, with `.png`, original, and editable copy) and `docs/brd/ui/<UC>-<name>/<n>-<what-it-shows>.png` with a `ui/README.md` listing captions.

## Stories vs BRD comparison

Run `python3 scripts/compare_docs.py docs/brd.docx "docs/stories/*/*.docx"`. It reports, per story file, how many table rows are not found in the BRD. Zero everywhere means the BRD's use cases are identical, so only extract what the BRD adds. Rows that differ are a gap: ask which version wins.

## Enum and field inventory

To build the Statuses & values catalog, list every field whose type is a list, choice, boolean or badge across all data tables, with its table and values. Adapt the type keywords to the document language (for example Arabic `قائمة`, `اختيار`, `منطقي`, `شارات`). Then group by field, compare the values across tables, and flag any difference (different spellings of the same code, values missing in one table, codes with no definition).

## What to write into `docs/brd/`

- `README.md`: source, version, how it relates to the stories, file index.
- `overview.md`: purpose, in scope, out of scope, glossary, assumptions, risks, approvals.
- `roles-and-permissions.md`: permissions per party and the action × party matrix; note contradictions.
- `use-case-map.md`: the business's own grouping of use cases, parties per use case, story keys.
- `process-flow.md`: the main flow as numbered text, and how it differs from the use cases.
- `reference-data.md`: statuses, transitions, SLAs, every code list, attachment rules, numbering.
