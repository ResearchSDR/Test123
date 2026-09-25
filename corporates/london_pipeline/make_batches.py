import json, re, os, glob
U = {x['num']: x for x in json.load(open('w2/uniq.json'))}
O = json.load(open('w2/office.json'))
os.makedirs('w2/agent_in', exist_ok=True); os.makedirs('w2/agent_out', exist_ok=True)
for f in glob.glob('w2/agent_in/*'): os.remove(f)
ORDER = lambda u: 0 if re.search('contact|office|location|find-us', u, re.I) else 1 if re.search('team|people|leadership|about|who-we|culture', u, re.I) else 2 if re.search('news|careers|join|life', u, re.I) else 3
items = []
for o in O:
    x = U[o['num']]; s = json.load(open(f"w2/pages/{o['num']}.json"))
    pages = sorted(s['pages'], key=lambda p: ORDER(p['url']))
    budget, keep = 22000, []
    for p in pages:
        t = p['text'][:7000] if ORDER(p['url']) == 1 else p['text'][:4000]
        if budget <= 0: break
        keep.append({'url': p['url'], 'text': t[:budget]}); budget -= len(t)
    items.append({'num': o['num'], 'companies_house_name': x['name'], 'registered_address': f"{x['addr']} {x['pc']}", 'sic': x['sic'],
                  'website': s['website'], 'emails_seen_on_site': s['emails'], 'office_postcode_used': o['office_pc'], 'pages': keep})
B = 10
for i in range(0, len(items), B):
    json.dump(items[i:i + B], open(f'w2/agent_in/batch_{i // B + 1:02d}.json', 'w'))
print('companies', len(items), 'batches', (len(items) + B - 1) // B)
