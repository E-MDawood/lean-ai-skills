"""Logs in to SEHA and reads, per role, SEHA's token (and in app mode the app's token).

Two sources of roles:
- --sheet <sheet.json> (seha mode): every test user of the workbook; lists each user's role entries on SEHA and checks
  every entry whose role is in the sheet.
- --users <users.json> (app mode, or re-checks): the entries of the users file as they are, no listing.

Users run in parallel (different SEHA accounts don't affect each other); the roles of one user run one after another
(selecting a role replaces the previous session of that account).

Usage:
  python3 -I check.py --sheet sheet.json --out results.json --base-url URL --password PW [--otp 1234]
  python3 -I check.py --users docs/seha-auth/users.json --out results.json --base-url URL --app-host pal.devclan.io
  Options: --roles "<Arabic role>,<Arabic role>" (only these roles), --usernames 111,222, --parallel 3,
           --service "<service name>" (default: from the sheet, or required with --users),
           --app-storage-key persist:auth, --app-token-field token
"""
import argparse, json, subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).parent


def node(*args, timeout=480):
    p = subprocess.run(['node', *map(str, args)], capture_output=True, text=True, timeout=timeout)
    line = (p.stdout.strip().splitlines() or [''])[-1]
    try: return json.loads(line)
    except Exception: return {'error': (p.stderr or p.stdout or 'no output').strip()[-300:]}


def role_token(a, username, password, tab, account, entry):
    extra = ['--app-host', a.app_host, '--app-storage-key', a.app_storage_key, '--app-token-field', a.app_token_field] if a.app_host else []
    args = [HERE / 'role-token.mjs', a.base_url, username, password, a.otp, tab, account, entry, a.service, *extra]
    r = node(*args)
    if not r.get('tokenReceived') or (a.app_host and not r.get('appTokenReceived')):
        r = node(*args)  # one retry: SEHA test environments are slow under load
    return r


def from_sheet(a, username, roles):
    listing = node(HERE / 'list-roles.mjs', a.base_url, username, a.password, a.otp)
    if listing.get('error'): listing = node(HERE / 'list-roles.mjs', a.base_url, username, a.password, a.otp)
    results = []
    for tab in listing.get('tabs', []):
        for acc in tab['accounts']:
            for entry in acc['entries']:
                role = entry.split(' - ')[0].strip()
                if role not in roles: continue
                r = role_token(a, username, a.password, tab['tab'], acc['account'], entry)
                r.update({'username': username, 'roleAr': role, 'tab': tab['tab'], 'account': acc['account'].strip(), 'entry': entry.strip()})
                results.append(r); log(r)
    return {'username': username, 'listing': listing, 'results': results}


def from_users(a, username, entries):
    results = []
    for u in entries:
        tab = 'صحة أعمال' if u.get('isBusiness') else 'صحة طبي'
        r = role_token(a, username, u['password'], tab, u['accordionName'], u['accountName'])
        r.update({'username': username, 'roleAr': u['label'], 'tab': tab, 'account': u['accordionName'], 'entry': u['accountName'], 'id': u.get('id')})
        results.append(r); log(r)
    return {'username': username, 'listing': {}, 'results': results}


def log(r):
    state = 'SEHA token read' if r.get('tokenReceived') else f"SEHA token not read ({r.get('error')})"
    if 'appTokenReceived' in r or 'appError' in r:
        state += ', app token read' if r.get('appTokenReceived') else f", app token not read ({r.get('appError')})"
    print(f"{r['username']} | {r['roleAr']} | {state}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument('--sheet'); src.add_argument('--users')
    ap.add_argument('--out', required=True); ap.add_argument('--base-url', required=True)
    ap.add_argument('--password', default=''); ap.add_argument('--otp', default='1234')
    ap.add_argument('--parallel', type=int, default=3); ap.add_argument('--usernames', default='')
    ap.add_argument('--roles', default=''); ap.add_argument('--service', default='')
    ap.add_argument('--app-host', default=''); ap.add_argument('--app-storage-key', default='persist:auth')
    ap.add_argument('--app-token-field', default='token')
    a = ap.parse_args()
    only_roles = {x.strip() for x in a.roles.split(',') if x.strip()}
    only_users = {x.strip() for x in a.usernames.split(',') if x.strip()}
    if a.sheet:
        sheet = json.load(open(a.sheet, encoding='utf-8'))
        a.service = a.service or sheet['service']['nameAr']
        if not a.password: ap.error('--password is required with --sheet')
        roles = {r['ar'] for r in sheet['roles']} & (only_roles or {r['ar'] for r in sheet['roles']})
        users = sorted({u['username'] for u in sheet['testUsers'] if u['username'] and (not only_roles or u['roleAr'] in only_roles)})
        users = [u for u in users if not only_users or u in only_users]
        work = lambda u: from_sheet(a, u, roles)
    else:
        if not a.service: ap.error('--service is required with --users')
        entries = [u for u in json.load(open(a.users, encoding='utf-8'))
                   if (not only_roles or u['label'] in only_roles) and (not only_users or u['username'] in only_users)]
        grouped = {}
        for u in entries: grouped.setdefault(u['username'], []).append(u)
        users = sorted(grouped)
        work = lambda u: from_users(a, u, grouped[u])
    with ThreadPoolExecutor(max_workers=a.parallel) as pool:
        runs = list(pool.map(work, users))
    json.dump(runs, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


main()
