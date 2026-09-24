"""Build the City of London / Canary Wharf corporate outreach workbook (Google Sheets friendly).
Inputs (same folder): city_canary_wharf_corporates_400.csv, venues.csv, slots.csv, booking_contacts.csv
"""
import csv, os, datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.comments import Comment

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get('OUT', f'{HERE}/FC_Urban_City_Canary_Wharf_corporates_400.xlsx')
MAXR = int(os.environ.get('MAXR', '1000'))
rd = lambda f: list(csv.DictReader(open(f'{HERE}/{f}', encoding='utf-8')))
corps, venues, slots = rd('city_canary_wharf_corporates_400.csv'), rd('venues.csv'), rd('slots.csv')
contacts = {r['venue']: r for r in rd('booking_contacts.csv')}
emails = {r['company']: r for r in rd('emails.csv')} if os.path.exists(f'{HERE}/emails.csv') else {}
if os.environ.get('SAMPLE'): corps = corps[:int(os.environ['SAMPLE'])]

# ---------- styles ----------
F = 'Arial'
fnt, bold = Font(name=F, size=10), Font(name=F, size=10, bold=True)
white, title = Font(name=F, size=10, bold=True, color='FFFFFF'), Font(name=F, size=14, bold=True)
blue, green = Font(name=F, size=10, color='0000FF'), Font(name=F, size=10, color='008000')
link = Font(name=F, size=10, color='1155CC', underline='single')
YEL, HDR = PatternFill('solid', fgColor='FFF2CC'), PatternFill('solid', fgColor='1F3864')
BANDS = {'Company': '2F5496', 'Contact — fill in': 'BF9000', 'Nearest pitch': '548235',
         'Lead with (message)': 'C55A11', 'Tracking — fill in': 'BF9000'}
thin = Side(style='thin', color='D9D9D9'); box = Border(bottom=thin)
wrap, top = Alignment(wrap_text=True, vertical='top'), Alignment(vertical='top')
DT, D, T = 'ddd d mmm yyyy hh:mm', 'ddd d mmm yyyy', 'hh:mm'
GBP = '£#,##0.00;-£#,##0.00;-'

def hdr(ws, row, cols, fill=HDR):
    for i, h in enumerate(cols, 1):
        c = ws.cell(row=row, column=i, value=h); c.font = white; c.fill = fill
        c.alignment = Alignment(wrap_text=True, vertical='center')

wb = Workbook()

# ================= Slots =================
ws = wb.active; ws.title = 'Slots'
SC = ['Venue', 'Date', 'Day', 'Start', 'End', 'Slot start', 'Format', 'Players (full pitch)', 'Status', 'Hire (£ per slot)',
      'Cost per player (£)', 'Floodlit', 'Booking source', 'Booking link', 'Notes', 'Checked', 'Rank in venue', 'Key']
hdr(ws, 1, SC)
n_s = max(len(slots), 1)
tm = lambda x: datetime.time(*map(int, x.split(':')[:2])) if x else None
for i, s in enumerate(slots, 2):
    d = datetime.date.fromisoformat(s['date']) if s['date'] else None
    try: hire = float(s['hire_price_gbp']) if s['hire_price_gbp'] else None
    except ValueError: hire = None
    vals = [s['venue'], d, s['day'] or None, tm(s['start']), tm(s['end']),
            f'=IF(B{i}="","",B{i}+D{i})', s['pitch_format'] or None,
            f'=IFERROR(VALUE(LEFT(G{i},FIND("-",G{i})-1))*2,"")', s['status'], hire,
            f'=IF(OR(J{i}="",H{i}=""),"",J{i}/H{i})',
            s['floodlit'] or None, s['booking_source'] or None, s['booking_url'] or None, s['notes'] or None, s.get('checked') or None,
            f'=IF(AND(I{i}="Available",F{i}<>""),COUNTIFS($A$2:$A${n_s+1},A{i},$I$2:$I${n_s+1},"Available",$F$2:$F${n_s+1},"<"&F{i})+1,"")',
            f'=IF(Q{i}="","",A{i}&"#"&Q{i})']
    for j, v in enumerate(vals, 1):
        c = ws.cell(row=i, column=j, value=v); c.font = blue if j == 10 else (green if isinstance(v, str) and v.startswith('=') else fnt); c.border = box
    ws.cell(row=i, column=2).number_format = D
    ws.cell(row=i, column=4).number_format = T; ws.cell(row=i, column=5).number_format = T
    ws.cell(row=i, column=6).number_format = DT
    ws.cell(row=i, column=10).number_format = GBP; ws.cell(row=i, column=11).number_format = GBP
    if s['booking_url'].startswith('http'): ws.cell(row=i, column=14).hyperlink = s['booking_url']; ws.cell(row=i, column=14).font = link
