import json, glob, re, math, subprocess, collections, urllib.parse, concurrent.futures as cf, sys
U = {x['num']: x for x in json.load(open('w5/uniq.json'))}
O = {o['num']: o for o in json.load(open('w5/office.json'))}
A = {}
for f in sorted(glob.glob('w5/agent_out/*.json')):
    try:
        for x in json.load(open(f)): A[str(x.get('num'))] = x
    except Exception as e: print('bad', f, e)
V = json.load(open('w5/venues_active.json'))
def hav(a, b, c, d):
    R = 6371000; p1, p2 = math.radians(a), math.radians(c); dl = math.radians(d - b); dp = p2 - p1
    return 2 * R * math.asin(math.sqrt(math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2))
WALK = lambda m: m * 1.3 / 80.0
PCRE = re.compile(r'^((?:EC|WC)[1-4][A-Z]?|(?:E|N|NW|SE|SW|W)\d{1,2}[A-Z]?) ?(\d[A-Z]{2})$')
pcs = {(a.get('office_postcode') or '').upper().strip() for a in A.values()} | {o['office_pc'] for o in O.values()}
pl = sorted(p for p in pcs if PCRE.match(p)); geo = {}
for i in range(0, len(pl), 100):
    r = subprocess.run(['curl', '-sS', '--max-time', '60', '-X', 'POST', 'https://api.postcodes.io/postcodes', '-H', 'Content-Type: application/json', '-d', json.dumps({'postcodes': pl[i:i + 100]})], capture_output=True, text=True).stdout
    for q in json.loads(r)['result']:
        if q['result']: geo[q['query']] = (q['result']['latitude'], q['result']['longitude'], q['result']['postcode'])
def reg(d):
    d = d.lower().split(':')[0]; d = d[4:] if d.startswith('www.') else d; p = d.split('.')
    return '.'.join(p[-3:]) if len(p) > 2 and p[-2] in ('co', 'org', 'ac') else '.'.join(p[-2:])
cur = json.load(open('/home/user/Test123/corporates/london_300_rows.json'))['rows']
cur_dom = {reg(urllib.parse.urlparse(r['web']).netloc) for r in cur if r.get('web')}
sent = json.load(open('w2/sent_hits.json')); sup = {e.split('@')[-1] for e in json.load(open('w2/suppress_senders.json'))}
extra_sent = set(json.load(open('w5/sent_hits.json'))) if __import__('os').path.exists('w5/sent_hits.json') else set()
BIG = re.compile(r'microsoft|salesforce|google|amazon|meta\.|facebook|apple|ibm|oracle|accenture|deloitte|pwc|kpmg|ey\.com|atos|aecom|citi|hsbc|barclays|revolut|aig\.|willis|guidewire|flywheel|mongodb|statestreet|yahoo|zopa|monzo|wise\.com|currenciesdirect|expereo|quadient|currencycloud|ziffdavis|waterman|niit|multiverse|workday|atlassian|figma|pinterest|twilio|adecco|kyndryl|teradata|jetbrains|clarivate|mimecast|zoominfo|thoughtspot|yougov|valtech|zayo|cowi|wsp|jll|cbre|knightfrank|savills|arup|mace|bbc|itv|sky\.', re.I)
BAN = re.compile(r'^(orders?|shop|store|sales|press|media|pr|privacy|data|dpo|gdpr|compliance|careers?|recruit\w*|jobs|talent|support|help|customer\w*|ir|investor\w*|alumni|complaints?|legal|accounts?|billing|noreply|no-reply|marketing|news|nl|de|fr|es|it|us|nyc|paris|cvs?|partners|scilife)\b', re.I)
out = []; st = collections.Counter()
for num, o in O.items():
    x = U[num]; a = A.get(num)
    if not a: st['not extracted'] += 1; continue
    if not a.get('site_matches_company'): st['website is a different company'] += 1; continue
    ex = (a.get('exclude_reason') or '')
    if ex and not re.search(r'recruit|employment|staffing|nursing agenc', ex, re.I): st['excluded type'] += 1; continue
    web = o['website']; dom = reg(urllib.parse.urlparse(web).netloc)
    if dom in cur_dom: st['already on current list'] += 1; continue
    if BIG.search(dom) or BIG.search(x['name']): st['large multinational'] += 1; continue
    if dom in sent or dom in sup or dom in extra_sent: st['already contacted / suppressed'] += 1; continue
    p = (a.get('office_postcode') or '').upper().strip()
    g = geo.get(p) if PCRE.match(p) else None
    basis = 'Website' if g else o.get('office_basis', 'Website')
    g = g or geo.get(o['office_pc'])
    if not g: st['no geocode'] += 1; continue
    best = min((WALK(hav(g[0], g[1], v['lat'], v['lon'])), v['name'], v['slug']) for v in V)
    if best[0] > 15: st['office >15 min from a venue'] += 1; continue
    hc = a.get('headcount'); hc = int(hc) if str(hc).isdigit() else None
    if hc is not None and hc < 20: st['headcount under 20'] += 1; continue
    if hc is not None and hc > 500: st['headcount over 500'] += 1; continue
    pe = (a.get('contact_email') or '').lower().strip(); ge = (a.get('general_email') or '').lower().strip()
    ok = lambda e: e and '@' in e and reg(e.split('@')[1]) == dom and not BAN.match(e.split('@')[0])
    fn = (a.get('contact_first_name') or '').strip(); title = (a.get('contact_title') or '').strip()
    if ok(pe): email, tier = pe, 'a/b named person'
    elif ok(ge): email, tier = ge, ('a/b named person via general inbox' if fn else 'c general inbox')
    else:
        try: scraped = json.load(open(f'w2/pages/{num}.json')).get('emails', {})
        except Exception: scraped = {}
        GENR = re.compile(r'^(info|hello|office|london|enquiries|enquiry|contact|reception|studio|mail|general|team|ask)@', re.I)
        cands = sorted([e for e in scraped if ok(e.lower()) and GENR.match(e.lower())], key=len)
        if cands: email, tier = cands[0].lower(), ('a/b named person via general inbox' if fn else 'c general inbox'); st['email from site scrape'] += 1
        else: st['no usable email on own domain'] += 1; continue
    out.append({'num': num, 'x': x, 'a': a, 'web': web, 'dom': dom, 'email': email, 'tier': tier, 'fn': fn, 'title': title,
                'office_pc': g[2], 'office_basis': basis, 'office_street': a.get('office_street') or '', 'venue': best[1], 'slug': best[2], 'walk': round(best[0], 1), 'hc': hc})
def mx(dom):
    try:
        j = json.loads(subprocess.run(['curl', '-sS', '-m', '10', f'https://dns.google/resolve?name={dom}&type=MX'], capture_output=True, text=True).stdout)
        return bool([z for z in j.get('Answer', []) if z.get('type') == 15])
    except Exception: return False
with cf.ThreadPoolExecutor(16) as ex: mxs = list(ex.map(mx, [r['dom'] for r in out]))
final = [r for r, m in zip(out, mxs) if m]; st['no MX'] = len(out) - len(final)
# one row per domain
seen = set(); fin2 = []
for r in final:
    if r['dom'] in seen: st['duplicate domain'] += 1; continue
    seen.add(r['dom']); fin2.append(r)
st['KEPT'] = len(fin2)
json.dump(fin2, open('w5/new_rows.json', 'w'), default=str)
json.dump(sorted({r['dom'] for r in fin2}), open('w5/new_domains.json', 'w'))
print(dict(st)); print(collections.Counter(r['venue'] for r in fin2).most_common(15))
