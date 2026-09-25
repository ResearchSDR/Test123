import json, glob, re, math, subprocess, csv, collections, html, datetime, urllib.parse, concurrent.futures as cf
U = {x['num']: x for x in json.load(open('w2/uniq.json'))}
O = {o['num']: o for o in json.load(open('w2/office.json'))}
A = {}
for f in sorted(glob.glob('w2/agent_out/*.json')):
    for x in json.load(open(f)): A[str(x.get('num'))] = x
V = {html.unescape(v['name']): v for v in json.load(open('london_venues.json'))}
# ---- slots: Available, Mon-Thu, kick-off 17:30-20:00, next 3 weeks ----
TODAY = datetime.date(2026, 9, 25); END = TODAY + datetime.timedelta(days=21)
rows = list(csv.DictReader(open('/home/user/Test123/linkedin/venue_slots/raw_slots.csv', encoding='utf-8')))
for f in glob.glob('slots_agent*.csv'): rows += list(csv.DictReader(open(f, encoding='utf-8')))
SL = collections.defaultdict(list)
for r in rows:
    if r['status'] != 'Available' or not r['date']: continue
    d = datetime.date.fromisoformat(r['date'])
    if TODAY <= d <= END and d.weekday() <= 3 and '17:30' <= r['start'] <= '20:00': SL[r['venue']].append((d, r['start'], r['end'], r['pitch_format'], r['booking_source'], r['hire_price_gbp']))
DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday']
def slot_offer(v):
    s = sorted(SL[v]); pat = collections.defaultdict(list)
    for d, st, en, fm, src, pr in s: pat[(d.weekday(), st)].append(d)
    rec = sorted(((-len(ds), min(ds), k) for k, ds in pat.items()))
    n, _, (wd, st) = rec[0]; n = -n; ds = sorted(pat[(wd, st)]); fm = next(x[3] for x in s if x[0].weekday() == wd and x[1] == st)
    src = next(x[4] for x in s if x[0].weekday() == wd and x[1] == st)
    if n >= 2: txt = f"every {DAYS[wd]} at {st} ({', '.join(d.strftime('%-d %b') for d in ds)})"; kind = 'Recurring'
    else: txt = f"{ds[0].strftime('%A %-d %B')} at {st}"; kind = 'One-off'
    return {'pitch': v, 'slot_text': txt, 'slot_kind': kind, 'format': fm, 'first_date': ds[0].isoformat(), 'time': st, 'source': src, 'open_slots': len(s)}
PITCHES = [v for v in SL]
OFFER = {v: slot_offer(v) for v in PITCHES}
def hav(a, b, c, d):
    R = 6371000; p1, p2 = math.radians(a), math.radians(c); dl = math.radians(d - b); dp = p2 - p1
    return 2 * R * math.asin(math.sqrt(math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2))
WALK = lambda m: m * 1.3 / 80.0
PCRE = re.compile(r'^((?:EC|WC)[1-4][A-Z]?|(?:E|N|NW|SE|SW|W)\d{1,2}[A-Z]?) ?(\d[A-Z]{2})$')
pcs = set()
for n, a in A.items():
    p = (a.get('office_postcode') or '').upper().strip()
    if PCRE.match(p): pcs.add(p)
for o in O.values(): pcs.add(o['office_pc'])
geo = {}
pl = sorted(pcs)
for i in range(0, len(pl), 100):
    r = subprocess.run(['curl', '-sS', '--max-time', '60', '-X', 'POST', 'https://api.postcodes.io/postcodes', '-H', 'Content-Type: application/json', '-d', json.dumps({'postcodes': pl[i:i + 100]})], capture_output=True, text=True).stdout
    for q in json.loads(r)['result']:
        if q['result']: geo[q['query']] = (q['result']['latitude'], q['result']['longitude'], q['result']['postcode'])
