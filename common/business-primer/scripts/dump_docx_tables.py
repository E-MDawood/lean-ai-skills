#!/usr/bin/env python3
"""Print every table row of a DOCX as one line: cells joined by ' | '.

Merged cells repeat in python-docx, so consecutive duplicate cells are collapsed.
Tables are separated by a '===== TABLE n' line.

Usage: python3 dump_docx_tables.py file.docx [> tables.txt]
"""
import sys

import docx


def rows(path):
    doc = docx.Document(path)
    for n, table in enumerate(doc.tables, 1):
        yield f"===== TABLE {n}"
        for row in table.rows:
            cells = []
            for cell in row.cells:
                text = " ".join(cell.text.split())
                if not cells or cells[-1] != text:
                    cells.append(text)
            yield " | ".join(cells)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    for line in rows(sys.argv[1]):
        print(line)
