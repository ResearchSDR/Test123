"""Compose FC Urban outreach emails from researched rows and run the QA gate.

Venue rule: claim "we already run games at <venue>" only when the nearest LIVE venue
(pipeline/venues_live.json, scraped from fcurban.com that morning) is within 15 minutes'
walk of the working office. Otherwise use the "opening new weekly games near your office"
variant, which makes no venue claim and carries no link.

Walk time: straight line x 1.3 at 4.8 km/h (80 m per minute), office postcode via postcodes.io.
"""
import json, re, math, hashlib, html, subprocess

LABEL = {
    'acton': 'Club Des Sports in Acton', 'bermondsey': 'our Bermondsey pitch on Lynton Road',
    'borough-academy': 'Borough Academy', 'brixton-03dac': 'our Brixton pitch on Nursery Road',
    'chelsea': 'our Chelsea pitch on Sydney Street', 'docklands-surrey-quays': 'our Surrey Quays pitch on Salter Road',
    'hackney': 'our Hackney pitch on Homerton High Street', 'hampstead-3g': 'Hampstead 3G on Fleet Road',
    'kennington': 'our Kennington pitch on Hackford Road', 'old-st-moreland-primary-school': 'Moreland School on Gard Street',
    'poplar': 'our Poplar pitch on Poplar High Street', 'shoreditch-rooftop': 'our Shoreditch rooftop pitch on Pitfield Street',
    'south-kensington': 'our South Kensington pitch on Thomas More Walk', 'st-johns-wood': "our St John's Wood pitch on Finchley Road",
    'whitechapel': 'our Whitechapel pitch on Richard Street', 'whittington-park': 'Whittington Park',
}
# Venue postcodes that postcodes.io has retired (coordinates from its terminated_postcodes endpoint).
TERMINATED = {'E1 2JR': (51.514494, -0.059625)}
# Weekend-only venues are no use for an after-work pitch.
AFTER_WORK_ONLY = True
MAX_WALK = 15
BANNED_LOCAL = re.compile(r'^(press|media|pr|careers?|jobs|recruit\w*|talent|compliance|complaints?|support|help\w*|customer\w*|service|ir|investor\w*|brand\w*|marketing|privacy|gdpr|dpo|legal|accounts?|billing|noreply|no-reply|sales)$', re.I)
US_UK = {'organize': 'organise', 'organization': 'organisation', 'organizing': 'organising', 'color': 'colour', 'favorite': 'favourite',
         'center': 'centre', 'honor': 'honour', 'recognized': 'recognised', 'recognize': 'recognise', 'realize': 'realise', 'analyze': 'analyse',
         'celebrating': None, 'launched': None, 'specialized': 'specialised', 'program ': 'programme ', 'labor': 'labour', 'neighborhood': 'neighbourhood',
         'traveled': 'travelled', 'modeling': 'modelling', 'catalog': 'catalogue', 'defense': 'defence', 'license ': 'licence '}

def hav(a, b, c, d):
    R = 6371000; p1, p2 = math.radians(a), math.radians(c); dl = math.radians(d - b); dp = p2 - p1
    return 2 * R * math.asin(math.sqrt(math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2))

def geocode(pcs):
    out = {}; pcs = sorted({p.upper().strip() for p in pcs if p})
    for i in range(0, len(pcs), 100):
        r = subprocess.run(['curl', '-sS', '--max-time', '60', '-X', 'POST', 'https://api.postcodes.io/postcodes', '-H', 'Content-Type: application/json',
                            '-d', json.dumps({'postcodes': pcs[i:i + 100]})], capture_output=True, text=True).stdout
        for q in json.loads(r)['result']:
            if q['result']: out[q['query'].upper()] = (q['result']['latitude'], q['result']['longitude'], q['result']['postcode'], q['result'].get('outcode'))
    return out

def live_venues(venues_live_path, weekday_evening_only=AFTER_WORK_ONLY):
    d = json.load(open(venues_live_path))
    vs = [v for v in d['venues'] if v['live'] and v['slug'] in LABEL]
    if weekday_evening_only:
        vs = [v for v in vs if any(p[:3] in ('Mon', 'Tue', 'Wed', 'Thu', 'Fri') and int(p[4:6]) >= 17 for p in v['weekly_pattern'])]
    g = geocode([v['postcode'] for v in vs])
    g.update({k: v for k, v in TERMINATED.items() if k not in g})
    for v in vs: v['lat'], v['lon'] = g[v['postcode'].upper()][:2]
    return vs

def an(n): return 'an' if n in (8, 11, 18) else 'a'

def subject_for(brand, street, key):
    h = int(hashlib.md5(key.encode()).hexdigest(), 16) % 3
    if h == 1 and street and not re.match(r'^\d', street) and len(street) < 30: return f'Football near your {street} office'
    if h == 2: return f'A weekly kickabout for {brand}?'
    return f'Weekly football for the {brand} team'

def undash(t):
    t = (t or '').replace('—', ', ').replace('–', ' to ').replace(' - ', ', ').replace('‑', ' ')
    return re.sub(r'\s+,', ',', re.sub(r'\s{2,}', ' ', t)).strip()