# ---- suppression ----
sent = json.load(open('w2/sent_hits.json'))
sup = {e.split('@')[-1] for e in json.load(open('w2/suppress_senders.json'))}
BIG = re.compile(r'chillys|nscgroup|microsoft|salesforce|pinterest|atlassian|figma|workday|twilio|maersk|adecco|kyndryl|teradata|jetbrains|clarivate|oceaneering|getronics|coforge|mimecast|zoominfo|symphony|bullhorn|similarweb|thoughtspot|toluna|yougov|valtech|colt\.net|zayo|econocom|cowi|nbbj|costain|monotype|ex-libris|pluralsight|dataiku|druva|avepoint|a10networks|brillio|griddynamics|office-angels|modis|penna|wsp', re.I)
BAN = re.compile(r'^(orders?|shop|store|sales|enquiries-sales|press|media|pr|privacy|data|dpo|gdpr|compliance|careers?|recruit\w*|jobs|talent|support|help|customer\w*|ir|investor\w*|alumni|complaints?|legal|accounts?|billing|noreply|no-reply|marketing|news)\b', re.I)
def reg(d):
    d = d.lower().split(':')[0]; d = d[4:] if d.startswith('www.') else d; p = d.split('.')
    return '.'.join(p[-3:]) if len(p) > 2 and p[-2] in ('co', 'org', 'ac') else '.'.join(p[-2:])
def mx(dom):
    try:
        j = json.loads(subprocess.run(['curl', '-sS', '-m', '10', f'https://dns.google/resolve?name={dom}&type=MX'], capture_output=True, text=True).stdout)
        return bool([a for a in j.get('Answer', []) if a.get('type') == 15])
    except Exception: return False
out = []; st = collections.Counter()
for num, o in O.items():
    x = U[num]; a = A.get(num)
    if not a: st['not extracted yet'] += 1; continue
    if not a.get('site_matches_company'): st['website is a different company'] += 1; continue
    if a.get('exclude_reason'): st['excluded type: ' + a['exclude_reason'][:30]] += 1; continue
    web = o['website']; dom = reg(urllib.parse.urlparse(web).netloc)
    if BIG.search(dom): st['large multinational (>500 staff)'] += 1; continue
    if dom in sent or dom in sup: st['already contacted / suppressed'] += 1; continue
    p = (a.get('office_postcode') or '').upper().strip()
    if PCRE.match(p) and p in geo:
        g = geo[p]; basis = 'Website' + (f" ({a.get('office_street')})" if a.get('office_street') else '')
    else:
        g = geo.get(o['office_pc']); basis = o.get('office_basis', 'Website')
        if not g: st['office postcode not geocoded'] += 1; continue
    best = min((WALK(hav(g[0], g[1], V[v]['lat'], V[v]['lon'])), v) for v in PITCHES)
    if best[0] > 15: st['office >15 min from a slot pitch'] += 1; continue
    hc = a.get('headcount'); hc = int(hc) if str(hc).isdigit() else None
    if hc is not None and hc < 20: st['headcount under 20'] += 1; continue
    if hc is not None and hc > 500: st['headcount over 500'] += 1; continue
    # contact
    pe = (a.get('contact_email') or '').lower().strip(); ge = (a.get('general_email') or '').lower().strip()
    def ok(e): return e and '@' in e and reg(e.split('@')[1]) == dom and not BAN.match(e.split('@')[0])
    fn = (a.get('contact_first_name') or '').strip(); title = (a.get('contact_title') or '').strip()
    if ok(pe): email, tier, src = pe, 'a/b named person', a.get('contact_source_url')
    elif ok(ge): email, tier, src = ge, ('a/b named person via general inbox' if fn else 'c general inbox'), a.get('general_email_source_url') or a.get('contact_source_url')
    else: st['no usable email on own domain'] += 1; continue
    out.append({'num': num, 'x': x, 'a': a, 'web': web, 'dom': dom, 'email': email, 'tier': tier, 'email_src': src or '', 'fn': fn, 'title': title,
                'office_pc': g[2], 'office_basis': basis, 'office_street': a.get('office_street') or '', 'pitch': best[1], 'walk': round(best[0], 1), 'hc': hc})
with cf.ThreadPoolExecutor(16) as ex: mxs = list(ex.map(mx, [r['dom'] for r in out]))
final = []
for r, m in zip(out, mxs):
    if not m: st['email domain has no MX record'] += 1; continue
    final.append(r)
