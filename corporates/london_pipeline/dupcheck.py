import csv, re, openpyxl
SUF = set('LIMITED LTD LLP PLC UK U K THE AND & CO COMPANY GROUP INTERNATIONAL HOLDINGS SERVICES GLOBAL LONDON EMEA EUROPE PUBLIC INC LLC SA AG NV'.split())
FIN = re.compile(r'bank|financ|invest|capital|asset|fund|insur|underwrit|broker|law|legal|solicit|attorney|wealth|trust|reinsur|lloyd|equity|securit|account', re.I)
def core(n):
    t = re.sub(r"[^A-Z0-9 ]", " ", str(n).upper().replace('&', ' ').replace("'", '')).split()
    t = [x for x in t if x not in SUF]
    return tuple(t)
L = '/home/user/Test123/linkedin/'
used = []   # (core, label, finance_context)
wb = openpyxl.load_workbook('/root/.claude/uploads/1a31dd2e-3db0-5067-ac37-58491793a12d/c365f032-fcurban_all_businesses_merged.xlsx', read_only=True)
it = wb['London'].iter_rows(values_only=True); h = list(next(it))
for r in it:
    if r[0]: used.append((core(r[0]), f'FC Urban London sheet: {r[0]}', bool(FIN.search(f"{r[5] or ''} {r[0]} {r[4] or ''}"))))
for f, col, lab in [('city_of_london_finance_companies_house.csv','Company name','City finance research list (933)'),
                    ('city_of_london_finance_linkedin_list.csv','Business','City finance LinkedIn list (117)'),
                    ('city_of_london_finance_top100.csv','Company name','City finance top 100 (Joep)'),
                    ('haggerston_park_nearby_leads.csv','Business','Haggerston Park pilot leads')]:
    for r in csv.DictReader(open(L+f)):
        fin = True if 'haggerston' not in f else bool(FIN.search(f"{r.get('Industry','')} {r[col]}"))
        used.append((core(r[col]), f'{lab}: {r[col]}', fin))
GENERIC = set('LONDON CITY GLOBAL INTERNATIONAL CAPITAL FIRST NEW UK BRITISH EUROPEAN ROYAL NATIONAL STANDARD GENERAL UNITED AMERICAN ASIAN BANK THE ST PRIVATE ASSET INVESTMENT INVESTMENTS FINANCIAL WEALTH LEGAL LAW ATLANTIC PACIFIC NORTHERN SOUTHERN EASTERN WESTERN NORTH SOUTH EAST WEST GREEN BLUE RED BLACK WHITE GOLD SILVER CROWN EMPIRE ALPHA BETA OMEGA DELTA APEX PRIME ONE TWO THREE EURO ARAB AFRICAN INDIAN CHINA JAPAN EUROPE WORLD TRUST INSURANCE RE MARINE CORPORATE COMMERCIAL PARTNERS MANAGEMENT ADVISORS ADVISERS SMART CHARLES JOHN JAMES WILLIAM THOMAS GEORGE DAVID PETER MICHAEL RICHARD ROBERT HENRY EDWARD SAINT MOUNT KING LORD SIR DR MR'.split())
def brand(name):
    t = [x for x in re.sub(r'[^A-Z0-9& ]', ' ', str(name).upper()).split() if x != 'THE']
    if not t: return ''
    return ' '.join(t[:2]) if (t[0] in GENERIC or len(t[0]) <= 2) else t[0]
idx = {}; bidx = {}
for c, lab, fin in used:
    if c: idx.setdefault(c[0], []).append((c, lab, fin))
for (c, lab, fin), raw in zip(used, [u[1].split(': ', 1)[1] for u in used]):
    if fin and 'London sheet' not in lab: bidx.setdefault(brand(raw), []).append(lab)
def _match(name, want_soft):
    b = core(name)
    if not b: return None
    for a, lab, fin in idx.get(b[0], []):
        if ('research list (933)' in lab) != want_soft: continue
        k = min(len(a), len(b))
        if a[:k] == b[:k] and (k >= 2 or (fin and len(a[0]) >= 4)):
            return lab
    for lab in bidx.get(brand(name), []):
        if ('research list (933)' in lab) == want_soft: return lab
    return None
def dup(name): return _match(name, False)          # already in an outreach list -> exclude
def seen_research(name): return _match(name, True)  # only in the unmessaged 933 research list -> keep, flag

