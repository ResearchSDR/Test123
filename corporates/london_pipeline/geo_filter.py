import json, re, math, subprocess, collections, html
raw = json.load(open('w2/raw.json'))
V = {html.unescape(v['name']): v for v in json.load(open('london_venues.json'))}
PITCHES = ['Stepney 3G', 'COLA Shoreditch Park', 'Shoreditch Powerleague', 'Old St - Moreland Primary School', 'Market Road', 'Shoreditch Rooftop']
P = [(n, V[n]['lat'], V[n]['lon']) for n in PITCHES]
def hav(a, b, c, d):
    R = 6371000; p1, p2 = math.radians(a), math.radians(c); dl = math.radians(d - b); dp = p2 - p1
    return 2 * R * math.asin(math.sqrt(math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2))
SHELL = re.compile(r"\b(TOPCO|MIDCO|BIDCO|HOLDCO|HOLDINGS?|NOMINEES?|TRUSTEES?|TRUST CORPORATION|FUNDING|ISSUER|SPV|GP|CARRY|CO-?INVEST|FEEDER|FACILITY|VCT|INVESTMENT TRUST|INCOME TRUST|GROWTH TRUST|FUND\b|FUNDS\b|LP\b|L\.P\.|SECURITISATION|FINANCE (NO|PLC)|NO\.? ?\d+|\d{3,4}|PROPCO|OPCO|INTERMEDIATE|ACQUISITION|ACQUISITIONCO|FINCO|DEBTCO|MEZZ|NAMECO|CORPORATE MEMBER|DORMANT|PENSION|SCHEME|CHARIT|FOUNDATION|SCHOOL|NHS|COUNCIL|EMBASSY|RESTAURANT|HOTEL|DENTAL|CLINIC|NURSERY)\b")
out = []; drop = collections.Counter()
for x in raw:
    if SHELL.search(x['name'].upper()): drop['shell / excluded type'] += 1; continue
    out.append(x)
pcs = sorted({x['pc'] for x in out}); geo = {}
for i in range(0, len(pcs), 100):
    r = subprocess.run(['curl', '-sS', '--max-time', '60', '-X', 'POST', 'https://api.postcodes.io/postcodes', '-H', 'Content-Type: application/json',
                        '-d', json.dumps({'postcodes': pcs[i:i + 100]})], capture_output=True, text=True).stdout
    for q in json.loads(r)['result']:
        if q['result']: geo[q['query']] = (q['result']['latitude'], q['result']['longitude'])
keep = []
for x in out:
    g = geo.get(x['pc'])
    if not g: drop['postcode not found'] += 1; continue
    d = min((hav(g[0], g[1], la, lo), n) for n, la, lo in P)
    if d[0] > 2000: drop['registered >2 km from a slot pitch'] += 1; continue
    x['lat'], x['lon'] = g; x['reg_near'] = (round(d[0]), d[1]); keep.append(x)
addr = collections.defaultdict(set)
for x in keep: addr[(x['addr'].upper(), x['pc'])].add(x['name'].split()[0])
fin = []
for x in keep:
    if len(addr[(x['addr'].upper(), x['pc'])]) > 12: drop['formation-agent address'] += 1; continue
    fin.append(x)
json.dump(fin, open('w2/near.json', 'w'))
print(dict(drop)); print('kept', len(fin), collections.Counter(x['sector'] for x in fin))
