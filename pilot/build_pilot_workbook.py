import csv, re, datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.comments import Comment

BASE = '/home/user/Test123/linkedin'
import os
OUT  = os.environ.get('OUT','/home/user/Test123/pilot/FC_Urban_London_pilot_Haggerston_Park.xlsx')
leads    = list(csv.DictReader(open(f'{BASE}/haggerston_park_nearby_leads.csv', encoding='utf-8')))
slots    = list(csv.DictReader(open(f'{BASE}/venue_slots/raw_slots.csv', encoding='utf-8')))
contacts = {r['venue']: r for r in csv.DictReader(open(f'{BASE}/venue_slots/booking_contacts.csv', encoding='utf-8'))}

ADDR = {'Haggerston Park':'Yorkton St, E2 8NH','Whitechapel':'Mulberry Sports & Leisure Centre, Richard St, E1 2JP',
 'Shoreditch Rooftop':'Britannia Leisure Centre, Pitfield St, N1 5FT','Rosemary Gardens 3G - Islington':'Southgate Rd, N1 3JP',
 'Stepney 3G':'Globe Football Pitch, 110 Globe Rd, E1 4DZ','Old St - Moreland Primary School':'Gard St, EC1V 8DW',
 'Hackney':'The City Academy Hackney, Homerton High St, E9 6JQ','COLA Shoreditch Park':'Hyde Rd, N1 5JU','Market Road':'Market Rd, N7 9PL'}
VENUES = list(dict.fromkeys(r['venue'] for r in slots))
BOOKABLE = {'COLA Shoreditch Park','Old St - Moreland Primary School','Hackney','Shoreditch Rooftop','Market Road'}
DEFAULT_ALT = 'COLA Shoreditch Park'
MAXR = int(os.environ.get('MAXR','2000'))

# ---------- styles ----------
F  = 'Arial'
fnt   = Font(name=F, size=10)
bold  = Font(name=F, size=10, bold=True)
white = Font(name=F, size=10, bold=True, color='FFFFFF')
title = Font(name=F, size=14, bold=True)
blue  = Font(name=F, size=10, color='0000FF')
green = Font(name=F, size=10, color='008000')
link  = Font(name=F, size=10, color='1155CC', underline='single')
YEL   = PatternFill('solid', fgColor='FFF2CC')
HDR   = PatternFill('solid', fgColor='1F3864')
BANDS = {'Lead':'2F5496','Tagged venue':'548235','Fallback pitch':'7F6000','Lead with (message)':'C55A11','Tracking — fill in':'BF9000'}
thin  = Side(style='thin', color='D9D9D9'); box = Border(bottom=thin)
wrap  = Alignment(wrap_text=True, vertical='top'); top = Alignment(vertical='top')
DT, D, T = 'ddd d mmm yyyy hh:mm', 'ddd d mmm yyyy', 'hh:mm'

def hdr(ws, row, cols, fill=HDR):
    for i, h in enumerate(cols, 1):
        c = ws.cell(row=row, column=i, value=h); c.font = white; c.fill = fill
        c.alignment = Alignment(wrap_text=True, vertical='center')

def seg(ind):
    i = ind.lower()
    if i in ('coworking_space','coworking','office building (multi-tenant)','amenity: conference centre'): return 'Coworking / shared office'
    if i in ('finance','consultant','lawyer','company','service','estate_agent','corporate_office','advertising_agency',
             'insurance_agency','architect','ngo','it','charity','notary','agency','graphic_design','recruitment',
             'office: company','amenity: bank','manufacturer','rentable','shop: estate agent'): return 'Office & professional'
    if re.match(r'amenity: (restaurant|pub|cafe|bar|fast food|nightclub)|tourism: (hotel|hostel|guest house|apartment)', i): return 'Hospitality'
    if re.match(r'amenity: (school|college|student accommodation|training|library)', i): return 'Education'
    if re.match(r'amenity: (dentist|hospital|clinic|doctors|pharmacy)|shop: (chemist|optician)', i): return 'Health'
    if re.match(r'tourism: (gallery|museum)|amenity: (theatre|community centre|cinema|arts centre|events venue|studio|dojo)|leisure:|club:', i): return 'Leisure & culture'
    if i.startswith(('shop:','craft:')): return 'Retail'
    return 'Other'
TIER = {'E2':'1 · E2 Haggerston','E8':'1 · E8 London Fields','N1':'2 · N1 Hoxton','EC2A':'2 · EC2A Shoreditch','E1':'3 · E1 Whitechapel'}

