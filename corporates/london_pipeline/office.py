import json, math, subprocess, collections, html, glob, re
U = {x['num']: x for x in json.load(open('w2/uniq.json'))}
V = {html.unescape(v['name']): v for v in json.load(open('london_venues.json'))}
PITCHES = ['Stepney 3G', 'COLA Shoreditch Park', 'Shoreditch Powerleague', 'Old St - Moreland Primary School', 'Market Road', 'Shoreditch Rooftop']
P = [(n, V[n]['lat'], V[n]['lon']) for n in PITCHES]
def hav(a, b, c, d):
    R = 6371000; p1, p2 = math.radians(a), math.radians(c); dl = math.radians(d - b); dp = p2 - p1
    return 2 * R * math.asin(math.sqrt(math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2))
WALK = lambda m: m * 1.3 / 80.0
S = {}
for f in glob.glob('w2/pages/*.json'):
    s = json.load(open(f)); S[s['num']] = s
pcs = sorted({p for s in S.values() for p in s['postcodes']})
geo = {}
for i in range(0, len(pcs), 100):
    r = subprocess.run(['curl', '-sS', '--max-time', '60', '-X', 'POST', 'https://api.postcodes.io/postcodes', '-H', 'Content-Type: application/json',
                        '-d', json.dumps({'postcodes': pcs[i:i + 100]})], capture_output=True, text=True).stdout
    for q in json.loads(r)['result']:
        if q['result']: geo[q['query']] = (q['result']['latitude'], q['result']['longitude'], q['result']['postcode'], q['result'].get('admin_district') or '')
out = []; st = collections.Counter()
for num, s in S.items():
    x = U.get(num)
    if not x: continue
    if not s['website']: st['no website found'] += 1; continue
    # London offices named on the firm's own pages; prefer ones found on a contact/office page
    offs = []
    for p, u in s['postcodes'].items():
        g = geo.get(p)
        if not g: continue
        best = min((WALK(hav(g[0], g[1], la, lo)), n) for n, la, lo in P)
        pri = 0 if re.search('contact|office|location|find-us|london', u, re.I) else 1
        offs.append((pri, best[0], g[2], best[1], u, g[3]))
    if not offs:
        best = min((WALK(hav(x['lat'], x['lon'], la, lo)), n) for n, la, lo in P)
        if best[0] > 15: st['no address on site, registered >15 min'] += 1; continue
        st['kept (registered office, no address on site)'] += 1
        out.append(dict(num=num, website=s['website'], office_pc=x['pc'], office_src='', office_basis='Registered office (no address on website)',
                        pitch=best[1], walk=round(best[0], 1), reg_pc=x['pc'], office_differs=False, n_emails=len(s['emails'])))
        continue
    offs.sort(); pri0 = offs[0][0]
    cand = [o for o in offs if o[0] == pri0]
    o = min(cand, key=lambda o: o[1])
    if o[1] > 15: st['office >15 min from a slot pitch'] += 1; continue
    st['kept'] += 1
    out.append(dict(num=num, website=s['website'], office_pc=o[2], office_src=o[4], office_basis='Website contact page' if o[0] == 0 else 'Website (other page)', pitch=o[3], walk=round(o[1], 1),
                    reg_pc=x['pc'], office_differs=o[2].replace(' ', '') != x['pc'].replace(' ', ''), n_emails=len(s['emails'])))
json.dump(out, open('w2/office.json', 'w'))
print(dict(st)); print(collections.Counter(o['pitch'] for o in out)); print('office differs from registered:', sum(o['office_differs'] for o in out))
