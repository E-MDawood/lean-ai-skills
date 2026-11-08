"""Writes the permissions reference from the PM's workbook: every SEHA permission with its ID in each environment,
each role with its permissions, and the service profile per environment (never the client secret). It outlives the
workbook, which is not kept in the repo, and is what the app and update modes compare against.

Usage: python3 -I build_reference.py <workbook.xlsx> <out: docs/seha-auth/permissions.json> [--keep-app-mapping]
With --keep-app-mapping, an existing file's appPermission values are kept for permissions that still exist.
"""
import datetime, json, os, sys
import openpyxl

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from read_sheet import ENV_ALIASES, resolved, sheet, text


def main():
    path, out = sys.argv[1], sys.argv[2]
    keep = '--keep-app-mapping' in sys.argv
    wb = openpyxl.load_workbook(path)

    services, block = {}, None
    for row in sheet(wb, 'service').iter_rows(values_only=True):
        a, b = text(row[0]), text(row[1]) if len(row) > 1 else ''
        if a.lower().startswith('profile info'):
            block = next((env for env, al in ENV_ALIASES.items() if any(b.lower().endswith(x) or x in b.lower().split() for x in al)), None)
            if block: services[block] = {}
            continue
        if block and a and 'secret' not in a.lower():
            key = {'services name ar': 'nameAr', 'services name en': 'nameEn', 'services url': 'url', 'client id': 'clientId'}.get(a.lower())
            if key: services[block][key] = b

    ps = sheet(wb, 'permission', exclude='role')
    header = [text(c).lower() for c in next(ps.iter_rows(max_row=1, values_only=True))]
    env_cols = {env: next((i for i, h in enumerate(header) if 'id' in h and any(h.endswith('_' + x) for x in al)), None)
                for env, al in ENV_ALIASES.items()}
    level_col = next((i for i, h in enumerate(header) if 'level' in h), None)
    old = {}
    if keep:
        try:
            for p in json.load(open(out, encoding='utf-8'))['permissions']: old[p['en'].lower()] = p.get('appPermission')
        except FileNotFoundError: pass
    permissions = []
    for row in ps.iter_rows(min_row=2, values_only=True):
        en = text(row[0]).split('\n')[0].strip()
        if not en: continue
        ids = {env: (int(row[c]) if c is not None and row[c] not in (None, '') else None) for env, c in env_cols.items()}
        permissions.append({'en': en, 'ar': text(row[1]), 'level': text(row[level_col]) if level_col is not None else '',
                            'sehaIds': ids, 'appPermission': old.get(en.lower())})

    rs = sheet(wb, 'role', 'permission', exclude='old')
    values, _ = resolved(rs)
    hdr = [text(rs.cell(1, c).value).lower() for c in range(1, rs.max_column + 1)]
    col = lambda *w: next(i + 1 for i, h in enumerate(hdr) if all(x in h for x in w))
    c_en, c_ar, c_perm = col('role', 'english'), col('role', 'arabic'), col('permission', 'english')
    c_party = next((i + 1 for i, h in enumerate(hdr) if 'party' in h), None)
    roles = {}
    for r in range(2, rs.max_row + 1):
        en = text(values.get((r, c_en)))
        if not en: continue
        role = roles.setdefault(en, {'en': en, 'ar': text(values.get((r, c_ar))),
                                     'party': text(values.get((r, c_party))) if c_party else '', 'permissions': []})
        perm = text(values.get((r, c_perm))).split('\n')[0].strip()
        if perm and perm not in role['permissions']: role['permissions'].append(perm)

    ref = {'generatedFrom': path.split('/')[-1], 'generatedAt': datetime.date.today().isoformat(),
           'services': services, 'permissions': permissions, 'roles': list(roles.values())}
    json.dump(ref, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=4)
    open(out, 'a').write('\n')
    print(f"{len(permissions)} permissions, {len(roles)} roles, environments {sorted(services)}")


if __name__ == '__main__':
    main()