wb = Workbook()

# ================= Slots =================
ws = wb.active; ws.title = 'Slots'
SC = ['Venue','Date','Day','Start','End','Slot start','Format','Players (full pitch)','Status','Hire (£ per slot)',
      'Venue charges per player (£)','Cost per player (£)','Floodlit','Booking source','Booking link','Notes','Rank in venue','Key']
hdr(ws, 1, SC)
n_s = len(slots)
for i, s in enumerate(slots, 2):
    d = datetime.date.fromisoformat(s['date']) if s['date'] else None
    tm = lambda x: datetime.time(*map(int, x.split(':'))) if x else None
    pp = None
    if s['venue'] == 'Stepney 3G' and s['status'] == 'Available':
        pp = 3 if 'Off-peak' in s['notes'] else 5
    vals = [s['venue'], d, s['day'] or None, tm(s['start']), tm(s['end']),
            f'=IF(B{i}="","",B{i}+D{i})', s['pitch_format'] or None,
            f'=IFERROR(VALUE(LEFT(G{i},FIND("-",G{i})-1))*2,"")', s['status'],
            float(s['hire_price_gbp']) if s['hire_price_gbp'] else None, pp,
            f'=IF(J{i}<>"",IF(H{i}="","",J{i}/H{i}),IF(K{i}<>"",K{i},""))',
            s['floodlit'], s['booking_source'], s['booking_url'], s['notes'] or None,
            f'=IF(I{i}="Available",COUNTIFS($A$2:$A${n_s+1},A{i},$I$2:$I${n_s+1},"Available",$F$2:$F${n_s+1},"<"&F{i})+1,"")',
            f'=IF(Q{i}="","",A{i}&"#"&Q{i})']
    for j, v in enumerate(vals, 1):
        c = ws.cell(row=i, column=j, value=v); c.font = blue if j in (10, 11) else fnt; c.border = box
    ws.cell(row=i, column=2).number_format = D
    ws.cell(row=i, column=4).number_format = T; ws.cell(row=i, column=5).number_format = T
    ws.cell(row=i, column=6).number_format = DT
    ws.cell(row=i, column=10).number_format = '£#,##0.00;-£#,##0.00;-'
    ws.cell(row=i, column=11).number_format = '£#,##0.00;-£#,##0.00;-'
    ws.cell(row=i, column=12).number_format = '£#,##0.00;-£#,##0.00;-'
    if s['booking_url']: ws.cell(row=i, column=15).hyperlink = s['booking_url']; ws.cell(row=i, column=15).font = link
ws.cell(row=1, column=11).comment = Comment('Stepney 3G is run by BookMyPitch as pay-per-player games (£3 off-peak 17:30, £5 peak). Source: Claude in Chrome check, 24 Sep 2026.', 'FC Urban')
ws.cell(row=1, column=10).comment = Comment('Whole-pitch price per slot as listed by the venue, checked 24 Sep 2026. "Price-from" at enni.space venues.', 'FC Urban')
for j, w in enumerate([30,13,6,7,7,20,16,9,16,11,11,10,8,34,40,70,8,30], 1): ws.column_dimensions[L(j)].width = w
ws.freeze_panes = 'B2'; ws.auto_filter.ref = f'A1:{L(len(SC))}{n_s+1}'
SL = f'$2:${n_s+1}'
def srng(col): return f"Slots!${col}$2:${col}${n_s+1}"

# ================= Venues =================
wv = wb.create_sheet('Venues')
VC = ['Venue','Address','Status','Open after-work slots','Earliest slot','Earliest format','Earliest hire (£)',
      'Cost per player at earliest (£)','Floodlit','Booking source','Booking link','Booking contact','Phone','Email',
      'How to book / notes','Leads tagged here','Leads using as fallback']