st['KEPT'] = len(final)
json.dump({'rows': final, 'offer': OFFER}, open('w2/final.json', 'w'), default=str)
print(dict(st)); print(collections.Counter(r['tier'] for r in final)); print(collections.Counter(r['pitch'] for r in final))
print(json.dumps(OFFER, indent=0)[:1500])

# ---- rows for the workbook ----
sel = open('select400.py').read(); a_ = sel.index('def nice(n):'); b_ = sel.index('import emailpick')
ns = {'re': re}; exec(sel[a_:b_], ns); nice, short = ns['nice'], ns['short']
def segment(x):
    s = x['sector']; n = x['name'].upper()
    if s != 'LLP (by name)': return s
    if re.search(r'SOLICITOR|LAW|LEGAL|& CO LLP|LLP$', n) and re.search(r'SOLICITOR|LAW|LEGAL', n): return 'Law'
    if re.search(r'ARCHITECT|DESIGN|STUDIO', n): return 'Architecture'
    if re.search(r'ACCOUNT|AUDIT|TAX|ADVIS', n): return 'Finance / accounting'
    if re.search(r'CAPITAL|INVEST|PARTNERS|ASSET|WEALTH', n): return 'Finance / accounting'
    return 'Professional services (LLP)'
TRIV = re.compile(r'^(was )?(founded|established|incorporated|registered)\b', re.I)
CONCRETE = re.compile(r'\b(street|road|square|lane|yard|place|row|court|house|building|moved|move|relocat|new (office|home|studio|hq)|\d+\s*(people|staff|employees|strong|colleagues|person)|team of \d+|award|won|winner|charity|marathon|run\b|football|five-a-side|5-a-side|sports|hiring|opening|expan|acquir|b corp|certified)', re.I)
def clean(t, maxlen):
    t = re.sub(r'\s+', ' ', t or '').strip()
    return '' if len(t) > maxlen or re.search(r'\b(days|cookie|javascript)\b', t, re.I) else t
W = []
for r in final:
    x, a = r['x'], r['a']
    pers = clean(a.get('personal_line'), 110).rstrip('.')
    if TRIV.match(pers) or not CONCRETE.search(pers): pers = ''
    if pers and pers[0].isupper() and not pers.split()[0].isupper(): pers = pers[0].lower() + pers[1:]
    W.append({'num': x['num'], 'company': nice(x['name']), 'short': short(x['name']), 'segment': segment(x), 'area': r['office_pc'].split()[0],
              'priority': 1 if r['tier'].startswith('a/b named person') and not 'via' in r['tier'] else 2 if 'via' in r['tier'] else 3,
              'web': r['web'], 'hc': r['hc'], 'acc': x['acc'], 'inc': x['inc'], 'reg_addr': x['addr'].title(), 'reg_pc': x['pc'],
              'fn': clean(r['fn'], 20) if clean(r['title'], 60) or not r['title'] else '', 'full': clean(' '.join(p for p in [a.get('contact_first_name'), a.get('contact_last_name')] if p), 40) if clean(r['title'], 60) or not r['title'] else '', 'title': clean(r['title'], 60),
              'email': r['email'], 'tier': r['tier'], 'email_src': r['email_src'], 'office_street': '' if re.search(r'manchester|leeds|birmingham|bristol|edinburgh|glasgow', r['office_street'], re.I) else clean(r['office_street'], 70), 'office_pc': r['office_pc'],
              'office_basis': r['office_basis'], 'pitch': r['pitch'], 'walk': r['walk'], 'personal': pers, 'personal_src': (a.get('personal_line_source_url') or '') if pers else ''})
W.sort(key=lambda w: (w['priority'], w['walk']))
json.dump({'rows': W, 'offer': {p: OFFER[p] for p in {w['pitch'] for w in W}}}, open('/home/user/Test123/corporates/london_300_rows.json', 'w'), indent=1)
print('rows written', len(W), collections.Counter(w['segment'] for w in W), 'personal lines', sum(bool(w['personal']) for w in W))
