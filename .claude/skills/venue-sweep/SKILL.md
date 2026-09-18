---
name: venue-sweep
description: Find bookable pitch slots for a confirmed FC Urban group booking on hireapitch.com, in a real logged-in Chrome session. Use when a firm has said yes to playing and given a location, area, date window or preferred evening — including phrasings like "find us a pitch", "what's free near Old Street in October", "check availability for the 24th", "they want a Thursday", or when a reply to the outreach batch names a location and a date. Produces a shortlist of 3-5 bookable slots with price and cost per head, not a full calendar dump.
---

# Venue sweep

Turns "yes, we want to play, we're near <somewhere>" into three bookable options
the organiser can pick from in one reply.

This is the step after the outreach workflow in `n8n/` lands a positive reply.
Outreach is automated; this was not, and a manual sweep of three venues over
eight weeks costs ~40 screenshots and returns 170 rows nobody reads.

## Run it in Chrome. Not curl, not n8n.

`hireapitch.com` is behind Cloudflare bot protection. A plain request gets an
interstitial, not the page:

```
$ curl -sS -o /dev/null -w '%{http_code}\n' https://hireapitch.com/Haggerston-School
403          # body is "Just a moment..." + a Cloudflare challenge
```

So an n8n **HTTP Request** node cannot do this, and neither can a headless
scraper without a solver. A real browser session that has already passed the
challenge can. That is the whole reason this runs in Claude in Chrome.

Do not spend a turn re-discovering this. If a fetch returns 403 with
`Just a moment...`, switch to the browser and carry on.

## Inputs to pin down first

Ask for whatever is missing before opening a tab — sweeping the wrong window is
the expensive mistake:

| Input | Why it matters |
|---|---|
| Area or postcode | Picks the venue list. "London" is not an area. |
| Head count | Decides format **and how many courts** — see below. |
| Date window | A week is a 3-minute sweep. Two months is an hour. |
| Preferred day/time | Almost every corporate game is 18:00-20:00 midweek. |
| Budget or cost-per-head cap | Lets you rank, not just list. |

**Head count drives court count, and that is the trap.** A slot is only usable
if enough courts are free *at the same hour*:

| Heads | Format | Courts needed |
|---|---|---|
| 10-12 | 5-a-side | 1 |
| 12-14 | 6-a-side | 1 |
| 20-24 | 5-a-side | 2 |
| 30 | 5-a-side | 3 |

Venues that split into identical courts (Haggerston School: 3× 5-a-side, 2×
6-a-side) list each court separately. "One court free" is a yes for a team of
10 and a **no** for a firm of 24. Count free courts per hour, never per venue.

## Procedure

### 1. Build the venue list

Search hireapitch for the area and keep the venues within a sensible travel
radius of the firm's office. Check `references/london-venues.md` first — if the
area is already covered there, use that list and skip straight to step 2.

### 2. Read the grid, don't photograph it

Open the venue page, set the format, and let the calendar load. Then read the
week's cells out of the DOM in one go rather than screenshotting and
transcribing — it is faster, and it does not silently drop a row.

Selectors change, so learn them once per session instead of trusting a snippet:

```js
// Dump every candidate cell with its text and classes.
[...document.querySelectorAll('td, [class*="slot"], [class*="cell"]')]
  .map(el => ({ text: el.innerText.trim().replace(/\s+/g, ' '), cls: el.className }))
  .filter(r => r.text)
```

Find one cell you can see is free and one you can see says BOOKED, note what
distinguishes them, then write the precise extractor for that class and reuse it
for every remaining week. Verify the first week's extraction against the
rendered page before trusting the other seven.

### 3. Sweep target-first, and stop early

Go to the requested week first, not to the start of the window. Three workable
options is the goal; once you have five, stop. Only widen — next week, then
neighbouring days, then other venues — if the target week comes up short.

A full enumeration is the fallback for "what are all our options", not the
default.

### 4. Hand back a shortlist

Cost per head is `price ÷ heads` (pitch price is **per court per hour**, so
two courts is double). Lead with the recommendation:

```
Three options for <Firm>, <format>, <heads> players:

1. Thu 24 Sept, 19:00 — Haggerston School, 2 courts 5-a-side — £138 (£5.75/head)
2. Tue 29 Sept, 18:00 — Haggerston School, 2 courts 5-a-side — £138 (£5.75/head)
3. Tue 29 Sept, 19:00 — Old Street Skyway, 5-a-side — £79 (one court only, max 12)

Checked <date>. Availability is live — these go to whoever books first.
```

Always stamp the date you checked. A sweep is a snapshot, and a slot that was
green this morning is somebody else's game by the evening.

## Traps

* **An empty calendar is not a full calendar.** Mint Street showed no free cells
  *and no BOOKED cells* across nine weeks — that is availability not published,
  not a sold-out venue. Never report it as unavailable; phone it
  (020 3589 4612) or say the online calendar is blank.
* **18:00-20:00 is usually the whole board.** No earlier or later start appears
  at these venues. Do not read a blank 21:00 row as "booked".
* **Missing days are structural.** Old Street Skyway renders no cells at all on
  Fri/Sat/Sun. That is the venue not selling those days, not a full weekend.
* **Price is per court per hour.** £69 looks cheap until a firm of 24 needs two
  courts for two hours.
* **Don't book.** Return the shortlist and let a human confirm with the firm.
  Slots are only held once paid, so the answer is "pick one and I'll book it",
  never a booking made on the firm's behalf.