ws.cell(row=1, column=10).comment = Comment('Whole-pitch price per slot as listed by the venue on the day it was checked.', 'FC Urban')
for j, w in enumerate([34, 13, 6, 7, 7, 20, 16, 9, 16, 11, 10, 8, 30, 40, 70, 22, 8, 30], 1): ws.column_dimensions[L(j)].width = w
ws.freeze_panes = 'B2'; ws.auto_filter.ref = f'A1:{L(len(SC))}{n_s+1}'
srng = lambda col: f"Slots!${col}$2:${col}${n_s+1}"

# ================= Venues =================
wv = wb.create_sheet('Venues')
VC = ['Venue', 'Type', 'Address', 'Postcode', 'Status', 'Open after-work slots', 'Earliest open slot', 'Earliest format',
      'Earliest hire (£)', 'Cost per player at earliest (£)', 'Chosen slot (override)', 'Chosen format (override)', 'Lead-with slot', 'Lead-with format',
      'Floodlit', 'Booking source', 'Booking link', 'Booking contact', 'Phone', 'Email', 'How to book / notes', 'FC Urban page',
      'Companies: nearest pitch', 'Companies: lead with']
hdr(wv, 1, VC)
for j in (11, 12): wv.cell(row=1, column=j).fill = YEL; wv.cell(row=1, column=j).font = bold
nV = len(venues)
for i, v in enumerate(venues, 2):
    rows = [r for r in slots if r['venue'] == v['venue']]
    status = ('Available' if any(r['status'] == 'Available' for r in rows) else rows[0]['status']) if rows else 'Not checked'
    c = contacts.get(v['venue'], {})
    r0 = rows[0] if rows else {}
    vals = [v['venue'], v['kind'], v['address'] or None, v['postcode'], status,
            f'=COUNTIFS({srng("A")},A{i},{srng("I")},"Available")',
            f'=IF(F{i}=0,"",_xlfn.MINIFS({srng("F")},{srng("A")},A{i},{srng("I")},"Available"))',
            f'=IFERROR(INDEX({srng("G")},MATCH(A{i}&"#1",{srng("R")},0)),"")',
            f'=IFERROR(INDEX({srng("J")},MATCH(A{i}&"#1",{srng("R")},0)),"")',
            f'=IFERROR(INDEX({srng("K")},MATCH(A{i}&"#1",{srng("R")},0)),"")',
            None, None,
            f'=IF(K{i}<>"",K{i},G{i})', f'=IF(L{i}<>"",L{i},IF(H{i}<>"",H{i},"5-a-side"))',
            r0.get('floodlit') or None, r0.get('booking_source') or None, r0.get('booking_url') or None,
            c.get('booking_contact_name') or None, c.get('phone') or None, c.get('email') or None,
            (c.get('notes') or r0.get('notes')) or None, v['fcurban_page'] or None, '__NEAR__', '__LEAD__']
    for j, val in enumerate(vals, 1):
        cc = wv.cell(row=i, column=j, value=val); cc.border = box; cc.alignment = top
        cc.font = green if isinstance(val, str) and val.startswith('=') else fnt
    for j in (11, 12): wv.cell(row=i, column=j).fill = YEL; wv.cell(row=i, column=j).font = blue
    for j in (7, 11, 13): wv.cell(row=i, column=j).number_format = DT
    for j in (9, 10): wv.cell(row=i, column=j).number_format = GBP
    wv.cell(row=i, column=21).alignment = wrap
    for j, u in ((17, r0.get('booking_url', '')), (22, v['fcurban_page'])):
        if u and u.startswith('http'): wv.cell(row=i, column=j).hyperlink = u; wv.cell(row=i, column=j).font = link
