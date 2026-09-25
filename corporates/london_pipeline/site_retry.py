import json, glob, os, re, sys, concurrent.futures as cf
sys.path.insert(0, '.'); sys.argv = ['x']
import findemail as F
_orig = F.cands
def cands2(r):
    base = _orig(r)
    t = [x for x in F.toks(re.sub(r'\(.*?\)', '', r['Name for messages'])) if x]
    core = [x for x in t if x not in F.STOP] or t
    extra = []
    for b in [''.join(core), ''.join(t[:2]), core[0] if core else '', '-'.join(core[:2]), ''.join(core) + 'group', ''.join(core) + 'london', ''.join(core) + 'uk', 'the' + ''.join(core)]:
        if len(b) >= 3:
            for tld in ('.io', '.ai', '.co', '.agency', '.studio', '.london', '.uk', '.tech', '.law', '.net', '.com', '.co.uk'):
                extra.append(b + tld)
    return list(dict.fromkeys(base + extra))[:40]
F.cands = cands2
import importlib.util
spec = importlib.util.spec_from_file_location('sf', 'w2/site_fetch.py')
src = open('w2/site_fetch.py').read().replace('with cf.ThreadPoolExecutor(32) as ex: out = list(ex.map(work, U))', '')
src = src.replace('from select400 import nice, short', 'nice = lambda n: n.title(); short = None')
src = src.split("print('sites'")[0]
ns = {}
exec(src, ns)
# reuse nice/short from the corporates selection without re-running it
exec(open('select400.py').read().split('def nice(n):')[0].split('# ---- venues')[0], {})
sel = open('select400.py').read(); a = sel.index('def nice(n):'); b = sel.index('import emailpick')
exec(sel[a:b], ns)
todo = []
for f in glob.glob('w2/pages/*.json'):
    s = json.load(open(f))
    if not s['website']: os.remove(f); todo.append(s['num'])
U = [x for x in ns['U'] if x['num'] in set(todo)]
print('retrying', len(U))
with cf.ThreadPoolExecutor(48) as ex: out = list(ex.map(ns['work'], U))
print('new sites', sum(bool(o['website']) for o in out), 'with postcodes', sum(bool(o['postcodes']) for o in out))