hdr(wv, 1, VC)
nV = len(VENUES)
for i, v in enumerate(VENUES, 2):
    rows = [r for r in slots if r['venue'] == v]
    status = 'Available' if any(r['status']=='Available' for r in rows) else rows[0]['status']
    c = contacts.get(v, {})
    vals = [v, ADDR.get(v,''), status,
            f'=COUNTIFS({srng("A")},A{i},{srng("I")},"Available")',
            f'=IF(D{i}=0,"",_xlfn.MINIFS({srng("F")},{srng("A")},A{i},{srng("I")},"Available"))',
            f'=IFERROR(INDEX({srng("G")},MATCH(A{i}&"#1",{srng("R")},0)),"")',
            f'=IFERROR(INDEX({srng("J")},MATCH(A{i}&"#1",{srng("R")},0)),"")',
            f'=IFERROR(INDEX({srng("L")},MATCH(A{i}&"#1",{srng("R")},0)),"")',
            rows[0]['floodlit'], rows[0]['booking_source'], rows[0]['booking_url'],
            c.get('booking_contact_name') or None, c.get('phone') or None, c.get('email') or None,
            (c.get('notes') or rows[0]['notes']) or None,
            "__TAGGED__", "__FALLBACK__"]
    for j, val in enumerate(vals, 1):
        cc = wv.cell(row=i, column=j, value=val); cc.font = fnt; cc.border = box; cc.alignment = top
        if j in (4,5,6,7,8): cc.font = green
    wv.cell(row=i, column=5).number_format = DT
    wv.cell(row=i, column=7).number_format = '£#,##0.00;-£#,##0.00;-'
    wv.cell(row=i, column=8).number_format = '£#,##0.00;-£#,##0.00;-'
    wv.cell(row=i, column=15).alignment = wrap
    if rows[0]['booking_url']: wv.cell(row=i, column=11).hyperlink = rows[0]['booking_url']; wv.cell(row=i, column=11).font = link
for j, w in enumerate([30,40,16,10,20,14,11,12,8,30,36,34,15,24,60,10,10], 1): wv.column_dimensions[L(j)].width = w
wv.freeze_panes = 'B2'
V = lambda col: f"Venues!${col}$2:${col}${nV+1}"

# ================= Pilot offer =================
wp = wb.create_sheet('Pilot offer')
wp['B1'] = 'Pilot offer · Haggerston Park'; wp['B1'].font = title
wp['B2'] = 'Yellow cells are inputs. Once date, kick-off, format and price are filled, every Outreach row leads with this slot.'; wp['B2'].font = fnt
P = [  # label, value, kind, owner/note
 ('Pitch', 'Haggerston Park', 'in', 'Luuk'),
 ('Address', 'Yorkton St, E2 8NH', 'in', 'Luuk'),
 ('Date', None, 'in', 'Luuk'),
 ('Kick-off', None, 'in', 'Luuk'),
 ('Duration (min)', 60, 'in', 'Luuk'),
 ('Format', None, 'in', 'Luuk'),
 ('Players on the pitch', '=IFERROR(VALUE(LEFT(C8,FIND("-",C8)-1))*2,"")', 'f', ''),
 ('Hire cost (£)', None, 'in', 'Luuk'),
 ('Price per player (£)', None, 'in', 'Joep'),
 ('Minimum paying players to cover hire', '=IF(OR(C10="",C11="",C11=0),"",ROUNDUP(C10/C11,0))', 'f', ''),
 ('Revenue if full (£)', '=IF(OR(C9="",C11=""),"",C9*C11)', 'f', ''),
 ('Margin if full (£)', '=IF(OR(C13="",C10=""),"",C13-C10)', 'f', ''),
 ('Margin if full (%)', '=IF(OR(C14="",C13="",C13=0),"",C14/C13)', 'f', ''),
 ('Booking deadline (venue)', None, 'in', 'Luuk'),
 ('Cancellation terms (venue)', None, 'in', 'Luuk'),
 ('We commit to the venue when…', None, 'in', 'Joep'),
 ('Joining link (app)', None, 'in', ''),
 ('Deadline for players to commit', None, 'in', ''),
 ('Who confirms the booking', 'Hackney Parks bookings (GLL) · 020 8986 7955 (Mon–Fri 09:00–15:30) · hackney.marshes@gll.org', 'in', 'Luuk'),
 ('Floodlit', 'Yes per Playfinder / Hackney Council (18:00–22:00 in term time); fcurban.com page says no — confirm on the call', 'in', 'Luuk'),
]
wp['B3'], wp['C3'], wp['D3'] = 'Item', 'Value', 'Owner'
for c in ('B3','C3','D3'): wp[c].font = white; wp[c].fill = HDR
for k, (lab, val, kind, own) in enumerate(P, 4):   # Pitch lands on row 4... shift so Pitch is C3? keep explicit map below
    pass
