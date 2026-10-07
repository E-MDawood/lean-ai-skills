#!/usr/bin/env python3
"""Check whether each story document's table rows also appear in the BRD.

Prints, per story file, the number of rows and how many are not found in the BRD,
followed by each missing row and the closest BRD row (so wording changes are easy
to spot). Zero missing rows everywhere means the BRD's use cases match the stories.

Usage: python3 compare_docs.py BRD.docx "docs/stories/*/*.docx"
"""
import difflib
import glob
import sys

import docx


def table_rows(path):
    out = []
    for table in docx.Document(path).tables:
        for row in table.rows:
            cells = []
            for cell in row.cells:
                text = " ".join(cell.text.split())
                if not cells or cells[-1] != text:
                    cells.append(text)
            line = " | ".join(cells)
            if line.strip(" |"):
                out.append(line)
    return out


def main(brd_path, pattern):
    brd = set(table_rows(brd_path))
    brd_list = list(brd)
    for path in sorted(glob.glob(pattern)):
        rows = table_rows(path)
        missing = [r for r in rows if r not in brd]
        print(f"## {path}: {len(rows)} rows, {len(missing)} not in BRD")
        for row in missing:
            best = difflib.get_close_matches(row, brd_list, 1, 0.6)
            print(f"  STORY: {row[:300]}")
            print(f"  BRD  : {best[0][:300] if best else 'NONE'}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
