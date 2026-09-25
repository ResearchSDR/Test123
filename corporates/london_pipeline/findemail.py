import csv, re, json, sys, subprocess, concurrent.futures as cf, html, urllib.parse
SP='/tmp/claude-0/-home-user-Test123/1a31dd2e-3db0-5067-ac37-58491793a12d/scratchpad'
import os
rows=list(csv.DictReader(open(os.environ.get('CSV','/home/user/Test123/corporates/city_canary_wharf_corporates_400.csv'),encoding='utf-8')))
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36'
def get(u, t=12):
    try:
        r=subprocess.run(['curl','-sSL','-m',str(t),'-A',UA,'--max-filesize','3000000','-w','\n@@%{http_code} %{url_effective}',u],capture_output=True,timeout=t+5)
        out=r.stdout.decode('utf-8','ignore'); body,_,meta=out.rpartition('\n@@')
        code,_,eff=meta.partition(' ')
        return int(code or 0), eff.strip(), body
    except Exception: return 0,'',''
STOP={'limited','ltd','llp','plc','uk','the','and','of','co','company','group','international','holdings','holding','services','europe','global','london','management','asset','investment','investments','partners','capital','bank','insurance','underwriting','solicitors','law','fund','funds','advisors','advisers','financial','securities','markets','limited','llc','emea','agency','managing','brokers','broking','corporation','reinsurance','wealth','trust','specialty'}
def toks(n): return [t for t in re.sub(r'[^a-z0-9 ]',' ',n.lower().replace('&',' and ').replace("'",'')).split() if t]
def cands(r):
    out=[]
    for n in (r['Name for messages'], r['Company name']):
        t=toks(re.sub(r'\(.*?\)','',n)); core=[x for x in t if x not in STOP] or t
        for base in [''.join(core),''.join(t[:3]),''.join(core[:2]),'-'.join(core[:2]),''.join(t[:2]),core[0] if core else '',''.join(x[0] for x in core) if len(core)>=3 else '']:
            if False: pass
        for base in [''.join(core),''.join(t[:3]),''.join(core[:2]),'-'.join(core[:2]),''.join(t[:2]),core[0] if core else '',''.join(x[0] for x in core) if len(core)>=3 else '']:
            if len(base)>=3:
                for tld in ('.com','.co.uk'): out.append(base+tld)
    seen=[]; [seen.append(x) for x in out if x not in seen]; return seen[:16]
BAD=re.compile(r'domain (is )?for sale|buy this domain|parked|godaddy|sedo|hugedomains|this domain|coming soon|account suspended|dan\.com',re.I)
def title(b):
    m=re.search(r'<title[^>]*>(.*?)</title>',b,re.S|re.I); return html.unescape(m.group(1).strip()) if m else ''
def valid(r, body, dom):
    key=([x for x in toks(re.sub(r'\(.*?\)','',r['Name for messages'])) if x not in STOP and len(x)>=3] or toks(r['Name for messages']))[:3]
    ti=title(body).lower()
    m=re.search(r'<meta[^>]+(?:name|property)="(?:description|og:title|og:site_name)"[^>]+content="([^"]*)"',body,re.I)
    head=ti+' '+(m.group(1).lower() if m else '')+' '+re.sub(r'<[^>]+>',' ',body[:60000]).lower()
    if BAD.search(ti) or len(body)<1500: return False
    return all(k in head for k in key) and (key[0] in ti or key[0] in dom)
EM=re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
def cf_decode(s):
    k=int(s[:2],16); return ''.join(chr(int(s[i:i+2],16)^k) for i in range(2,len(s),2))
def emails(body):
    body=html.unescape(urllib.parse.unquote(body))
    e=set(EM.findall(body))
    for m in re.findall(r'data-cfemail="([0-9a-f]+)"',body): e.add(cf_decode(m))
    return {x.strip('.').lower() for x in e if not re.search(r'\.(png|jpe?g|gif|svg|webp|css|js)$|example\.|sentry|wixpress|@2x|domain\.com|email\.com|yourcompany|@sentry',x,re.I)}
GEN=re.compile(r'^(info|enquir|inquir|contact|london|hello|office|reception|general|mail|admin|uk|team|ask|help|clientservices|client|sales|business|newbusiness|marketing|communications|press|media)',re.I)
LOW=re.compile(r'^(privacy|dpo|data|gdpr|compliance|complaint|legal|careers|recruit|jobs|hr|talent|graduate|no-?reply|unsubscribe|abuse|webmaster|security|accessibility)',re.I)
def rank(e):
    lp=e.split('@')[0]
    return 0 if GEN.match(lp) else (2 if LOW.match(lp) else 1)
def root(d): 
    d=d.lower().split(':')[0]; d=d[4:] if d.startswith('www.') else d
    p=d.split('.'); return '.'.join(p[-3:]) if p[-2:-1]==['co'] or p[-2:-1]==['org'] and p[-1]=='uk' else '.'.join(p[-2:])
def work(r):
    res={'#':r['#'],'website':'','email':'','email_type':'','all_emails':'','source':''}
    site=None
    for d in cands(r):
        code,eff,body=get('https://www.'+d)
        if code==200 and valid(r,body,d): site=(eff,body); break
    if not site: return res
    eff,body=site; dom=root(urllib.parse.urlparse(eff).netloc); res['website']=f'https://{urllib.parse.urlparse(eff).netloc}'
    found={e:eff for e in emails(body)}
    links=re.findall(r'href="([^"#]+)"',body)
    cl=[urllib.parse.urljoin(eff,l) for l in links if re.search(r'contact|about|office|location|privacy|legal|imprint|get-in-touch',l,re.I)]
    cl=[l for l in cl if root(urllib.parse.urlparse(l).netloc)==dom]
    pages=list(dict.fromkeys(cl+[res['website']+p for p in ('/contact','/contact-us','/contact-us/','/privacy-policy')]))[:7]
    for p in pages:
        c,e2,b=get(p,10)
        if c==200:
            for e in emails(b): found.setdefault(e,p)
    b0=dom.split('.')[0]
    own={e:s for e,s in found.items() if (lambda d: d==dom or d.endswith('.'+dom) or d in (b0+'.com',b0+'.co.uk',b0+'.uk',b0+'.london'))(e.split('@')[1])}
    if own:
        best=sorted(own,key=lambda e:(rank(e),len(e)))[0]
        res.update(email=best,email_type=['general','personal','privacy / compliance'][rank(best)],all_emails='; '.join(sorted(own,key=lambda e:(rank(e),len(e)))[:6]),source=own[best])
    return res
if __name__=='__main__':
    sub=rows if len(sys.argv)<2 else rows[:int(sys.argv[1])]
    cache=json.load(open(f'{SP}/em/cache_by_name.json'))
    todo=[r for r in sub if r['Company name'] not in cache]
    print('cached',len(sub)-len(todo),'to fetch',len(todo))
    with cf.ThreadPoolExecutor(24) as ex:
        for r,res in zip(todo,ex.map(work,todo)): cache[r['Company name']]=res
    json.dump(cache,open(f'{SP}/em/cache_by_name.json','w'))
    out=[dict(cache[r['Company name']],**{'#':r['#']}) for r in sub]
    json.dump(out,open(f'{SP}/em/emails_pass1.json','w'),indent=0)
    import collections
    print('sites',sum(bool(x['website']) for x in out),'emails',sum(bool(x['email']) for x in out),collections.Counter(x['email_type'] for x in out))