# explicit rows so formulas above line up: Pitch=C3? no — lay out from row 3 with header on row 2
wp.delete_rows(3); wp['B2'].value = None
wp['B2'] = 'Yellow cells are inputs. Once date, kick-off, format and price are filled, every Outreach row leads with this slot.'; wp['B2'].font = fnt
rowmap = {}
for k, (lab, val, kind, own) in enumerate(P, 3):
    wp.cell(row=k, column=2, value=lab).font = bold
    c = wp.cell(row=k, column=3, value=val); c.alignment = Alignment(wrap_text=True, vertical='top')
    c.font = blue if kind == 'in' else fnt
    if kind == 'in': c.fill = YEL
    wp.cell(row=k, column=4, value=own or None).font = fnt
    rowmap[lab] = k
# rows: Pitch 3, Address 4, Date 5, Kick-off 6, Duration 7, Format 8, Players 9, Hire 10, Price 11, Min 12, Rev 13, Margin 14, Margin% 15
assert rowmap['Date']==5 and rowmap['Format']==8 and rowmap['Price per player (£)']==11
wp['C5'].number_format = D; wp['C6'].number_format = T
for r in (10,11,13,14): wp[f'C{r}'].number_format = '£#,##0.00;-£#,##0.00;-'
wp['C15'].number_format = '0.0%;-0.0%;-'
wp['C16'].number_format = D; wp['C20'].number_format = D
r_ready = len(P) + 4
wp.cell(row=r_ready, column=2, value='Pilot ready to lead outreach?').font = bold
wp.cell(row=r_ready, column=3, value='=IF(AND(C5<>"",C6<>"",C8<>"",C11<>""),"Yes","No — fill Date, Kick-off, Format and Price")').font = bold
READY = f"'Pilot offer'!$C${r_ready}"
dvf = DataValidation(type='list', formula1='"5-a-side,6-a-side,7-a-side,8-a-side,11-a-side"', allow_blank=True); wp.add_data_validation(dvf); dvf.add('C8')
wp.cell(row=r_ready+2, column=2, value='Cost floor for comparison: see Venues › Cost per player at earliest. Old St – Moreland 6-a-side works out at £7.50 per player at cost; COLA 5-a-side £9.10.').font = fnt
wp.column_dimensions['A'].width = 2; wp.column_dimensions['B'].width = 36; wp.column_dimensions['C'].width = 62; wp.column_dimensions['D'].width = 10

# ================= Outreach =================
wo = wb.create_sheet('Outreach', 0)
cols = [  # (header, band, width)
 ('#','Lead',5),('Tier','Lead',17),('Segment','Lead',20),('List','Lead',12),('Business','Lead',34),('Industry','Lead',20),
 ('Email','Lead',30),('Email type','Lead',13),('Phone','Lead',16),('Website','Lead',28),('Address','Lead',30),('Postcode','Lead',10),
 ('Tagged venue','Tagged venue',26),('Walk (min)','Tagged venue',7),('Status','Tagged venue',15),('Open slots','Tagged venue',7),('Earliest slot','Tagged venue',19),
 ('Bookable nearby?','Fallback pitch',10),('—','Fallback pitch',2),
 ('Fallback venue','Fallback pitch',26),('Fallback slot','Fallback pitch',19),('Format','Fallback pitch',10),('Cost per player at cost (£)','Fallback pitch',10),
 ('Lead with: venue','Lead with (message)',24),('Lead with: slot','Lead with (message)',19),('Lead with: format','Lead with (message)',10),
 ('Lead with: price per player (£)','Lead with (message)',10),('Lead-with line (for drafting)','Lead with (message)',60),
 ('Owner','Tracking — fill in',9),('Channel','Tracking — fill in',11),('Contacted on','Tracking — fill in',12),('Replied','Tracking — fill in',8),
 ('Call booked','Tracking — fill in',8),('Group created','Tracking — fill in',8),('First game booked','Tracking — fill in',8),
 ('Second game booked','Tracking — fill in',8),('Sees us as competitor?','Tracking — fill in',10),
 ('Objection (exact words)','Tracking — fill in',40),('Next step','Tracking — fill in',28),('Notes','Tracking — fill in',30)]