def compose(row, venues, geo, slots):
    """row keys: brand, email, greeting_name, office_street, office_postcode, hook, source_url"""
    brand = undash(row['brand']); street = undash(row.get('office_street') or '')
    street = re.sub(r'^((\w+|\d+(st|nd|rd|th)) Floor|Level \d+|Suite \w+|Unit \w+),\s*', '', street, flags=re.I)
    g = geo.get((row.get('office_postcode') or '').upper().strip())
    venue, walk = None, None
    if g:
        walk, venue = min(((hav(g[0], g[1], v['lat'], v['lon']) * 1.3 / 80), v['slug']) for v in venues) if venues else (None, None)
        if walk is not None and walk > MAX_WALK: venue = None
    greet = f"Hi {row['greeting_name'].strip()}," if (row.get('greeting_name') or '').strip() else f'Hi {brand} team,'
    hook = undash(row.get('hook') or '') if row.get('source_url') else ''
    ROADS = r'(Street|St|Road|Rd|Lane|Walk|Row|Place|Yard|Terrace|Avenue|Way|Grove|Hill|Gardens|Crescent|Close|Mews|Wharf|Passage|Drive|Parade|Circus|Market)\.?$'
    on_ok = bool(re.search(ROADS, street)) and not re.match(r'^(\d|One |Unit|Suite|Floor|Level|The |[A-Z][a-z]+ (House|Building|Tower|Court|Works|Studios)\b)', street) and ',' not in street
    loc = (('on ' if on_ok else 'at ') + street) if street else 'nearby'
    paras = [greet] + ([hook] if hook else [])
    if venue:
        v = next(x for x in venues if x['slug'] == venue); wm = max(2, round(walk))
        url = f'https://www.fcurban.com/location/{venue}'
        paras.append(f"I'm Brian from FC Urban. We organise social football games across London, and we already run games at [[{LABEL[venue]}]], about {an(wm)} {wm} minute walk from your office {loc}.")
        if slots.get(venue): paras.append(f'We currently have space there on {slots[venue]}.')
    else:
        url, wm = '', None
        paras.append("I'm Brian from FC Urban. We organise social football games across London, and we're opening new weekly games near your office" + (f' {loc}.' if street else '.'))
    paras.append("We'd love to help start a regular after work game for the team. We handle the pitch, the organisation and the payments, and if a few people can't make it we fill the spare places with our own players.")
    paras.append("Would there be any interest? If it's not for you, would you mind forwarding this to whoever looks after staff socials or wellbeing?")
    paras.append('Best,\nBrian\nFC Urban')
    optout = 'Reply with "no thanks" and I won\'t contact you again.'
    body = '\n\n'.join(p.replace('[[', '').replace(']]', f' ({url})' if url else '') for p in paras) + '\n\n' + optout
    hp = []
    for p in paras:
        e = html.escape(p, quote=False).replace('\n', '<br>')
        if url: e = e.replace('[[', f'<a href="{url}">').replace(']]', '</a>')
        hp.append(f'<p>{e}</p>')
    hp.append(f'<p><span style="font-size:9pt;color:rgb(136,136,136)">{html.escape(optout, quote=False)}</span></p>')
    return {'subject': subject_for(brand, street, row['email']), 'body': body, 'htmlBody': '<div dir="ltr">' + ''.join(hp) + '</div>',
            'venue': venue or '', 'venue_label': LABEL.get(venue, '') if venue else '', 'venue_url': url, 'walk_min': wm,
            'variant': 'venue' if venue else 'opening_new', 'outcode': g[3] if g else ''}

def qa(row, msg, supp_domains, supp_addresses, live_slugs, seen_domains):
    fails = []
    email = row['email'].lower().strip(); dom = email.split('@')[-1]
    txt = msg['subject'] + '\n' + msg['body'] + '\n' + msg['htmlBody']
    if 'google.com/url' in txt: fails.append('wrapped link')
    if re.search(r'[\[\]{}<>]', msg['subject'] + msg['body'].replace(msg['venue_url'], '')) or re.search(r'\bTODO|XXX|\?\?', txt): fails.append('placeholder or bracket')
    if re.search('[–—]', txt): fails.append('en/em dash')
    words = len(msg['body'].replace(f" ({msg['venue_url']})", '').split('\n\nReply with')[0].split())
    msg['words'] = words
    if words >= 130: fails.append('130+ words')
    if email in supp_addresses or dom in supp_domains or any(dom.endswith('.' + d) for d in supp_domains): fails.append('suppressed')
    if dom in seen_domains: fails.append('duplicate domain today')
    if BANNED_LOCAL.match(email.split('@')[0]): fails.append('banned inbox type')
    if msg['variant'] == 'venue' and (msg['venue'] not in live_slugs or not msg['walk_min'] or msg['walk_min'] > MAX_WALK): fails.append('venue claim not live or >15 min')
    if (row.get('hook') or '').strip() and not (row.get('source_url') or '').strip(): fails.append('hook without source')
    low = ' ' + msg['body'].lower() + ' '
    for us, uk in US_UK.items():
        if uk and re.search(r'\b' + re.escape(us.strip()) + r'\b', low): fails.append(f'US spelling: {us.strip()}')
    return fails
