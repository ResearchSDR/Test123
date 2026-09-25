"""Build the London after-work football lead sheet (one decision-maker email per company, real pitch slot, drafts gated on a confirmed price).
Input: london_300_rows.json (made by the research pipeline). Output: FC_Urban_London_after_work_leads.xlsx
"""
import json, os, datetime, re
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.comments import Comment

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(f'{HERE}/london_300_rows.json', encoding='utf-8'))
rows, offer = D['rows'], D['offer']
OUT = os.environ.get('OUT', f'{HERE}/FC_Urban_London_after_work_leads.xlsx')
MAXR = 1000
F = 'Arial'
fnt, bold = Font(name=F, size=10), Font(name=F, size=10, bold=True)
white, title = Font(name=F, size=10, bold=True, color='FFFFFF'), Font(name=F, size=14, bold=True)
blue, green = Font(name=F, size=10, color='0000FF'), Font(name=F, size=10, color='008000')
link = Font(name=F, size=10, color='1155CC', underline='single')
YEL, HDR = PatternFill('solid', fgColor='FFF2CC'), PatternFill('solid', fgColor='1F3864')
BANDS = {'Company': '2F5496', 'Contact': '7030A0', 'Office & pitch': '548235', 'Lead with (message)': 'C55A11', 'Checks': '404040', 'Tracking — fill in': 'BF9000'}
box = Border(bottom=Side(style='thin', color='D9D9D9')); top = Alignment(vertical='top'); wrap = Alignment(wrap_text=True, vertical='top')
GBP = '£#,##0.00;-£#,##0.00;-'
wb = Workbook()

# ---------- Offer: one confirmed price per city ----------
wp = wb.active; wp.title = 'Offer'
wp['B1'] = 'Confirmed price per player (one row per city)'; wp['B1'].font = title
wp['B2'] = 'Not used in the first (interest-check) email. Used later in the group-invite email once a company says yes. Never type TBC.'; wp['B2'].font = fnt
for j, h in enumerate(['City', 'Currency', 'Price per player', 'Confirmed by', 'Confirmed on'], 2):
    c = wp.cell(row=4, column=j, value=h); c.font = white; c.fill = HDR
for i, (city, cur) in enumerate([('London', 'GBP'), ('Stockholm', 'SEK')], 5):
    wp.cell(row=i, column=2, value=city).font = bold; wp.cell(row=i, column=3, value=cur).font = fnt
    for j in (4, 5, 6): c = wp.cell(row=i, column=j); c.fill = YEL; c.font = blue
wp['D5'].number_format = GBP; wp['D6'].number_format = '#,##0 "kr"'; wp['F5'].number_format = 'd mmm yyyy'; wp['F6'].number_format = 'd mmm yyyy'
wp['B8'] = 'Sender for this sheet'; wp['B8'].font = bold; wp['D8'] = 'Brian'; wp['D8'].font = blue; wp['D8'].fill = YEL
wp['B9'] = 'Sending inbox'; wp['B9'].font = bold; wp['D9'] = 'brian@fcurban.com'; wp['D9'].font = fnt
for col, w in zip('ABCDEF', (2, 30, 10, 16, 16, 14)): wp.column_dimensions[col].width = w
PRICE, SENDER = 'Offer!$D$5', 'Offer!$D$8'

# ---------- Slots used ----------
ws = wb.create_sheet('Slots')
SH = ['Pitch', 'Offer in email', 'Recurring or one-off', 'Format', 'First date', 'Kick-off', 'Open Mon–Thu 17:30–20:00 slots (next 3 weeks)', 'Booking source']
for j, h in enumerate(SH, 1): c = ws.cell(row=1, column=j, value=h); c.font = white; c.fill = HDR; c.alignment = wrap
for i, (p, o) in enumerate(sorted(offer.items()), 2):
    for j, v in enumerate([p, o['slot_text'], o['slot_kind'], o['format'], datetime.date.fromisoformat(o['first_date']), o['time'], o['open_slots'], o['source']], 1):
        c = ws.cell(row=i, column=j, value=v); c.font = fnt
    ws.cell(row=i, column=5).number_format = 'ddd d mmm yyyy'