dvo = DataValidation(type='list', formula1='"5-a-side,6-a-side,7-a-side,8-a-side,9-a-side,11-a-side"', allow_blank=True)
wv.add_data_validation(dvo); dvo.add(f'L2:L{nV+1}')
wv.cell(row=1, column=11).comment = Comment('Fill once a slot is confirmed with the venue (date + time, e.g. 6/10/2026 19:00). Overrides the earliest open slot everywhere, including the drafts. Use this for "Contact required" venues.', 'FC Urban')
for j, w in enumerate([34, 18, 36, 10, 16, 9, 20, 13, 10, 10, 20, 12, 20, 12, 8, 28, 36, 30, 15, 26, 60, 34, 10, 10], 1): wv.column_dimensions[L(j)].width = w
wv.freeze_panes = 'B2'; wv.auto_filter.ref = f'A1:{L(len(VC))}{nV+1}'
V = lambda col: f"Venues!${col}$2:${col}${nV+1}"

# ================= Offer =================
wp = wb.create_sheet('Offer')
wp['B1'] = 'Offer · after-work football for City and Canary Wharf teams'; wp['B1'].font = title
wp['B2'] = 'Yellow cells are inputs. They feed every draft on Outreach. The pitch and slot per company come from Venues (Lead-with slot).'; wp['B2'].font = fnt
P = [('Price per player (£)', None, 'Brian', 'Corporate teams can carry more than the Haggerston pilot. Compare with Venues › Cost per player at earliest.'),
     ('Default sender (when Owner is empty)', 'Brian', '', ''),
     ('Joining link (app)', None, '', ''),
     ('Deadline for players to commit', None, '', 'Date. Leave empty to drop the sentence.'),
     ('Game length (min)', 60, '', ''),
     ('Minimum paying players to cover hire', '=IF(OR(C4="",C4=0),"",ROUNDUP(_xlfn.MAXIFS(Venues!$I$2:$I$' + str(nV+1) + ',Venues!$F$2:$F$' + str(nV+1) + ',">0")/C4,0))', '', 'Worst case across venues with open slots (highest earliest hire ÷ price).')]
hdr_row = 3
for j, h in enumerate(['Item', 'Value', 'Owner', 'Note'], 2):
    c = wp.cell(row=hdr_row, column=j, value=h); c.font = white; c.fill = HDR
for k, (lab, val, own, note) in enumerate(P, 4):
    wp.cell(row=k, column=2, value=lab).font = bold
    c = wp.cell(row=k, column=3, value=val); c.alignment = top
    if isinstance(val, str) and val.startswith('='): c.font = green
    else: c.font = blue; c.fill = YEL
    wp.cell(row=k, column=4, value=own or None).font = fnt
    wp.cell(row=k, column=5, value=note or None).font = fnt
# rows: price C4, sender C5, joining link C6, deadline C7, game length C8, minimum players C9
wp['C4'].number_format = GBP; wp['C7'].number_format = D
PRICE, SENDER, JLINK, DEADLINE = "Offer!$C$4", "Offer!$C$5", "Offer!$C$6", "Offer!$C$7"
wp.column_dimensions['A'].width = 2; wp.column_dimensions['B'].width = 38; wp.column_dimensions['C'].width = 30
wp.column_dimensions['D'].width = 8; wp.column_dimensions['E'].width = 80

# ================= Outreach =================
wo = wb.create_sheet('Outreach', 0)
cols = [
 ('#', 'Company', 5), ('Priority', 'Company', 7), ('Segment', 'Company', 20), ('Area', 'Company', 13), ('Company', 'Company', 36),
 ('Name for messages', 'Company', 26), ('Website', 'Company', 26), ('Email', 'Company', 30), ('Email type', 'Company', 13), ('Email source', 'Company', 14),
 ('Companies House no.', 'Company', 11), ('Companies House', 'Company', 12),
 ('Accounts', 'Company', 9), ('Incorporated', 'Company', 11), ('Registered address', 'Company', 34), ('Postcode', 'Company', 10),
 ('In 933 research list?', 'Company', 16),
 ('Contact first name', 'Contact — fill in', 12), ('Contact full name', 'Contact — fill in', 20), ('Job title', 'Contact — fill in', 22),
 ('Direct email', 'Contact — fill in', 28), ('Phone', 'Contact — fill in', 14),
 ('Nearest pitch', 'Nearest pitch', 28), ('Walk (min)', 'Nearest pitch', 7), ('Other pitches ≤19 min', 'Nearest pitch', 34),
 ('Lead with: pitch', 'Lead with (message)', 28), ('Walk to it (min)', 'Lead with (message)', 7), ('Pitch status', 'Lead with (message)', 15),
 ('Open slots', 'Lead with (message)', 7), ('Lead with: slot', 'Lead with (message)', 19), ('Lead with: format', 'Lead with (message)', 10),
 ('Price per player (£)', 'Lead with (message)', 9), ('Lead-with line', 'Lead with (message)', 56),
 ('Send to', 'Lead with (message)', 30), ('Subject', 'Lead with (message)', 44), ('Email draft', 'Lead with (message)', 60),
 ('Follow-up email (day 4)', 'Lead with (message)', 50), ('Draft status', 'Lead with (message)', 16),
 ('Owner', 'Tracking — fill in', 9), ('Channel', 'Tracking — fill in', 11), ('Contacted on', 'Tracking — fill in', 12), ('Follow-up sent on', 'Tracking — fill in', 12),
 ('Replied', 'Tracking — fill in', 8), ('Call booked', 'Tracking — fill in', 8), ('Group created', 'Tracking — fill in', 8),
 ('First game booked', 'Tracking — fill in', 8), ('Second game booked', 'Tracking — fill in', 8), ('Objection (exact words)', 'Tracking — fill in', 40),
 ('Next step', 'Tracking — fill in', 28), ('Notes', 'Tracking — fill in', 30)]