# drop the spacer column
cols = [c for c in cols if c[0] != '—']
H = [c[0] for c in cols]; ci = {h: i+1 for i, h in enumerate(H)}
# section band row 1
start = 1
for band in dict.fromkeys(c[1] for c in cols):
    span = [i+1 for i, c in enumerate(cols) if c[1] == band]
    a, b = span[0], span[-1]
    wo.merge_cells(start_row=1, start_column=a, end_row=1, end_column=b)
    cell = wo.cell(row=1, column=a, value=band); cell.font = white
    cell.fill = PatternFill('solid', fgColor=BANDS[band]); cell.alignment = Alignment(horizontal='left', vertical='center')
    for j in range(a, b+1): wo.cell(row=1, column=j).fill = PatternFill('solid', fgColor=BANDS[band])
for i, (h, band, w) in enumerate(cols, 1):
    c = wo.cell(row=2, column=i, value=h); c.font = white if band != 'Tracking — fill in' else bold
    c.fill = HDR if band != 'Tracking — fill in' else YEL
    c.alignment = Alignment(wrap_text=True, vertical='center'); wo.column_dimensions[L(i)].width = w
wo.row_dimensions[2].height = 42

# sort: tier, then postcode
def tier(pc): return TIER.get(pc.split()[0].upper(), '4 · other') if pc else '4 · other'
leads.sort(key=lambda r: (tier(r['Postcode']), r['Postcode'], r['Business']))
if os.environ.get('SAMPLE'):
    seen=set(); pick=[]
    for x in leads:
        v=x['Currently tagged venue'].strip()
        if v not in seen: seen.add(v); pick.append(x)
    pick += [x for x in leads if x not in pick][:30-len(pick)]
    leads = pick
LIST = {}  # From list lookup
import openpyxl
src = openpyxl.load_workbook('/root/.claude/uploads/1a31dd2e-3db0-5067-ac37-58491793a12d/c365f032-fcurban_all_businesses_merged.xlsx', read_only=True)['London']
it = src.iter_rows(values_only=True); hh = list(next(it)); ix = {k:i for i,k in enumerate(hh)}
for r in it: LIST[(str(r[ix['Business']]), str(r[ix['Email']]))] = r[ix['From list']]

C = lambda h: L(ci[h])
for n, r in enumerate(leads, 3):
    tv = r['Currently tagged venue'].strip()
    fb = tv if tv in BOOKABLE else DEFAULT_ALT
    walk = r['Walk to tagged venue (min)']
    lst = LIST.get((r['Business'], r['Email']), '')
    row = {
     '#': n-2, 'Tier': tier(r['Postcode']), 'Segment': seg(r['Industry']), 'List': (lst or '').replace(' list',''),
     'Business': r['Business'], 'Industry': r['Industry'], 'Email': r['Email'], 'Email type': r['Email type'],
     'Phone': r['Phone (international)'] or None, 'Website': r['Website'] or None, 'Address': r['Address'] or None,
     'Postcode': r['Postcode'], 'Tagged venue': tv, 'Walk (min)': int(float(walk)) if walk not in ('', None) else None,
     'Status': f'=IFERROR(INDEX({V("C")},MATCH({C("Tagged venue")}{n},{V("A")},0)),"Not checked")',
     'Open slots': f'=IFERROR(INDEX({V("D")},MATCH({C("Tagged venue")}{n},{V("A")},0)),0)',
     'Earliest slot': f'=IFERROR(INDEX({V("E")},MATCH({C("Tagged venue")}{n},{V("A")},0)),"")',
     'Bookable nearby?': f'=IF({C("Open slots")}{n}>0,"Yes","No")',
     'Fallback venue': fb,
     'Fallback slot': f'=IFERROR(INDEX({V("E")},MATCH({C("Fallback venue")}{n},{V("A")},0)),"")',
     'Format': f'=IFERROR(INDEX({V("F")},MATCH({C("Fallback venue")}{n},{V("A")},0)),"")',
     'Cost per player at cost (£)': f'=IFERROR(INDEX({V("H")},MATCH({C("Fallback venue")}{n},{V("A")},0)),"")',
     'Lead with: venue': f"=IF({READY}=\"Yes\",'Pilot offer'!$C$3,{C('Fallback venue')}{n})",
     'Lead with: slot': f"=IF({READY}=\"Yes\",'Pilot offer'!$C$5+'Pilot offer'!$C$6,{C('Fallback slot')}{n})",
     'Lead with: format': f"=IF({READY}=\"Yes\",'Pilot offer'!$C$8,{C('Format')}{n})",
     'Lead with: price per player (£)': f"=IF({READY}=\"Yes\",'Pilot offer'!$C$11,\"\")",
     'Lead-with line (for drafting)': (
        f'=IF({C("Lead with: slot")}{n}="","",{C("Lead with: venue")}{n}&" · "&TEXT({C("Lead with: slot")}{n},"ddd d mmm, hh:mm")'
        f'&" · "&{C("Lead with: format")}{n}&IF({C("Lead with: price per player (£)")}{n}<>"",'
        f'" · £"&TEXT({C("Lead with: price per player (£)")}{n},"0.00")&" per player",'
        f'" · price TBC (cost £"&TEXT({C("Cost per player at cost (£)")}{n},"0.00")&" pp)"))'),
    }
    for h, v in row.items():
        c = wo.cell(row=n, column=ci[h], value=v); c.font = fnt; c.border = box; c.alignment = top
        if isinstance(v, str) and v.startswith('='): c.font = green
    for h in ('Earliest slot','Fallback slot','Lead with: slot'): wo.cell(row=n, column=ci[h]).number_format = DT
    for h in ('Cost per player at cost (£)','Lead with: price per player (£)'): wo.cell(row=n, column=ci[h]).number_format = '£#,##0.00;-£#,##0.00;-'
    wo.cell(row=n, column=ci['Contacted on']).number_format = D
    if r['Website']:
        u = r['Website'] if r['Website'].startswith('http') else 'https://' + r['Website']
        wo.cell(row=n, column=ci['Website']).hyperlink = u; wo.cell(row=n, column=ci['Website']).font = link