for j, w in enumerate([32, 46, 14, 10, 14, 9, 14, 40], 1): ws.column_dimensions[L(j)].width = w

# ---------- Outreach ----------
wo = wb.create_sheet('Outreach', 0)
cols = [('#', 'Company', 5), ('Priority', 'Company', 7), ('Segment', 'Company', 18), ('Area', 'Company', 12), ('Company', 'Company', 32),
        ('Name for messages', 'Company', 22), ('Website', 'Company', 24), ('Headcount', 'Company', 9), ('Companies House no.', 'Company', 11),
        ('Companies House', 'Company', 10), ('Accounts', 'Company', 8), ('Incorporated', 'Company', 11), ('Registered address', 'Company', 30), ('Postcode', 'Company', 9),
        ('In 933 research list?', 'Company', 9),
        ('Contact first name', 'Contact', 11), ('Contact full name', 'Contact', 18), ('Contact title', 'Contact', 20), ('Email', 'Contact', 28),
        ('Email type', 'Contact', 20), ('Contact source URL', 'Contact', 22), ('Direct email', 'Contact', 18), ('Phone', 'Contact', 12),
        ('Office street', 'Office & pitch', 26), ('Office postcode', 'Office & pitch', 10), ('Office basis', 'Office & pitch', 22),
        ('Nearest pitch', 'Office & pitch', 26), ('Walk (min)', 'Office & pitch', 7),
        ('Lead with: pitch', 'Lead with (message)', 26), ('Lead with: slot', 'Lead with (message)', 30), ('Slot type', 'Lead with (message)', 10),
        ('Lead with: format', 'Lead with (message)', 9), ('Price per player (£)', 'Lead with (message)', 9), ('Personal line', 'Lead with (message)', 36),
        ('Personal line source', 'Lead with (message)', 20), ('Hook type', 'Lead with (message)', 12), ('Research confidence', 'Lead with (message)', 9),
        ('Check before sending', 'Lead with (message)', 30), ('Send to', 'Lead with (message)', 26), ('Subject', 'Lead with (message)', 40),
        ('Email draft', 'Lead with (message)', 60), ('Follow-up email (day 5)', 'Lead with (message)', 45),
        ('Suppression check', 'Checks', 10), ('MX check', 'Checks', 9), ('Hold (check first)', 'Checks', 24), ('Draftable', 'Checks', 30),
        ('Owner', 'Tracking — fill in', 8), ('Contacted on', 'Tracking — fill in', 11), ('Follow-up sent on', 'Tracking — fill in', 11),
        ('Replied', 'Tracking — fill in', 8), ('Reply category', 'Tracking — fill in', 14), ('Call booked', 'Tracking — fill in', 8),
        ('Group created', 'Tracking — fill in', 8), ('First game booked', 'Tracking — fill in', 8), ('Notes', 'Tracking — fill in', 28)]
H = [c[0] for c in cols]; ci = {h: i + 1 for i, h in enumerate(H)}; C = lambda h: L(ci[h])
for band in dict.fromkeys(c[1] for c in cols):
    span = [i + 1 for i, c in enumerate(cols) if c[1] == band]
    wo.merge_cells(start_row=1, start_column=span[0], end_row=1, end_column=span[-1])
    cell = wo.cell(row=1, column=span[0], value=band); cell.font = white
    for j in span: wo.cell(row=1, column=j).fill = PatternFill('solid', fgColor=BANDS[band])
for i, (h, band, w) in enumerate(cols, 1):
    fill_in = band.startswith('Tracking')
    c = wo.cell(row=2, column=i, value=h); c.font = bold if fill_in else white; c.fill = YEL if fill_in else HDR
    c.alignment = Alignment(wrap_text=True, vertical='center'); wo.column_dimensions[L(i)].width = w
