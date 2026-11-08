"""Reads the PM's SEHA accounts workbook for one environment into sheet.json.

Usage: python3 -I read_sheet.py <workbook.xlsx> <DEV|QA|STG|PROD> <out.json>

Expected tabs (the standard SEHA accounts workbook; names matched loosely):
- "Services Profile": blocks "Profile in SEHA <Env>" with Services Name AR / EN, Services URL, Client ID, Client Secret.
- "Permissions": Permissions Name_EN, Permissions Name_AR, Level, Permissions_ID_<Env> columns.
- "Roles & Permissions" (not "(OLD)"): Role (English), Role (Arabic), Permission label (English) per row; a role's
  name is merged over its permission rows.
- "Test Users": SEHA Environment, Role_AR, Test User, account (حساب), organization; merged cells over role rows.
The client secret is never written out.
"""
import json, re, sys
import openpyxl

ENV_ALIASES = {"DEV": ["dev", "dv"], "QA": ["qa"], "STG": ["stg", "staging"], "PROD": ["prod", "production"]}


def resolved(ws):
    values = {(c.row, c.column): c.value for row in ws.iter_rows() for c in row}
    merged = set()
    for rg in ws.merged_cells.ranges:
        top = ws.cell(rg.min_row, rg.min_col).value
        for r in range(rg.min_row, rg.max_row + 1):
            for c in range(rg.min_col, rg.max_col + 1):
                values[(r, c)] = top
                if r > rg.min_row: merged.add((r, c))
    return values, merged


def sheet(wb, *words, exclude=None):
    for name in wb.sheetnames:
        low = name.lower()
        if all(w in low for w in words) and not (exclude and exclude in low): return wb[name]
    raise SystemExit(f'No tab matching {words} in {wb.sheetnames}')


def text(v): return '' if v is None else str(v).strip()


def main():
    path, env, out = sys.argv[1], sys.argv[2].upper(), sys.argv[3]
    aliases = ENV_ALIASES[env]
    wb = openpyxl.load_workbook(path)

    sp = sheet(wb, 'service')
    profile, current = {}, None
    for row in sp.iter_rows(values_only=True):
        a, b = text(row[0]), text(row[1]) if len(row) > 1 else ''
        if a.lower().startswith('profile info'):
            current = any(x in b.lower().split() or b.lower().endswith(x) for x in aliases)
            continue
        if current and a and 'secret' not in a.lower():
            profile[a] = b
    service = {
        'nameAr': next((v for k, v in profile.items() if 'name ar' in k.lower()), ''),
        'nameEn': next((v for k, v in profile.items() if 'name en' in k.lower()), ''),
        'url': next((v for k, v in profile.items() if 'url' in k.lower()), ''),
        'clientId': next((v for k, v in profile.items() if 'client id' in k.lower()), ''),
    }

    ps = sheet(wb, 'permission', exclude='role')
    header = [text(c).lower() for c in next(ps.iter_rows(max_row=1, values_only=True))]
    id_col = next(i for i, h in enumerate(header) if 'id' in h and any(h.endswith('_' + a) or h.endswith(a) for a in aliases))
    permissions = {}
    for row in ps.iter_rows(min_row=2, values_only=True):
        en = text(row[0]).split('\n')[0].strip()
        if en and row[id_col] not in (None, ''):
            permissions[en.lower()] = {'id': int(row[id_col]), 'en': en, 'ar': text(row[1])}

    rs = sheet(wb, 'role', 'permission', exclude='old')
    values, _ = resolved(rs)
    hdr = [text(rs.cell(1, c).value).lower() for c in range(1, rs.max_column + 1)]
    col = lambda *w: next(i + 1 for i, h in enumerate(hdr) if all(x in h for x in w))
    c_en, c_ar, c_perm = col('role', 'english'), col('role', 'arabic'), col('permission', 'english')
    c_party = next((i + 1 for i, h in enumerate(hdr) if 'party' in h), None)
    roles, missing = {}, set()
    for r in range(2, rs.max_row + 1):
        en, ar, perm = text(values.get((r, c_en))), text(values.get((r, c_ar))), text(values.get((r, c_perm)))
        if not en: continue
        role = roles.setdefault(en, {'en': en, 'ar': ar, 'party': text(values.get((r, c_party))) if c_party else '', 'permissions': []})
        if perm:
            key = perm.split('\n')[0].strip().lower()
            if key in permissions: role['permissions'].append(permissions[key]['id'])
            else: missing.add(perm)
    for role in roles.values(): role['permissions'] = sorted(set(role['permissions']))

    us = sheet(wb, 'test', 'user')
    values, merged = resolved(us)
    users, last_user = [], None
    for r in range(2, us.max_row + 1):
        env_code = text(values.get((r, 1))).lower()
        if env_code not in aliases: continue
        role_ar, user, account, org = (text(values.get((r, c))) for c in (2, 3, 4, 5))
        # A role row whose user cell is empty but whose account and organization cells are merged with the row above
        # belongs to the same test user: the sheet only merged some of the columns.
        if not user and last_user and (r, 4) in merged and (r, 5) in merged: user = last_user
        if user: last_user = user
        if role_ar: users.append({'roleAr': role_ar, 'username': user, 'account': account, 'organization': org, 'row': r})

    json.dump({'environment': env, 'service': service, 'permissions': {v['id']: v['en'] for v in permissions.values()},
               'roles': list(roles.values()), 'testUsers': users, 'unmappedPermissionLabels': sorted(missing)},
              open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"service: {service['nameAr']} | {service['url']}; permissions {len(permissions)}; roles {len(roles)}; "
          f"test-user rows {len(users)}; usernames {sorted({u['username'] for u in users if u['username']})}; "
          f"unmapped labels {len(missing)}")


if __name__ == '__main__':
    main()