last = len(leads) + 2
def dv(h, opts):
    d = DataValidation(type='list', formula1='"' + ','.join(opts) + '"', allow_blank=True)
    wo.add_data_validation(d); d.add(f'{C(h)}3:{C(h)}{MAXR}')
dv('Owner', ['Luuk','Joep','Brian','Stan','Nero','Nicky'])
dv('Channel', ['Email','LinkedIn','Phone','Instagram','WhatsApp','Walk-in','Other'])
for h in ('Replied','Call booked','Group created','First game booked','Second game booked','Sees us as competitor?'): dv(h, ['Yes','No'])
dd = DataValidation(type='date', allow_blank=True); wo.add_data_validation(dd); dd.add(f'{C("Contacted on")}3:{C("Contacted on")}{MAXR}')
wo.freeze_panes = f'{C("Industry")}3'
wo.auto_filter.ref = f'A2:{L(len(H))}{last}'
wo.cell(row=2, column=ci['Objection (exact words)']).comment = Comment('Only when they see FC Urban as a competitor. Ask: "Which part of this offer feels like we would take over your group?" Record their words verbatim.', 'Pilot ticket')
wo.cell(row=2, column=ci['Fallback venue']).comment = Comment('Rule: the tagged venue if it has instantly or request-bookable after-work slots (COLA, Old St, Hackney, Shoreditch Rooftop, Market Road); otherwise COLA Shoreditch Park, the nearest venue to Haggerston with the most open slots.', 'FC Urban')
wo.cell(row=2, column=ci['Lead with: venue']).comment = Comment('Switches to the Haggerston Park slot automatically once Pilot offer › "Pilot ready" says Yes.', 'FC Urban')

# patch Venues lead counts now that Outreach column letters are known
for i in range(2, nV + 2):
    wv.cell(row=i, column=16, value=f"=COUNTIF(Outreach!${C('Tagged venue')}$3:${C('Tagged venue')}${MAXR},A{i})").font = green
    wv.cell(row=i, column=17, value=f"=COUNTIF(Outreach!${C('Fallback venue')}$3:${C('Fallback venue')}${MAXR},A{i})").font = green

# ================= Totals =================
wt = wb.create_sheet('Totals')
wt['A1'] = 'Totals'; wt['A1'].font = title
O = lambda h: f"Outreach!${C(h)}$3:${C(h)}${MAXR}"
r = 3
def block(title_, rows_, formula_fn, hdrs=('','Count')):
    global r
    wt.cell(row=r, column=1, value=title_).font = bold; r += 1
    for j, h in enumerate(hdrs, 1):
        c = wt.cell(row=r, column=j, value=h); c.font = white; c.fill = HDR
    r += 1
    first = r
    for lab in rows_:
        wt.cell(row=r, column=1, value=lab).font = fnt
        for j, f in enumerate(formula_fn(lab, r), 2):
            c = wt.cell(row=r, column=j, value=f); c.font = fnt
        r += 1
    wt.cell(row=r, column=1, value='Total').font = bold
    for j in range(2, len(hdrs)+1):
        if hdrs[j-1].endswith('%'): continue
        c = wt.cell(row=r, column=j, value=f'=SUM({L(j)}{first}:{L(j)}{r-1})'); c.font = bold
    r += 2