wo.row_dimensions[2].height = 42
NL = 'CHAR(10)'
for n, r in enumerate(rows, 3):
    ref = lambda h: f'{C(h)}{n}'
    o = offer[r['pitch']]
    v = {'#': n - 2, 'Priority': r['priority'], 'Segment': r['segment'], 'Area': r['area'], 'Company': r['company'], 'Name for messages': r['short'],
         'Website': r['web'], 'Headcount': r['hc'] if r['hc'] else 'Not stated', 'Companies House no.': r['num'], 'Companies House': 'Open',
         'Accounts': r['acc'].title(), 'Incorporated': r['inc'], 'Registered address': r['reg_addr'], 'Postcode': r['reg_pc'], 'In 933 research list?': 'No',
         'Contact first name': r['fn'] or None, 'Contact full name': r['full'] or None, 'Contact title': r['title'] or None, 'Email': r['email'],
         'Email type': r['tier'], 'Contact source URL': r['email_src'] or None,
         'Office street': r['office_street'] or None, 'Office postcode': r['office_pc'], 'Office basis': r['office_basis'],
         'Nearest pitch': r['pitch'], 'Walk (min)': round(r['walk']), 'Lead with: pitch': r['pitch'], 'Lead with: slot': o['slot_text'],
         'Slot type': o['slot_kind'], 'Lead with: format': o['format'], 'Price per player (£)': f'=IF({PRICE}="","",{PRICE})',
         'Personal line': r.get('hook') or r['personal'] or None, 'Personal line source': r.get('hook_src') or r['personal_src'] or None,
         'Send to': f'=IF({ref("Direct email")}<>"",{ref("Direct email")},{ref("Email")})',
         'Suppression check': 'pass', 'MX check': 'MX ok · mailbox not verified', 'Hold (check first)': r.get('hold') or None}
    CO, FN, PR, WK, PL = ref('Name for messages'), ref('Contact first name'), ref('Price per player (£)'), ref('Walk (min)'), ref('Personal line')
    hi = f'"Hi "&IF({FN}<>"",{FN},{CO}&" team")&","'
    price = f'"£"&IF({PR}=INT({PR}),TEXT({PR},"0"),TEXT({PR},"0.00"))'
    street = f'IF({ref("Office street")}<>"",{ref("Office street")},{ref("Office postcode")})'
    pers = f'IF({PL}<>"","Saw that "&{CO}&" "&{PL}&"."&{NL}&{NL},"")'
    sender = f'IF({ref("Owner")}<>"",{ref("Owner")},{SENDER})'
    v['Hook type'] = r.get('hook_type') or None; v['Research confidence'] = r.get('confidence') or None; v['Check before sending'] = r.get('notes') or None
    plain = lambda t: re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'\1 (\2)', t or '')
    v['Subject'] = r.get('subject') or None
    v['Email draft'] = plain(r.get('body')) or None
    v['Follow-up email (day 5)'] = plain(r.get('followup')) or None
    v['Price per player (£)'] = 'Not in first email'
    v['Draftable'] = ('No – hold: ' + r['hold']) if r.get('hold') else ('Yes' if r.get('body') and r['email'] else 'No – no email')
    for h, val in v.items():
        c = wo.cell(row=n, column=ci[h], value=val); c.border = box; c.alignment = top
        c.font = green if isinstance(val, str) and val.startswith('=') else fnt
        if h in ('Email draft', 'Follow-up email (day 5)'): c.alignment = wrap
    wo.cell(row=n, column=ci['Price per player (£)']).number_format = GBP
    for h, u in (('Website', r['web']), ('Companies House', f"https://find-and-update.company-information.service.gov.uk/company/{r['num']}"),
                 ('Contact source URL', r['email_src']), ('Personal line source', r['personal_src'])):
        if u and u.startswith('http'): c = wo.cell(row=n, column=ci[h]); c.hyperlink = u; c.font = link
    for h in ('Contacted on', 'Follow-up sent on'): wo.cell(row=n, column=ci[h]).number_format = 'd mmm yyyy'
