import json, re, csv, collections, sys
sys.path.insert(0, '.')
import dupcheck
# earlier lead sheets: add the 400 corporates list to the duplicate index
for r in csv.DictReader(open('/home/user/Test123/corporates/city_canary_wharf_corporates_400.csv', encoding='utf-8')):
    c = dupcheck.core(r['Company name']); lab = f"City corporates 400: {r['Company name']}"
    dupcheck.idx.setdefault(c[0], []).append((c, lab, True)) if c else None
    dupcheck.bidx.setdefault(dupcheck.brand(r['Company name']), []).append(lab)
near = json.load(open('w2/near.json'))
BADSIC = re.compile(r'\b(6420[1-9]|6430[1-6]|64999|66300|68\d{3}|70100|64921|64922|64929|64910|66190)\b')  # holding cos, fund vehicles, fund mgmt SPVs, property, head offices, lenders
drop = collections.Counter(); keep = []
for x in near:
    codes = set(re.findall(r'\b\d{5}\b', x['sic']))
    if codes and all(BADSIC.match(c) for c in codes): drop['holding / fund / property SIC only'] += 1; continue
    d = dupcheck.dup(x['name']) or dupcheck.seen_research(x['name'])
    if d: drop['already in an earlier lead sheet'] += 1; continue
    keep.append(x)
by = collections.defaultdict(list)
for x in keep: by[dupcheck.brand(x['name'])].append(x)
ACC = {'GROUP': 0, 'MEDIUM': 1, 'FULL': 2}
uniq = []
for b, xs in by.items():
    xs.sort(key=lambda x: (ACC[x['acc']], '(' in x['name'], x['inc'][-4:] if x['inc'] else '9999'))
    y = dict(xs[0]); y['group_entities'] = len(xs); uniq.append(y); drop['collapsed into same group'] += len(xs) - 1
json.dump(uniq, open('w2/uniq.json', 'w'))
print(dict(drop)); print('unique', len(uniq), collections.Counter(x['sector'] for x in uniq))