H = [c[0] for c in cols]; ci = {h: i+1 for i, h in enumerate(H)}
C = lambda h: L(ci[h])
for band in dict.fromkeys(c[1] for c in cols):
    span = [i+1 for i, c in enumerate(cols) if c[1] == band]; a, b = span[0], span[-1]
    wo.merge_cells(start_row=1, start_column=a, end_row=1, end_column=b)
    cell = wo.cell(row=1, column=a, value=band); cell.font = white; cell.alignment = Alignment(vertical='center')
    for j in range(a, b+1): wo.cell(row=1, column=j).fill = PatternFill('solid', fgColor=BANDS[band])
for i, (h, band, w) in enumerate(cols, 1):
    fill_in = band.endswith('fill in')
    c = wo.cell(row=2, column=i, value=h); c.font = bold if fill_in else white; c.fill = YEL if fill_in else HDR
    c.alignment = Alignment(wrap_text=True, vertical='center'); wo.column_dimensions[L(i)].width = w
wo.row_dimensions[2].height = 42

NL = 'CHAR(10)'
for n, r in enumerate(corps, 3):
    ref = lambda h: f'{C(h)}{n}'
    row = {
     '#': int(r['#']), 'Priority': int(r['Priority']), 'Segment': r['Segment'], 'Area': r['Area'], 'Company': r['Company name'],
     'Name for messages': r['Name for messages'], 'Companies House no.': r['Companies House number'] or None,
     'Companies House': 'Open' if r['Companies House link'] else None,
     'Website': (emails.get(r['Company name'], {}).get('website') or None), 'Email': (emails.get(r['Company name'], {}).get('email') or None),
     'Email type': (emails.get(r['Company name'], {}).get('email_type') or 'Not found'),
     'Email source': ('Open page' if emails.get(r['Company name'], {}).get('source', '').startswith('http') else (emails.get(r['Company name'], {}).get('via') or None)),
     'Accounts': r['Accounts type'] or None, 'Incorporated': datetime.datetime.strptime(r['Incorporated'], '%d/%m/%Y').date() if r['Incorporated'] else None,
     'Registered address': r['Registered address'] or None, 'Postcode': r['Postcode'],
     'In 933 research list?': ('Yes' if r['Also in earlier 933 research list (not messaged)'] else 'No'),
     'Nearest pitch': r['Nearest pitch'], 'Walk (min)': round(float(r['Walk to nearest (min)'])),
     'Other pitches ≤19 min': r['Other pitches within 19 min'] or None,
     'Lead with: pitch': r['Lead-with pitch'], 'Walk to it (min)': round(float(r['Walk to lead-with pitch (min)'])),
     'Pitch status': f'=IFERROR(INDEX({V("E")},MATCH({ref("Lead with: pitch")},{V("A")},0)),"Not checked")',
     'Open slots': f'=IFERROR(INDEX({V("F")},MATCH({ref("Lead with: pitch")},{V("A")},0)),0)',
     'Lead with: slot': f'=IFERROR(INDEX({V("M")},MATCH({ref("Lead with: pitch")},{V("A")},0)),"")',
     'Lead with: format': f'=IFERROR(INDEX({V("N")},MATCH({ref("Lead with: pitch")},{V("A")},0)),"5-a-side")',
     'Price per player (£)': f'=IF({PRICE}="","",{PRICE})',
    }
    SL_, VN_, FM_, PR_, WK_ = ref('Lead with: slot'), ref('Lead with: pitch'), ref('Lead with: format'), ref('Price per player (£)'), ref('Walk to it (min)')
    CO_, FN_, OW_, PC_ = ref('Name for messages'), ref('Contact first name'), ref('Owner'), ref('Postcode')
    has_slot = f'ISNUMBER({SL_})'
    price = f'IF({PR_}<>"","£"&IF({PR_}=INT({PR_}),TEXT({PR_},"0"),TEXT({PR_},"0.00")),"[PRICE PER PLAYER]")'
    sender = f'IF({OW_}<>"",{OW_},IF({SENDER}<>"",{SENDER},"[NAME]"))'
    hi = f'"Hi "&IF({FN_}<>"",{FN_},{CO_}&" team")&","'
    row['Send to'] = f'=IF({ref("Direct email")}<>"",{ref("Direct email")},IF({ref("Email")}<>"",{ref("Email")},""))'
    when_long = f'IF({has_slot},"on "&TEXT({SL_},"dddd d mmmm")&" at "&TEXT({SL_},"hh:mm"),"on a weekday evening that suits your team")'
    when_short = f'IF({has_slot},TEXT({SL_},"ddd d mmm")&", "&TEXT({SL_},"hh:mm"),"weekday evenings")'
    jl = f'IF({JLINK}<>"",{JLINK},"[JOINING LINK]")'
    AR_ = ref('Area'); place = f'IF({AR_}="Canary Wharf","Canary Wharf","City")'
    a_walk = f'IF(OR({WK_}=8,{WK_}=11,{WK_}=18),"an ","a ")'
    a_co = f'IF(ISNUMBER(SEARCH(LEFT({CO_},1),"AEIOU")),"an ","a ")'
    dl = f'IF({DEADLINE}<>""," Spots are held until "&TEXT({DEADLINE},"dddd d mmmm")&".","")'
    row['Lead-with line'] = (f'={VN_}&" ("&{WK_}&" min walk) · "&IF({has_slot},TEXT({SL_},"ddd d mmm, hh:mm"),"slot to confirm with venue")'
                             f'&" · "&{FM_}&" · "&IF({PR_}<>"","£"&TEXT({PR_},"0.00")&" pp","price TBC")')
    row['Subject'] = f'="After-work football for "&{CO_}&" · "&{VN_}&", "&{WK_}&" min from your office"'
    row['Email draft'] = (
        f'={hi}&{NL}&{NL}'
        f'&"I\'m "&{sender}&" from FC Urban. We organise after-work football for teams in the City and Canary Wharf."&{NL}&{NL}'
        f'&"We have a "&{FM_}&" pitch at "&{VN_}&", "&{a_walk}&{WK_}&"-minute walk from your "&{PC_}&" office, "&{when_long}&". '
        f'It\'s "&{price}&" a player and we handle the pitch booking, sign-ups and payments, so all it takes is one person sharing a link with the team."&{NL}&{NL}'
        f'&"It works well as a team social or "&{a_co}&{CO_}&" vs clients game. Would your team be up for it, or is there someone who\'d enjoy organising it?"&{dl}&" "&{jl}&{NL}&{NL}'
        f'&"Best,"&{NL}&{sender}&{NL}&"FC Urban"')
    row['Follow-up email (day 4)'] = (
        f'={hi}&{NL}&{NL}&"Just bumping this up. The "&{FM_}&" pitch at "&{VN_}&" is still free "&{when_short}&", "&{a_walk}&{WK_}&"-minute walk from your office, "'
        f'&{price}&" a player. Happy to hold it for "&{CO_}&" if someone on the team fancies organising a game."&{dl}&" "&{jl}&{NL}&{NL}&"Best,"&{NL}&{sender}&{NL}&"FC Urban"')
    row['Draft status'] = (f'=IF({ref("Send to")}="","No email yet",IF(ISNUMBER(SEARCH("[",{ref("Email draft")})),"Fill placeholders",'
                           f'IF({has_slot},"Ready to send","Ready · no fixed slot")))')
    for h, v in row.items():
        c = wo.cell(row=n, column=ci[h], value=v); c.border = box; c.alignment = top
        c.font = green if isinstance(v, str) and v.startswith('=') else fnt
    wo.cell(row=n, column=ci['Lead with: slot']).number_format = DT
    wo.cell(row=n, column=ci['Incorporated']).number_format = 'd mmm yyyy'
    wo.cell(row=n, column=ci['Price per player (£)']).number_format = GBP
    wo.cell(row=n, column=ci['Contacted on']).number_format = D
    if r['Companies House link']:
        c = wo.cell(row=n, column=ci['Companies House']); c.hyperlink = r['Companies House link']; c.font = link
    e = emails.get(r['Company name'], {})
    if e.get('website', '').startswith('http'): c = wo.cell(row=n, column=ci['Website']); c.hyperlink = e['website']; c.font = link
    if e.get('source', '').startswith('http'): c = wo.cell(row=n, column=ci['Email source']); c.hyperlink = e['source']; c.font = link