block('Leads by tier', sorted(set(TIER.values())), lambda lab, rr: [f'=COUNTIF({O("Tier")},A{rr})'])
block('Leads by segment', ['Office & professional','Coworking / shared office','Hospitality','Education','Retail','Leisure & culture','Health','Other'],
      lambda lab, rr: [f'=COUNTIF({O("Segment")},A{rr})'])
block('Leads by tagged-venue status', ['Available','Contact required','No availability'], lambda lab, rr: [f'=COUNTIF({O("Status")},A{rr})'])

# funnel
STAGES = [('Contacted','Contacted on','>0'),('Replied','Replied','Yes'),('Call booked','Call booked','Yes'),
          ('Group created','Group created','Yes'),('First game booked','First game booked','Yes'),('Second game booked','Second game booked','Yes')]
wt.cell(row=r, column=1, value='Funnel (from the Tracking columns on Outreach)').font = bold; r += 1
for j, h in enumerate(['Stage','Leads','% of previous stage'], 1):
    c = wt.cell(row=r, column=j, value=h); c.font = white; c.fill = HDR
r += 1; f0 = r
for k, (lab, col, crit) in enumerate(STAGES):
    wt.cell(row=r, column=1, value=lab).font = fnt
    wt.cell(row=r, column=2, value=f'=COUNTIF({O(col)},"{crit}")').font = fnt
    if k:
        c = wt.cell(row=r, column=3, value=f'=IF(B{r-1}=0,"",B{r}/B{r-1})'); c.number_format = '0.0%'; c.font = fnt
    r += 1
wt.cell(row=r, column=1, value='Saw FC Urban as a competitor').font = fnt
wt.cell(row=r, column=2, value=f'=COUNTIF({O("Sees us as competitor?")},"Yes")').font = fnt
r += 3

def funnel_by(title_, field, values):
    global r
    wt.cell(row=r, column=1, value=title_).font = bold; r += 1
    hd = [field] + [s[0] for s in STAGES]
    for j, h in enumerate(hd, 1):
        c = wt.cell(row=r, column=j, value=h); c.font = white; c.fill = HDR
    r += 1
    for v in values:
        wt.cell(row=r, column=1, value=v).font = fnt
        for j, (lab, col, crit) in enumerate(STAGES, 2):
            wt.cell(row=r, column=j, value=f'=COUNTIFS({O(field)},$A{r},{O(col)},"{crit}")').font = fnt
        r += 1
    r += 2
funnel_by('Funnel by channel', 'Channel', ['Email','LinkedIn','Phone','Instagram','WhatsApp','Walk-in','Other'])
funnel_by('Funnel by segment', 'Segment', ['Office & professional','Coworking / shared office','Hospitality','Education','Retail','Leisure & culture','Health','Other'])

# slots by venue x weekday
wt.cell(row=r, column=1, value='Open after-work slots by venue and weekday (28 Sep – 23 Oct)').font = bold; r += 1
days = ['Mon','Tue','Wed','Thu','Fri']
for j, h in enumerate(['Venue'] + days + ['Total'], 1):
    c = wt.cell(row=r, column=j, value=h); c.font = white; c.fill = HDR
r += 1; s0 = r
for v in VENUES:
    wt.cell(row=r, column=1, value=v).font = fnt
    for j, d in enumerate(days, 2):
        wt.cell(row=r, column=j, value=f'=COUNTIFS({srng("A")},$A{r},{srng("C")},"{d}",{srng("I")},"Available")').font = fnt
    wt.cell(row=r, column=7, value=f'=SUM(B{r}:F{r})').font = bold
    r += 1
wt.cell(row=r, column=1, value='Total').font = bold
for j in range(2, 8): wt.cell(row=r, column=j, value=f'=SUM({L(j)}{s0}:{L(j)}{r-1})').font = bold
wt.column_dimensions['A'].width = 34
for j in range(2, 9): wt.column_dimensions[L(j)].width = 14

