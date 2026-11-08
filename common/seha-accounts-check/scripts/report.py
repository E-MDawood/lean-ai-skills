"""Builds the Markdown report (and, in seha mode, the users JSON) from check.py's results.

seha mode: SEHA's token per role against the sheet's permissions for that role.
  python3 -I report.py seha --sheet sheet.json --results results.json --report report.md \
      --users-out docs/seha-auth/users.json --password PW [--existing-users docs/seha-auth/users.json] \
      [--merge] [--group auto|yes|no]
  --merge (update mode): keep the existing entries and replace or add only the checked ones; entries whose role is no
  longer in the sheet are dropped and listed in the notes.

app mode: per role, every permission ID in SEHA's token, mapped through the reference's appPermission, against the
permissions in the app's own token.
  python3 -I report.py app --reference docs/seha-auth/permissions.json --env DEV --results results.json \
      --report report.md [--app-claim Permissions]
"""
import argparse, json, uuid


def service_header(service, env, title):
    return [f'# {title} ({env})', '',
            f"**Service:** {service.get('nameAr', '')} / {service.get('nameEn', '')}  ",
            f"**Service URL:** {service.get('url', '')}  ", f"**Client ID:** {service.get('clientId', '')}", '']


def table(rows, head):
    return ['| ' + ' | '.join(head) + ' |', '|' + '---|' * len(head)] + ['| ' + ' | '.join(map(str, r)) + ' |' for r in rows]


def seha_mode(a):
    sheet = json.load(open(a.sheet, encoding='utf-8'))
    runs = json.load(open(a.results, encoding='utf-8'))
    names = {int(k): v for k, v in sheet['permissions'].items()}
    known = set(names)
    found = {}
    for run in runs:
        for r in run['results']: found.setdefault(r['roleAr'], []).append(r)
    existing = []
    if a.existing_users:
        try: existing = json.load(open(a.existing_users, encoding='utf-8'))
        except FileNotFoundError: pass
    ids = {(u['username'], u['accountName']): u['id'] for u in existing}
    sheet_users = {}
    for u in sheet['testUsers']: sheet_users.setdefault(u['roleAr'], set()).add(u['username'])
    checked = {r['roleAr'] for run in runs for r in run['results']} if a.merge else None
    rows, users, notes = [], [], []
    for role in sheet['roles']:
        if checked is not None and role['ar'] not in checked: continue
        hits = found.get(role['ar'], [])
        if not hits:
            listed = ', '.join(sorted(x for x in sheet_users.get(role['ar'], []) if x)) or '-'
            rows.append([role['en'], role['ar'], listed, '-', '-', '-', 'Issue: no test user has this role on SEHA']); continue
        for r in hits:
            issues = []
            service = 'Yes' if r.get('serviceFound') else ('No' if 'services' in r else '?')
            if service == 'No': issues.append('service not in the menu (menu: ' + ', '.join(r.get('services', [])) + ')')
            perms = 'Token not read'
            if r.get('tokenReceived'):
                try: got = set(json.loads(r['claims'].get('PermissionList') or '[]'))
                except Exception: got = set()
                want = set(role['permissions'])
                missing, extra, other = sorted(want - got), sorted((got & known) - want), sorted(got - known)
                parts = ([f"Missing {', '.join(f'{p} {names[p]}' for p in missing)}"] if missing else []) + \
                        ([f"Extra {', '.join(f'{p} {names[p]}' for p in extra)}"] if extra else []) + \
                        ([f"IDs not in the sheet: {', '.join(map(str, other))}"] if other else [])
                perms = '; '.join(parts) or 'Match'
                issues += parts
            else:
                issues.append('token not read: ' + str(r.get('error')))
            org = r['entry'].split(' - ', 1)[1] if ' - ' in r['entry'] else ''
            if r['username'] not in sheet_users.get(role['ar'], set()):
                notes.append(f"{role['en']}: on SEHA under {r['username']}; the sheet lists {', '.join(sorted(x for x in sheet_users.get(role['ar'], []) if x)) or 'no user'}.")
            rows.append([role['en'], role['ar'], r['username'], org, service, perms, 'Correct' if not issues else 'Issue'])
            users.append({'label': role['ar'], 'username': r['username'], 'password': a.password, 'accordionName': r['account'],
                          'accountName': r['entry'], 'id': ids.get((r['username'], r['entry'])) or str(uuid.uuid4()),
                          **({'isBusiness': True} if 'أعمال' in r['tab'] else {}), '_group': role.get('party') or org or r['account']})
    for run in runs:
        if run['listing'].get('error'): notes.append(f"Test user {run['username']} could not be listed: {run['listing']['error']}")
        elif not run['results'] and not a.merge: notes.append(f"Test user {run['username']} holds none of the sheet's roles on SEHA.")
    if a.merge:
        sheet_roles = {r['ar'] for r in sheet['roles']}
        replaced = {u['label'] for u in users}
        kept = [u for u in existing if u['label'] not in replaced and u['label'] in sheet_roles]
        dropped = [u for u in existing if u['label'] not in sheet_roles]
        notes += [f"Removed from users.json (role no longer in the sheet): {u['label']} ({u['username']})." for u in dropped]
        groups_of = {u['label']: u.get('category') for u in existing}
        users = [{**{k: v for k, v in u.items() if k != 'category'}, '_group': groups_of.get(u['label']) or ''} for u in kept] + users
    groups = list(dict.fromkeys(u['_group'] for u in users))
    if a.group == 'yes' or (a.group == 'auto' and 1 < len(groups) < len(users)):
        users = [{'category': u['_group'], **u} for u in users]
        users.sort(key=lambda u: groups.index(u['category']))
    for u in users: u.pop('_group')
    json.dump(users, open(a.users_out, 'w', encoding='utf-8'), ensure_ascii=False, indent=4)
    open(a.users_out, 'a').write('\n')
    correct = sum(r[-1] == 'Correct' for r in rows)
    md = service_header(sheet['service'], sheet['environment'], 'SEHA accounts check' + (' (update)' if a.merge else ''))
    md += [f"**Result:** {correct} roles correct, {len(rows) - correct} with issues.", '']
    md += table(rows, ['Role', 'Arabic role', 'Test user', 'Organization', 'Service in menu', 'SEHA token permissions', 'Result'])
    if notes: md += ['', '## Notes', ''] + [f'- {n}' for n in notes]
    return md


