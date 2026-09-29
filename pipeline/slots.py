"""Slot line text per live venue: config/confirmed_slots.json first, else weekday evening games from the venue page."""
import json
DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
FULL = {'Mon': 'Mondays', 'Tue': 'Tuesdays', 'Wed': 'Wednesdays', 'Thu': 'Thursdays', 'Fri': 'Fridays'}
def join(xs): return xs[0] if len(xs) == 1 else ', '.join(xs[:-1]) + ' and ' + xs[-1]
def from_pattern(pattern):
    """Earliest weekday evening game per day; consecutive days with the same time are grouped
    ("Mondays to Thursdays at 19:30") so the line stays short."""
    first = {}
    for p in pattern:
        d, t = p[:3], p[4:]
        if d in DAYS and int(t[:2]) >= 17 and (d not in first or t < first[d]): first[d] = t
    if not first: return ''
    runs = []
    for d in DAYS:
        if d not in first: continue
        if runs and runs[-1][2] == first[d] and DAYS.index(d) == DAYS.index(runs[-1][1]) + 1: runs[-1][1] = d
        else: runs.append([d, d, first[d]])
    by_time = {}
    for a, b, t in runs: by_time.setdefault(t, []).append(FULL[a] if a == b else f"{FULL[a]} to {FULL[b]}")
    return join([f"{join(ds)} at {t}" for t, ds in by_time.items()])
def slot_lines(venues_live_path, confirmed_path):
    conf = {k: v for k, v in json.load(open(confirmed_path)).items() if not k.startswith('_')}
    out = {}
    for v in json.load(open(venues_live_path))['venues']:
        if not v['live']: continue
        out[v['slug']] = conf.get(v['slug']) or from_pattern(v['weekly_pattern'])
    return out
if __name__ == '__main__':
    for k, v in slot_lines('venues_live.json', 'config/confirmed_slots.json').items(): print(f'{k:35} {v}')
