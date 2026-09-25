import zipfile, csv, io, re, json, collections, html
z = zipfile.ZipFile('ch.zip')
rd = csv.DictReader(io.TextIOWrapper(z.open(z.namelist()[0]), encoding='utf-8', errors='replace'))
rd.fieldnames = [f.strip() for f in rd.fieldnames]
LONDON = re.compile(r'^(EC[1-4][A-Z]?|WC[12][A-Z]?|E\d{1,2}W?|N\d{1,2}|NW\d{1,2}|SE\d{1,2}|SW\d{1,2}[A-Z]?|W\d{1,2}[A-Z]?)$')
SECT = [('Law', r'^6910[129]$'), ('Finance / accounting', r'^(64\d{3}|66\d{3}|6920[123])$'), ('Insurance', r'^65\d{3}$'),
        ('Consultancy', r'^(70210|70221|70229)$'), ('Tech / software', r'^(62011|62012|62020|62030|62090|63110|63120|58290|58210)$'),
        ('Architecture', r'^(71111|71112|71121|71122|71129)$'), ('Recruitment', r'^(78100|78109|78200|78300)$'),
        ('Marketing / agency', r'^(73110|73120|73200|74100|74201|59112|59113)$')]
SECT = [(s, re.compile(p)) for s, p in SECT]
REAL = {'FULL', 'GROUP', 'MEDIUM', 'LARGE'}
SICK = [f'SICCode.SicText_{i}' for i in range(1, 5)]
out = []; n = 0
for row in rd:
    n += 1
    if (row.get('CompanyStatus') or '').strip() != 'Active': continue
    pc = (row.get('RegAddress.PostCode') or '').strip().upper()
    if not pc or not LONDON.match(pc.split()[0]): continue
    cat = (row.get('Accounts.AccountCategory') or '').strip()
    if cat not in REAL: continue
    codes = [(row.get(k) or '').split(' - ')[0].strip() for k in SICK]
    sector = next((s for s, rx in SECT if any(rx.match(c) for c in codes if c)), None)
    ctype = (row.get('CompanyCategory') or '').strip()
    if not sector and 'Limited Liability Partnership' in ctype: sector = 'LLP (by name)'
    if not sector: continue
    out.append({'name': row['CompanyName'].strip(), 'num': row.get('CompanyNumber', '').strip(), 'type': ctype, 'acc': cat, 'sector': sector,
                'sic': ' | '.join((row.get(k) or '').strip() for k in SICK if (row.get(k) or '').strip()), 'pc': pc,
                'addr': ', '.join(x.strip() for x in [row.get('RegAddress.AddressLine1', ''), row.get('RegAddress.AddressLine2', ''), row.get('RegAddress.PostTown', '')] if x and x.strip()),
                'inc': (row.get('IncorporationDate') or '').strip()})
json.dump(out, open('w2/raw.json', 'w'))
print('scanned', n, 'candidates', len(out)); print(collections.Counter(o['sector'] for o in out)); print(collections.Counter(o['acc'] for o in out))
