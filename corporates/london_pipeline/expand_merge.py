import json, re, glob, collections
sel = open('select400.py').read(); a_ = sel.index('def nice(n):'); b_ = sel.index('import emailpick')
ns = {'re': re}; exec(sel[a_:b_], ns); nice, short = ns['nice'], ns['short']
src = open('w2/assemble.py').read(); s0 = src.index('def segment(x):'); s1 = src.index('W = []')
exec(src[s0:s1], ns); segment, clean = ns['segment'], ns['clean']
R = {r['num']: r for r in json.load(open('w5/new_rows_f.json'))}
OUT = {}
for f in sorted(glob.glob('w5/wout/w*.json')):
    for o in json.load(open(f)): OUT[str(o['num'])] = o
P = '/home/user/Test123/corporates/london_300_rows.json'
D = json.load(open(P)); have = {r['num'] for r in D['rows']}
W = []; st = collections.Counter()
for num, r in R.items():
    if num in have: st['already merged'] += 1; continue
    o = OUT.get(num)
    if not o or not o.get('body'): st['no email written'] += 1; continue
    if o.get('hold') and re.search(r'different (company|organisation)|non-London|no London|no UK|only a Manchester|Marlow|Fareham|Brisbane|Cologne|Dutch|Milan|French|Mold|Wales|US-based|\bUS\b|only address|not a London|Greater Manchester', o['hold'], re.I):
        st['dropped: wrong company / not London'] += 1; continue
    if num == '04740661': o['subject'] = 'Team football near Eversholt Street, Sam'
    m = re.search(r'-minute walk from your (?:office|studio)[^.]*? (?:on|at) ([^.]+)\.', o['body'])
    body_street = m.group(1).strip() if m and not re.match(r'^[A-Z]{1,2}\d', m.group(1).strip()) else ''
    x, a = r['x'], r['a']
    title = clean(r['title'], 60); fn = clean(r['fn'], 20); full = clean(' '.join(p for p in [a.get('contact_first_name'), a.get('contact_last_name')] if p), 40)
    g = re.match(r'Hi ([^,\n]+),', o['body'])
    if fn and (not g or g.group(1).strip() != fn): fn = full = title = ''  # writer rejected the extracted contact (artefact / wrong person)
    W.append({'num': num, 'company': nice(x['name']), 'short': short(x['name']), 'segment': segment(x), 'area': r['office_pc'].split()[0],
              'priority': 1 if r['tier'].startswith('a/b named person') and 'via' not in r['tier'] else 2 if 'via' in r['tier'] else 3,
              'web': r['web'], 'hc': r['hc'], 'acc': x['acc'], 'inc': x['inc'], 'reg_addr': x['addr'].title(), 'reg_pc': x['pc'],
              'fn': fn, 'full': full, 'title': title,
              'email': r['email'], 'tier': r['tier'], 'email_src': a.get('contact_source_url') or a.get('general_email_source_url') or r['web'],
              'office_street': body_street or ('' if re.search(r'manchester|leeds|birmingham|bristol|edinburgh|glasgow', r['office_street'], re.I) else clean(r['office_street'], 70)),
              'office_pc': r['office_pc'], 'office_basis': r['office_basis'], 'pitch': r['venue'], 'venue_url': 'https://www.fcurban.com/locations/' + r['slug'],
              'walk': r['walk'], 'personal': '', 'personal_src': '',
              'subject': o.get('subject', ''), 'body': o['body'], 'followup': o.get('followup', ''), 'hook': o.get('hook', ''), 'hook_src': o.get('hook_source_url', ''),
              'hook_type': o.get('hook_type', ''), 'confidence': o.get('confidence', ''), 'notes': o.get('notes', ''), 'hold': o.get('hold', ''), 'batch': 'Expansion (Sep 2026)'})
    st['added'] += 1; st['hold' if W[-1]['hold'] else 'ready'] += 1
W.sort(key=lambda w: (bool(w['hold']), w['priority'], w['walk']))
D['rows'] += W
json.dump(D, open(P, 'w'), indent=1)
print(dict(st), 'total rows', len(D['rows']))