last = len(corps) + 2
def dv(h, opts):
    d = DataValidation(type='list', formula1='"' + ','.join(opts) + '"', allow_blank=True)
    wo.add_data_validation(d); d.add(f'{C(h)}3:{C(h)}{MAXR}')
dv('Owner', ['Brian', 'Joep', 'Luuk', 'Stan', 'Nero', 'Nicky'])
dv('Channel', ['Email', 'Phone', 'Walk-in', 'Other'])
for h in ('Replied', 'Call booked', 'Group created', 'First game booked', 'Second game booked'): dv(h, ['Yes', 'No'])
dd = DataValidation(type='date', allow_blank=True); wo.add_data_validation(dd)
for h in ('Contacted on', 'Follow-up sent on'): dd.add(f'{C(h)}3:{C(h)}{MAXR}'); [setattr(wo.cell(row=k, column=ci[h]), 'number_format', D) for k in range(3, last + 1)]
wo.freeze_panes = f'{C("Name for messages")}3'
wo.auto_filter.ref = f'A2:{L(len(H))}{last}'
wo.cell(row=2, column=ci['Priority']).comment = Comment('1 = target sector (law, bank, public bank, private bank, fund admin) with group/large accounts. 2 = target sector, or any sector with group accounts. 3 = fund managers / insurers / advisory with full accounts.', 'FC Urban')
wo.cell(row=2, column=ci['Lead with: pitch']).comment = Comment('Nearest pitch within 19 min that had open after-work slots when checked; otherwise the nearest pitch. Change the slot for all companies at once on Venues › Chosen slot (override).', 'FC Urban')
wo.cell(row=2, column=ci['In 933 research list?']).comment = Comment('Yes = the company also appears in the earlier 933-company City research list, which was never messaged. It is not in the top-100 (Joep), the 117 LinkedIn list, the Haggerston leads or the FC Urban London sheet.', 'FC Urban')
wo.cell(row=2, column=ci['Walk (min)']).comment = Comment('Straight-line distance × 1.3 for streets, at 4.8 km/h. From the registered office postcode.', 'FC Urban')

