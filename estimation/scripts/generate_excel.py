"""
Generate a Sprint Time Estimation Excel file from the approved template.

Usage:
    python generate_excel.py \
        --data /tmp/estimation_data.json \
        --output "docs/estimations/Sprint 5 Time Estimation.xlsx" \
        --skill-dir ".claude/skills/estimation"

JSON input schema:
    {
        "jira_base_url": "https://leansa.atlassian.net/browse/",
        "stories": [
            {
                "ticket": "REDJ-464",
                "name": "Story name",
                "url": "https://leansa.atlassian.net/browse/REDJ-464",
                "execution_order": 1,
                "dependencies": "REDJ-463",
                "estimation_hours": 8,
                "justification": "Reason here",
                "reduction_tips": "Tip here or null if no genuine reduction exists"
            }
        ]
    }

Notes:
  - dependencies: single ticket ID becomes a clickable hyperlink. Multiple comma-separated
    IDs remain plain text because Excel only supports one hyperlink per cell.
  - reduction_tips: omit or set to null/empty when there is no genuine reduction opportunity.
  - Row heights are calculated automatically from justification and reduction_tips text length.
"""

import argparse
import json
import os
import copy
from urllib.parse import urlparse
from openpyxl import load_workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

LINK_COLOR = '0563C1'
DEFAULT_JIRA_BASE = 'https://leansa.atlassian.net/browse/'

# Width (in Excel character units) of Justification and Reduction Tips columns.
_WRAP_COL_WIDTH = 34


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--data', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--skill-dir', required=True)
    return p.parse_args()


def apply_link_style(cell):
    existing = cell.font or Font()
    cell.font = Font(
        name=existing.name or 'Arial',
        size=existing.size or 10,
        color=LINK_COLOR,
        underline='single',
    )


def apply_saved(cell, saved_styles):
    for k, v in saved_styles.items():
        setattr(cell, k, v)


def save_row_styles(ws, row):
    return {
        col: {
            'font': copy.copy(ws.cell(row=row, column=col).font),
            'fill': copy.copy(ws.cell(row=row, column=col).fill),
            'border': copy.copy(ws.cell(row=row, column=col).border),
            'alignment': copy.copy(ws.cell(row=row, column=col).alignment),
            'number_format': ws.cell(row=row, column=col).number_format,
        }
        for col in range(1, 8)
    }


def estimate_row_height(justification, reduction_tips):
    def count_lines(text):
        if not text:
            return 1
        lines, current = 1, 0
        for word in str(text).split():
            wlen = len(word) + 1
            if current + wlen > _WRAP_COL_WIDTH:
                lines += 1
                current = wlen
            else:
                current += wlen
        return lines

    max_lines = max(count_lines(justification), count_lines(reduction_tips))
    return max(22, max_lines * 15 + 4)


def write_story_row(ws, r_idx, story, saved, jira_base):
    justification = story.get('justification', '') or ''
    reduction_tips = story.get('reduction_tips', '') or ''
    ws.row_dimensions[r_idx].height = estimate_row_height(justification, reduction_tips)

    cell = ws.cell(row=r_idx, column=1, value=story.get('execution_order', ''))
    apply_saved(cell, saved[1])

    cell = ws.cell(row=r_idx, column=2, value=story['ticket'])
    apply_saved(cell, saved[2])
    cell.hyperlink = story.get('url', '')
    apply_link_style(cell)

    cell = ws.cell(row=r_idx, column=3, value=story['name'])
    apply_saved(cell, saved[3])
    cell.hyperlink = story.get('url', '')
    apply_link_style(cell)

    _write_dependencies(ws, r_idx, story, saved[4], jira_base)

    cell = ws.cell(row=r_idx, column=5, value=story.get('estimation_hours', ''))
    apply_saved(cell, saved[5])
    cell.alignment = copy.copy(saved[5]['alignment'])

    cell = ws.cell(row=r_idx, column=6, value=justification)
    apply_saved(cell, saved[6])

    cell = ws.cell(row=r_idx, column=7, value=reduction_tips)
    apply_saved(cell, saved[7])


def _write_dependencies(ws, r_idx, story, saved_style, jira_base):
    deps_raw = story.get('dependencies', '') or ''
    cell = ws.cell(row=r_idx, column=4, value=deps_raw)
    apply_saved(cell, saved_style)

    if not deps_raw:
        return

    dep_list = [d.strip() for d in deps_raw.split(',') if d.strip()]
    if len(dep_list) == 1:
        cell.hyperlink = f'{jira_base}{dep_list[0]}'
    else:
        parsed = urlparse(jira_base)
        base_domain = f'{parsed.scheme}://{parsed.netloc}'
        jql_keys = '%2C%20'.join(dep_list)
        cell.hyperlink = f'{base_domain}/issues/?jql=issueKey%20in%20({jql_keys})'
    apply_link_style(cell)


def write_totals_row(ws, totals_row, last_data_row, saved_total):
    ws.row_dimensions[totals_row].height = 22
    for col in range(1, 8):
        cell = ws.cell(row=totals_row, column=col)
        apply_saved(cell, saved_total[col])

    c = ws.cell(row=totals_row, column=1, value='Total')
    apply_saved(c, saved_total[1])
    ws.cell(row=totals_row, column=5, value=f'=SUM(E2:E{last_data_row})')


def update_summary_formulas(ws2, last_data_row):
    replacements = [
        ('E2:E8', f'E2:E{last_data_row}'),
        ('B2:B8', f'B2:B{last_data_row}'),
    ]
    for row in ws2.iter_rows():
        for cell in row:
            if not isinstance(cell.value, str):
                continue
            for old, new in replacements:
                cell.value = cell.value.replace(old, new)


def main():
    args = parse_args()

    with open(args.data, encoding='utf-8') as f:
        data = json.load(f)

    stories = data['stories']
    jira_base = data.get('jira_base_url', DEFAULT_JIRA_BASE).rstrip('/') + '/'

    template_path = os.path.join(args.skill_dir, 'assets', 'template.xlsx')
    wb = load_workbook(template_path)
    ws1 = wb['Time estimation']

    saved = save_row_styles(ws1, row=2)
    saved_total = save_row_styles(ws1, row=ws1.max_row)

    ws1.delete_rows(2, ws1.max_row - 1)

    for r_idx, story in enumerate(stories, start=2):
        write_story_row(ws1, r_idx, story, saved, jira_base)

    last_data_row = len(stories) + 1
    totals_row = last_data_row + 1
    write_totals_row(ws1, totals_row, last_data_row, saved_total)

    ws1.auto_filter.ref = f'A1:{get_column_letter(7)}{last_data_row}'

    update_summary_formulas(wb['Summary'], last_data_row)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    wb.save(args.output)
    print(f'Saved: {args.output}')


if __name__ == '__main__':
    main()
