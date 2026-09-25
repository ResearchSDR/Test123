import json, re, sys, html, urllib.parse, concurrent.futures as cf, os
sys.path.insert(0, '.')
import findemail as F
from select400 import nice, short
U = json.load(open('w2/uniq.json'))
PC = re.compile(r'\b((?:EC|WC)[1-4][A-Z]? ?\d[A-Z]{2}|(?:E|N|NW|SE|SW|W)\d{1,2}[A-Z]? ?\d[A-Z]{2})\b')
KEEP = re.compile(r'contact|about|team|people|our-people|leadership|who-we-are|office|location|london|find-us|studio|culture|careers|news|life-at|join', re.I)
def text(b):
    b = re.sub(r'(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>', ' ', b)
    b = re.sub(r'(?i)<br\s*/?>|</(p|div|li|h\d|tr)>', '\n', b)
    t = html.unescape(re.sub(r'<[^>]+>', ' ', b))
    return re.sub(r'[ \t\r\f\v]+', ' ', re.sub(r'\n\s*\n+', '\n', t)).strip()
def work(x):
    fn = f"w2/pages/{x['num']}.json"
    if os.path.exists(fn): return json.load(open(fn))
    r = {'Company name': nice(x['name']), 'Name for messages': short(x['name'])}
    res = {'num': x['num'], 'website': '', 'pages': [], 'emails': {}, 'postcodes': {}}
    site = None
    for d in F.cands(r):
        code, eff, body = F.get('https://www.' + d)
        if code == 200 and F.valid(r, body, d): site = (eff, body); break
    if site:
        eff, body = site; host = urllib.parse.urlparse(eff).netloc; dom = F.root(host)
        res['website'] = f'https://{host}'
        links = [urllib.parse.urljoin(eff, l) for l in re.findall(r'href="([^"#?]+)"', body)]
        links = [l for l in dict.fromkeys(links) if F.root(urllib.parse.urlparse(l).netloc) == dom and KEEP.search(urllib.parse.urlparse(l).path)]
        links.sort(key=lambda l: (0 if re.search('contact|office|location|find-us', l, re.I) else 1 if re.search('team|people|leadership|about|who-we', l, re.I) else 2, len(l)))
        pages = [(eff, body)]
        for l in (links[:8] + [res['website'] + p for p in ('/contact', '/contact-us', '/about', '/team')])[:11]:
            if any(l.rstrip('/') == p[0].rstrip('/') for p in pages): continue
            c, e2, b = F.get(l, 10)
            if c == 200 and b: pages.append((e2, b))
        for u, b in pages:
            t = text(b)
            res['pages'].append({'url': u, 'text': t[:12000]})
            for e in F.emails(b):
                d2 = e.split('@')[1]
                if d2 == dom or d2.endswith('.' + dom): res['emails'].setdefault(e, u)
            for p in PC.findall(t.upper()): res['postcodes'].setdefault(p.replace(' ', ''), u)
    json.dump(res, open(fn, 'w'))
    return res
with cf.ThreadPoolExecutor(32) as ex: out = list(ex.map(work, U))
print('sites', sum(bool(o['website']) for o in out), 'with emails', sum(bool(o['emails']) for o in out), 'with postcodes', sum(bool(o['postcodes']) for o in out))