for i in range(2, nV + 2):
    wv.cell(row=i, column=23, value=f"=COUNTIF(Outreach!${C('Nearest pitch')}$3:${C('Nearest pitch')}${MAXR},A{i})").font = green
    wv.cell(row=i, column=24, value=f"=COUNTIF(Outreach!${C('Lead with: pitch')}$3:${C('Lead with: pitch')}${MAXR},A{i})").font = green

# ================= Totals =================
wt = wb.create_sheet('Totals')
wt['A1'] = 'Totals'; wt['A1'].font = title
O = lambda h: f"Outreach!${C(h)}$3:${C(h)}${MAXR}"
r = 3
def block(title_, labels, fn, hdrs=('', 'Companies')):
    global r
    wt.cell(row=r, column=1, value=title_).font = bold; r += 1
    for j, h in enumerate(hdrs, 1): c = wt.cell(row=r, column=j, value=h); c.font = white; c.fill = HDR
    r += 1; first = r
    for lab in labels:
        wt.cell(row=r, column=1, value=lab).font = fnt
        for j, f in enumerate(fn(r), 2): wt.cell(row=r, column=j, value=f).font = fnt
        r += 1
    wt.cell(row=r, column=1, value='Total').font = bold
    for j in range(2, len(hdrs)+1): wt.cell(row=r, column=j, value=f'=SUM({L(j)}{first}:{L(j)}{r-1})').font = bold
    r += 2