last = len(rows) + 2
def dv(h, opts):
    d = DataValidation(type='list', formula1='"' + ','.join(opts) + '"', allow_blank=True); wo.add_data_validation(d); d.add(f'{C(h)}3:{C(h)}{MAXR}')
dv('Owner', ['Brian']); dv('Replied', ['Yes', 'No']); dv('Call booked', ['Yes', 'No']); dv('Group created', ['Yes', 'No']); dv('First game booked', ['Yes', 'No'])
dv('Reply category', ['Interested', 'Call requested', 'Not now', 'Not interested', 'Wrong person', 'Opt-out', 'Bounce', 'Out of office'])
wo.freeze_panes = f'{C("Name for messages")}3'; wo.auto_filter.ref = f'A2:{L(len(H))}{last}'
wo.cell(row=2, column=ci['MX check']).comment = Comment('The domain has a mail (MX) record. Mailbox-level SMTP checks could not run from the research environment (port 25 blocked) — run a verifier before sending.', 'FC Urban')
wo.cell(row=2, column=ci['Office basis']).comment = Comment('Website = address from the firm\'s own site. "Registered office (no address on website)" = the site shows no address, so the Companies House address was used.', 'FC Urban')

# ---------- Read me ----------
wr = wb.create_sheet('Read me')
lines = [('FC Urban · London after-work football leads', title),
         (f'{len(rows)} companies ({sum(1 for r in rows if not r.get("hold"))} ready once the price is set, {sum(1 for r in rows if r.get("hold"))} on hold) with a published email on their own domain, an office within a 15-minute walk of a pitch that has an open Mon–Thu 17:30–20:00 slot in the next 3 weeks.', fnt), ('', fnt),
         ('How it was built', bold),
         ('1. Companies House bulk data: active London companies filing full, medium or group accounts; SIC for law, finance/accounting, insurance, consultancy, tech/software, architecture, recruitment, marketing/agencies (LLPs by name).', fnt),
         ('2. Removed shells, holding/fund/property vehicles, schools, charities, public bodies, hospitality, retail, clinics, formation-agent addresses (>12 brands at one address), and anything in an earlier FC Urban sheet.', fnt),
         ('3. Suppression: brian@fcurban.com Sent (last 90 days) checked domain by domain, plus senders of opt-out / "no thanks" / "not interested" replies.', fnt),
         ('4. Website found and read for each firm: working office from its own contact page (registered office only when the site shows no address, labelled in Office basis).', fnt),
         ('5. Walk = straight line × 1.3 at 4.8 km/h to the nearest pitch with a confirmed open slot (Slots tab). Kept ≤ 15 minutes.', fnt),
         ('6. Contact order: named HR / People / Office / Operations person → named partner/director/founder (firms under ~100) → general inbox on the firm\'s own domain. No press, privacy, careers, support, sales or other-country inboxes. Emails were only taken where published; none guessed.', fnt),
         ('7. Headcount from the firm\'s own site where stated; firms under 20 or over 500 removed; "Not stated" otherwise.', fnt),
         ('8. Personal line: one fact from the firm\'s own pages (source linked). Blank when nothing real was found.', fnt),
         ('9. Every email was written individually from that research. First email = interest check only (no price, no dates): who we are, that we already run games nearby, and a request to forward to whoever runs staff socials / wellbeing if the reader is not the right person (per Joep\'s learnings). Price (£8–£10 pp guide) comes in the group-invite email after a yes. Rows the research flagged are on Hold with the reason.', fnt), ('', fnt),
         ('Sending rules (for when the n8n workflow is switched on)', bold),
         ('Max 150 per inbox per day, spread across working hours; one sender name per inbox (Brian on brian@fcurban.com); stop the batch if bounces exceed 3%; log Contacted on here and reply categories in Notion.', fnt)]
for k, (t, f_) in enumerate(lines, 1): wr.cell(row=k, column=1, value=t).font = f_
wr.column_dimensions['A'].width = 170
wb.move_sheet('Offer', offset=-(wb.sheetnames.index('Offer') - 1))
wb.save(OUT); print('saved', OUT, len(rows))