def app_mode(a):
    ref = json.load(open(a.reference, encoding='utf-8'))
    runs = json.load(open(a.results, encoding='utf-8'))
    env = a.env.upper()
    by_id = {p['sehaIds'].get(env): p for p in ref['permissions'] if p['sehaIds'].get(env) is not None}
    rows, notes = [], []
    unmapped_global = sorted(p['en'] for p in ref['permissions'] if p['sehaIds'].get(env) and not p.get('appPermission'))
    if unmapped_global:
        notes.append('No appPermission in the reference for: ' + ', '.join(unmapped_global) + ' (expected when the app has no such permission; otherwise add the mapping).')
    for run in runs:
        for r in run['results']:
            issues = []
            if not r.get('tokenReceived'): issues.append('SEHA token not read: ' + str(r.get('error')))
            if not r.get('appTokenReceived'): issues.append('app token not read: ' + str(r.get('appError')))
            mapping = '-'
            if not issues:
                try: seha_ids = set(json.loads(r['claims'].get('PermissionList') or '[]'))
                except Exception: seha_ids = set()
                raw = r['appClaims'].get(a.app_claim)
                if isinstance(raw, str): app_values = {x.strip() for x in raw.split(',') if x.strip()}
                elif isinstance(raw, list): app_values = {str(x).strip() for x in raw}
                else: app_values = set()
                expected, unknown, no_mapping = {}, [], []
                for sid in sorted(seha_ids):
                    p = by_id.get(sid)
                    if not p: unknown.append(str(sid)); continue
                    ap = p.get('appPermission')
                    if not ap: no_mapping.append(f"{sid} {p['en']}"); continue
                    for v in (ap.get('value'), ap.get('name')):
                        if v is not None: expected[str(v)] = f"{ap.get('name') or ap.get('value')} ({sid} {p['en']})"
                expected_keys = {k for k in expected}
                present = {k for k in expected_keys if k in app_values}
                missing_names = sorted({expected[k] for k in expected_keys - present} - {expected[k] for k in present})
                valid_app = {str(p['appPermission'].get(f)) for p in ref['permissions'] if p.get('appPermission') for f in ('value', 'name') if p['appPermission'].get(f) is not None}
                extra = sorted(v for v in app_values if v not in expected_keys)
                parts = ([f"Missing in the app token: {', '.join(missing_names)}"] if missing_names else []) + \
                        ([f"Extra in the app token: {', '.join(extra)}" + ('' if all(e in valid_app for e in extra) else ' (some are not in the mapping at all)')] if extra else []) + \
                        ([f"SEHA IDs unknown to the reference: {', '.join(unknown)}"] if unknown else []) + \
                        ([f"SEHA permissions with no app mapping: {', '.join(no_mapping)}"] if no_mapping else [])
                mapping = '; '.join(parts) or 'Match'
                issues += parts
            organization = r['entry'].split(' - ', 1)[1] if ' - ' in r['entry'] else ''
            other_issues = [i for i in issues if i not in mapping]
            if not issues: result = 'Correct'
            elif other_issues: result = 'Issue: ' + '; '.join(other_issues)
            else: result = 'Issue'
            rows.append([r['roleAr'], r['username'], organization, mapping, result])
    correct = sum(r[-1] == 'Correct' for r in rows)
    md = service_header(ref['services'].get(env, {}), env, 'SEHA to app permission mapping check')
    md += [f"**Result:** {correct} roles correct, {len(rows) - correct} with issues. App claim checked: `{a.app_claim}`.", '']
    md += table(rows, ['Role', 'Test user', 'Organization', 'Mapping (SEHA token to app token)', 'Result'])
    if notes: md += ['', '## Notes', ''] + [f'- {n}' for n in notes]
    return md


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='mode', required=True)
    s = sub.add_parser('seha')
    s.add_argument('--sheet', required=True); s.add_argument('--results', required=True); s.add_argument('--report', required=True)
    s.add_argument('--users-out', required=True); s.add_argument('--password', required=True)
    s.add_argument('--existing-users', default=''); s.add_argument('--merge', action='store_true')
    s.add_argument('--group', choices=['auto', 'yes', 'no'], default='auto')
    p = sub.add_parser('app')
    p.add_argument('--reference', required=True); p.add_argument('--env', required=True)
    p.add_argument('--results', required=True); p.add_argument('--report', required=True)
    p.add_argument('--app-claim', default='Permissions')
    a = ap.parse_args()
    md = seha_mode(a) if a.mode == 'seha' else app_mode(a)
    open(a.report, 'w', encoding='utf-8').write('\n'.join(md) + '\n')
    print('\n'.join(md))


main()
