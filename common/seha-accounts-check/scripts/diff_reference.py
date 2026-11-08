"""Compares a new permissions reference (built from the PM's updated workbook) with the stored one, for update mode.

Usage: python3 -I diff_reference.py <old permissions.json> <new permissions.json> <ENV> [--users docs/seha-auth/users.json]
Prints the changes and, last, one line "ROLES_TO_CHECK=<Arabic role>,<Arabic role>" for check.py --roles.
A role is re-checked when it is new, when its permission list changed, or when the SEHA ID (in ENV) of one of its
permissions changed. Roles of the new sheet that no entry of users.json covers are listed as well.
"""
import argparse, json


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('old'); ap.add_argument('new'); ap.add_argument('env'); ap.add_argument('--users', default='')
    a = ap.parse_args()
    env = a.env.upper()
    old, new = json.load(open(a.old, encoding='utf-8')), json.load(open(a.new, encoding='utf-8'))
    op = {p['en'].lower(): p for p in old['permissions']}
    np_ = {p['en'].lower(): p for p in new['permissions']}
    orole = {r['en']: r for r in old['roles']}
    nrole = {r['en']: r for r in new['roles']}
    changed_ids = {k for k in op.keys() & np_.keys() if op[k]['sehaIds'].get(env) != np_[k]['sehaIds'].get(env)}

    print('## Permissions')
    for k in sorted(np_.keys() - op.keys()): print(f"+ {np_[k]['en']} ({env} ID {np_[k]['sehaIds'].get(env)})")
    for k in sorted(op.keys() - np_.keys()): print(f"- {op[k]['en']}")
    for k in sorted(changed_ids): print(f"~ {np_[k]['en']}: {env} ID {op[k]['sehaIds'].get(env)} -> {np_[k]['sehaIds'].get(env)}")

    print('## Roles')
    to_check = []
    for en in nrole:
        n = nrole[en]; o = orole.get(en)
        if not o:
            print(f"+ {en} ({n['ar']}): {len(n['permissions'])} permissions"); to_check.append(n['ar']); continue
        added = [p for p in n['permissions'] if p not in o['permissions']]
        removed = [p for p in o['permissions'] if p not in n['permissions']]
        ids = [p for p in n['permissions'] if p.lower() in changed_ids]
        if added or removed or ids or n['ar'] != o['ar']:
            print(f"~ {en}: " + '; '.join(x for x in [
                f"added {', '.join(added)}" if added else '', f"removed {', '.join(removed)}" if removed else '',
                f"ID changed for {', '.join(ids)}" if ids else '', f"Arabic name {o['ar']} -> {n['ar']}" if n['ar'] != o['ar'] else ''] if x))
            to_check.append(n['ar'])
    for en in orole.keys() - nrole.keys(): print(f"- {en} ({orole[en]['ar']}) removed from the sheet")

    if a.users:
        covered = {u['label'] for u in json.load(open(a.users, encoding='utf-8'))}
        missing = [r['ar'] for r in new['roles'] if r['ar'] not in covered]
        if missing:
            print('## Roles without an entry in users.json')
            for m in missing: print(f'+ {m}')
            to_check += [m for m in missing if m not in to_check]

    print('ROLES_TO_CHECK=' + ','.join(dict.fromkeys(to_check)))


main()
