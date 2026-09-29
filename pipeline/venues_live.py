"""Scrape every FC Urban London location page and record which venues have games in the next 14 days.

Liveness comes from the 'Next games' list on fcurban.com/location/<slug> (the 'Games we play weekly'
counter is filled in by JavaScript and reads 0 in the static HTML). Output: venues_live.json
"""
import json, re, html, sys, datetime, subprocess, math
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36'
def get(url):
    r = subprocess.run(['curl', '-sS', '-m', '25', '-A', UA, url], capture_output=True, text=True)
    return r.stdout
def text(h):
    h = re.sub(r'(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>', ' ', h)
    return html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', h)))
def london_slugs():
    sm = get('https://www.fcurban.com/sitemap.xml')
    locs = sorted(set(re.findall(r'https://www\.fcurban\.com/location/([a-z0-9\-]+)', sm)))
    return locs
MONTHS = {m: i for i, m in enumerate(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'], 1)}
def scrape(slug, today):
    t = text(get(f'https://www.fcurban.com/location/{slug}'))
    city = re.search(r'\b(London|Amsterdam|Stockholm|Munich|Rotterdam|Utrecht|The Hague|Barcelona|Madrid|Berlin|Brussels)\b', t)
    games = []
    for d, mon, hh, mm in re.findall(r'(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun) , (\d{1,2}) ([A-Z][a-z]{2}) (\d{2}):(\d{2})', t):
        y = today.year + (1 if MONTHS[mon] < today.month - 6 else 0)
        dt = datetime.datetime(y, MONTHS[mon], int(d), int(hh), int(mm))
        games.append(dt)
    games = sorted(set(games))
    soon = [g for g in games if 0 <= (g.date() - today).days <= 14]
    pcs = re.findall(r'\b((?:EC|WC)[1-4][A-Z]? ?\d[A-Z]{2}|(?:E|N|NW|SE|SW|W)\d{1,2}[A-Z]? ?\d[A-Z]{2})\b', t)
    return {'slug': slug, 'url': f'https://www.fcurban.com/location/{slug}', 'postcode': pcs[0] if pcs else '',
            'live': bool(soon), 'next_games': [g.strftime('%a %d %b %H:%M') for g in soon],
            'weekly_pattern': sorted({g.strftime('%a %H:%M') for g in soon}), 'is_london_text': 'London' in t}
if __name__ == '__main__':
    today = datetime.date.today()
    slugs = sys.argv[1:] or london_slugs()
    out = [scrape(s, today) for s in slugs]
    json.dump({'checked': str(today), 'venues': out}, open('venues_live.json', 'w'), indent=1)
    for v in out:
        print(f"{v['slug']:45} live={v['live']!s:5} {v['postcode']:9} {', '.join(v['weekly_pattern'])}")