SEGS = ['Law firm', 'Bank', 'Public / state-owned bank', 'Private bank', 'Fund administrator', 'Fund / asset manager', 'Insurance / broker', 'Advisory / accountancy']
block('Companies by segment and area', SEGS,
      lambda rr: [f'=COUNTIFS({O("Segment")},$A{rr},{O("Area")},"City of London")', f'=COUNTIFS({O("Segment")},$A{rr},{O("Area")},"Canary Wharf")',
                  f'=COUNTIF({O("Segment")},$A{rr})'], ('Segment', 'City of London', 'Canary Wharf', 'Total'))
block('Companies by priority', [1, 2, 3], lambda rr: [f'=COUNTIF({O("Priority")},A{rr})'])
block('Email found', ['general', 'role (other)', 'named person', 'privacy / compliance', 'Not found'], lambda rr: [f'=COUNTIF({O("Email type")},A{rr})'])
block('Companies by lead-with pitch', [v['venue'] for v in venues], lambda rr: [f'=COUNTIF({O("Lead with: pitch")},A{rr})'])
STAGES = [('Contacted', 'Contacted on', '>0'), ('Follow-up sent', 'Follow-up sent on', '>0'), ('Replied', 'Replied', 'Yes'),
          ('Call booked', 'Call booked', 'Yes'), ('Group created', 'Group created', 'Yes'), ('First game booked', 'First game booked', 'Yes'),
          ('Second game booked', 'Second game booked', 'Yes')]
wt.cell(row=r, column=1, value='Funnel (from the Tracking columns on Outreach)').font = bold; r += 1
for j, h in enumerate(['Stage', 'Companies', '% of contacted'], 1): c = wt.cell(row=r, column=j, value=h); c.font = white; c.fill = HDR
r += 1; f0 = r
for lab, col, crit in STAGES:
    wt.cell(row=r, column=1, value=lab).font = fnt
    wt.cell(row=r, column=2, value=f'=COUNTIF({O(col)},"{crit}")').font = fnt
    c = wt.cell(row=r, column=3, value=f'=IF($B${f0}=0,"",B{r}/$B${f0})'); c.number_format = '0.0%'; c.font = fnt
    r += 1
r += 2
wt.cell(row=r, column=1, value='Funnel by segment').font = bold; r += 1
for j, h in enumerate(['Segment'] + [s[0] for s in STAGES], 1): c = wt.cell(row=r, column=j, value=h); c.font = white; c.fill = HDR
r += 1
for sname in SEGS:
    wt.cell(row=r, column=1, value=sname).font = fnt
    for j, (lab, col, crit) in enumerate(STAGES, 2):
        wt.cell(row=r, column=j, value=f'=COUNTIFS({O("Segment")},$A{r},{O(col)},"{crit}")').font = fnt
    r += 1
r += 2
wt.cell(row=r, column=1, value='Open after-work slots by venue and weekday').font = bold; r += 1
days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
for j, h in enumerate(['Venue'] + days + ['Total'], 1): c = wt.cell(row=r, column=j, value=h); c.font = white; c.fill = HDR
r += 1; s0 = r
for v in venues:
    wt.cell(row=r, column=1, value=v['venue']).font = fnt
    for j, d in enumerate(days, 2):
        wt.cell(row=r, column=j, value=f'=COUNTIFS({srng("A")},$A{r},{srng("C")},"{d}",{srng("I")},"Available")').font = fnt
    wt.cell(row=r, column=7, value=f'=SUM(B{r}:F{r})').font = bold; r += 1
wt.cell(row=r, column=1, value='Total').font = bold
for j in range(2, 8): wt.cell(row=r, column=j, value=f'=SUM({L(j)}{s0}:{L(j)}{r-1})').font = bold
wt.column_dimensions['A'].width = 40
for j in range(2, 10): wt.column_dimensions[L(j)].width = 14