# ================= Read me =================
wr = wb.create_sheet('Read me')
lines = [
 ('FC Urban · London pilot · Haggerston Park', title),
 ('Goal: book a first game by leading with a specific pitch, time and price per player, and learn what makes organisers commit or hold back.', fnt),
 ('', fnt),
 ('Tabs', bold),
 ('Outreach — one row per organiser to contact (696). Everything needed to draft and log a message is on the row.', fnt),
 ('Pilot offer — the Haggerston Park slot and price. Fill the yellow cells; Outreach then leads with this slot on every row.', fnt),
 ('Venues — one row per nearby venue: open slots, earliest slot, cost per player, floodlights, who to call.', fnt),
 ('Slots — every open after-work slot found (weekdays 17:30–20:30 kick-off, 28 Sep – 23 Oct 2026).', fnt),
 ('Totals — leads by tier/segment, the outreach funnel (overall, by channel, by segment) and slots by weekday.', fnt),
 ('', fnt),
 ('What to fill in (yellow)', bold),
 ('Pilot offer: Date, Kick-off, Format, Hire cost (Luuk); Price per player and the commit point (Joep); booking deadline, cancellation terms, joining link.', fnt),
 ('Outreach › Tracking columns: Owner, Channel, Contacted on, then Yes/No per funnel stage. Objection only when they see us as a competitor — exact words.', fnt),
 ('Blue text = values typed in from a source. Green text = formulas; leave those alone.', fnt),
 ('', fnt),
 ('Example of a logged row (Tracking columns only)', bold),
]
for k, (t, f_) in enumerate(lines, 1):
    c = wr.cell(row=k, column=1, value=t); c.font = f_
ex_h = ['Owner','Channel','Contacted on','Replied','Call booked','Group created','First game booked','Second game booked','Sees us as competitor?','Objection (exact words)','Next step']
ex_v = ['Luuk','Email',datetime.date(2026,9,29),'Yes','Yes','No','No','No','Yes','"We already have a Thursday kickabout, I don\'t want players moving to your app"','Call Tue 6 Oct 12:30, send pitch link']
rr = len(lines) + 1
for j, (h, v) in enumerate(zip(ex_h, ex_v), 1):
    a = wr.cell(row=rr, column=j, value=h); a.font = white; a.fill = HDR; a.alignment = Alignment(wrap_text=True)
    b = wr.cell(row=rr+1, column=j, value=v); b.font = fnt; b.fill = YEL; b.alignment = Alignment(wrap_text=True)
wr.cell(row=rr+1, column=3).number_format = D
rr += 3
rules = [
 ('Rules used', bold),
 ('Tier: 1 = E2 and E8 (closest to Yorkton St); 2 = N1 and EC2A; 3 = E1.', fnt),
 ('Segment: grouped from the Industry column — Office & professional, Coworking / shared office, Hospitality, Education, Retail, Leisure & culture, Health, Other.', fnt),
 ('Fallback venue: the lead’s tagged venue if it has bookable after-work slots; otherwise COLA Shoreditch Park (closest to Haggerston, most open slots).', fnt),
 ('Cost per player at cost: whole-pitch hire ÷ players on a full pitch (5-a-side = 10, 6 = 12, 7 = 14). This is the floor, not the price to charge.', fnt),
 ('', fnt),
 ('Sources and caveats', bold),
 ('Slots and contacts: Claude in Chrome check of each venue’s booking system, 24 Sep 2026. Leads: FC Urban London lead list, postcodes E1, E2, E8, N1, EC2A.', fnt),
 ('Better (GLL) venues release slots only 6 days ahead — Shoreditch Rooftop, Market Road and Rosemary Gardens will show more availability closer to the date.', fnt),
 ('Stepney 3G is run by BookMyPitch as pay-per-player games (£3–£5), not a pitch we hire — it does not fit the “our pitch, our price” offer.', fnt),
 ('Haggerston Park: no online calendar; Playfinder shows it fully booked. Floodlit per Playfinder and Hackney Council, but the fcurban.com page says no — confirm on the call.', fnt),
 ('Cancellation terms and booking deadlines were not published by any venue — ask on the call.', fnt),
]
for k, (t, f_) in enumerate(rules, rr):
    wr.cell(row=k, column=1, value=t).font = f_
wr.column_dimensions['A'].width = 16
for j in range(2, 12): wr.column_dimensions[L(j)].width = 16
wr.column_dimensions['J'].width = 44; wr.column_dimensions['K'].width = 34

wb.move_sheet('Pilot offer', offset=-(wb.sheetnames.index('Pilot offer') - 1))
wb.save(OUT)
print('saved', OUT, '| sheets:', wb.sheetnames, '| outreach rows:', len(leads))