# ================= Read me =================
wr = wb.create_sheet('Read me')
nfc = sum(1 for v in venues if v['kind'] == 'FC Urban venue')
lines = [
 ('FC Urban · City of London & Canary Wharf corporates', title),
 (f'{len(corps)} companies (law firms, banks, public/state-owned banks, private banks, fund administrators, then fund managers and insurers) '
  'within a 19-minute walk of a pitch. Each row leads with a specific pitch, slot and price per player.', fnt),
 ('', fnt),
 ('Tabs', bold),
 ('Outreach — one row per company with its website and a published contact email (Email source links to the page it came from). Send to = Direct email if you add one, else Email. Send the Email draft, then the Follow-up email after 4 days; log the Tracking columns.', fnt),
 ('Offer — price per player, default sender, joining link and commit deadline. These feed every draft.', fnt),
 (f'Venues — {len(venues)} pitches ({nfc} FC Urban venues + others found nearby): open slots, earliest slot, cost per player, who to call. '
  'Put a confirmed slot in Chosen slot (override) and every draft for that pitch uses it.', fnt),
 ('Slots — every open after-work slot found (weekdays, 17:30–20:30 kick-off, 28 Sep – 23 Oct 2026).', fnt),
 ('Totals — companies by segment, area, priority and pitch; the outreach funnel; slots by weekday.', fnt),
 ('', fnt),
 ('Colours', bold),
 ('Yellow = fill in. Blue text = values typed from a source. Green text = formulas; leave those alone.', fnt),
 ('', fnt),
 ('How the list was built', bold),
 ('1. Companies House bulk data (September 2026), active companies registered in EC1–EC4, E1, E1W, E14, SE1, WC1 and WC2.', fnt),
 ('2. Kept sectors by SIC code: legal (69101/69102/69109), banks (64110/64191/64192), fund management and admin (66300, 64301–64306, 66190), insurance (65110–65300, 66220), plus LLPs identified by name.', fnt),
 ('3. Kept only companies that file full, group or medium-sized accounts (no micro or small-company filers), so they can afford a team game.', fnt),
 ('4. Removed shells and vehicles (holdco/bidco/topco, nominees, trustees, funding/issuer SPVs, numbered funds, investment trusts, VCTs, Lloyd\'s corporate members) and formation-agent addresses (more than 12 unrelated brands at one address).', fnt),
 ('5. One row per company group: foreign-practice LLPs and subsidiaries collapse into the main entity (Group entities collapsed in the CSV).', fnt),
 ('6. No duplicates: removed anything already in the FC Urban London sheet, the City finance top 100 (Joep), the 117-company LinkedIn list or the Haggerston Park leads (matched on name and brand). '
  'Companies that are only in the earlier 933-company research list (never messaged) are kept and marked "In 933 research list? = Yes".', fnt),
 ('7. Geocoded each registered-office postcode (postcodes.io). Kept companies within 1.8 km of Bank or Canary Wharf and within a 19-minute walk of a pitch (straight line × 1.3, 4.8 km/h).', fnt),
 ('8. Picked all target-sector companies (law, banks, public banks, private banks, fund admin), then filled to 400 with fund managers, insurers and advisory firms, balanced between them, largest accounts and shortest walk first.', fnt),
 ('', fnt),
 ('9. Only companies with a pitch that has a confirmed open after-work slot within 19 minutes. No Canary Wharf pitch had one (all enquiry-only), so this list is City-only; Canary Wharf firms can be added once Poplar / George Green\'s / Westferry confirm a slot.', fnt),
 ('10. Emails: scraped from each firm\'s own website (contact / office pages), then a web search for the rest; every address was checked against the firm\'s own domain. Where two sources existed, a general inbox beat a named person.', fnt),
 ('', fnt),
 ('Caveats', bold),
 ('Registered office ≠ always the working office (some firms register at their accountant or lawyer). Check the walk time before you send.', fnt),
 ('Emails were taken only from each firm\'s own website or an official register (never guessed). Most are general inboxes (info@, enquiries@); "named person" means a published address of a specific person; "privacy / compliance" is a last resort — swap in a better one if you find it.', fnt),
 ('Better (GLL) venues release slots about 6 days ahead, and school pitches are often enquiry-only: those show as Contact required. Call, then put the agreed slot in Venues › Chosen slot (override).', fnt),
 ('Bank of England is a statutory body, not on Companies House; it was added by hand. Public / state-owned banks are those owned by a government (e.g. Indian, Korean, Chinese and Ghanaian state banks).', fnt),
]
for k, (t, f_) in enumerate(lines, 1):
    c = wr.cell(row=k, column=1, value=t); c.font = f_
wr.column_dimensions['A'].width = 160

wb.move_sheet('Offer', offset=-(wb.sheetnames.index('Offer') - 1))
wb.save(OUT)
print('saved', OUT, '| sheets:', wb.sheetnames, '| rows:', len(corps), '| venues:', nV, '| slots:', len(slots))
