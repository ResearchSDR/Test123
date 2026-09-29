# FC Urban London daily outreach pipeline

Status: **dry run**. Nothing in here sends email on its own yet. Sending is only enabled after Brian approves a dry run day.

## How the day runs

| Time (London) | Step | Runs in |
|---|---|---|
| 06:00 | Rebuild suppression, scrape venue pages, source and research leads, write emails | Claude Code routine (fresh session, connectors: Gmail, Google Drive, Notion) |
| 07:30 | QA gate (`compose.qa`) on every email, failures dropped and logged | same routine |
| 07:45 | Slack DM to Brian (U0BLTEGER54): count, 10 random full samples, sector and venue split, drops and why, link to the day's sheet | same routine (Slack connector) |
| 08:30 | Approval: phase 1 sets `Approved = yes` only after Brian replies "go" in that thread. Phase 2 (Brian enables after 10 clean days) sets it unless he replies "stop" before 08:55 | Claude Code routine |
| 09:00 | Wave 1: up to 100 sends, random 20 to 40 s gaps | n8n `n8n/fcurban-daily-send-workflow.json` |
| 14:00 | Wave 2: up to 100 sends | same n8n workflow |
| 17:30 | Reply digest (classify, suppress, suggested replies with two free 10 minute slots) | Claude Code routine |

Weekends: no sends (the n8n schedule is `1-5`).

## Why sending is in n8n and not in Claude

Emails sent through the Claude Gmail connector's `send_message` come out with every link rewritten to
`https://www.google.com/url?q=...` (confirmed on 29 Sep in the raw MIME of all 30 finance batch 3 emails).
Drafts created through the connector keep the plain link. The n8n Gmail node sends through the Gmail API
with its own MIME, so the venue link stays plain. The QA gate and the n8n `Build wave` node both refuse any
email containing `google.com/url`.

## Files

| File | What it does |
|---|---|
| `venues_live.py` | Scrapes every fcurban.com location page, marks a venue live if its "Next games" list has a game in the next 14 days. The "Games we play weekly" counter is filled by JavaScript and reads 0 in static HTML, so it is not used. |
| `slots.py` + `config/confirmed_slots.json` | Slot line per live venue: the confirmed tab first (St John's Wood, Poplar from Luuk), else the weekday evening games on the venue page, compressed ("Mondays to Thursdays at 19:30"). |
| `compose.py` | Writes subject, plain text and HTML body. Venue claim only for the nearest LIVE weekday evening venue within 15 minutes' walk (straight line x 1.3 at 4.8 km/h from the working office postcode), else the "opening new weekly games near your office" variant with no link. Runs the QA gate. |
| `build_n8n_send_workflow.py` | Generates `n8n/fcurban-daily-send-workflow.json`. |

## Venue state on 29 Sep 2026 (from the scrape, next 14 days)

Live, weekday evenings: Borough Academy (Fri 19:30), Old Street Moreland (Fri 19:00), Poplar (Tue, Thu 20:00),
St John's Wood (Mon 19:30, Tue 21:00 on the page; Luuk's confirmed slots used instead), Kennington (Mon 20:00),
Whitechapel (Mon to Thu 19:30), Shoreditch Rooftop on Pitfield Street (Fri 20:00), Bermondsey, Chelsea,
South Kensington, Hackney, Hampstead, Whittington Park, Surrey Quays, Acton.
Live but weekend only (not used for an after work pitch): Brixton.
Not live: Coram's Fields, Attlee Centre, St Pancras Rooftop, Powerleague Shoreditch, Rosemary Gardens, Stepney,
COLA Shoreditch Park (no games listed yet).

## Open items before sending can be switched on

1. **SPF/DKIM for fcurban.com.** The domain has two SPF records (invalid), neither includes Google, there is no
   Google DKIM record, DMARC is `p=none`. Fix: one record
   `v=spf1 include:_spf.google.com include:_spf.firebasemail.com include:spf.mandrillapp.com ~all`, then turn on
   DKIM in Google Admin (Apps > Google Workspace > Gmail > Authenticate email).
2. **API keys** (none in this environment): email verification (NeverBounce or ZeroBounce), Companies House API,
   Google Places, Apollo / Hunter / PDL. Add them as environment secrets, never in code.
3. **n8n**: import `n8n/fcurban-daily-send-workflow.json`, replace `QUEUE_SHEET_ID` and `LOG_SHEET_ID`, pick the
   Gmail and Sheets credentials, leave it inactive until the dry run is approved.
4. **Dugout groups**: no access from here; export a list of group company names/domains into the suppression sheet.
5. **Volume**: the pool of new firms within 15 minutes of a live weekday venue is small (about 60 venue claims on
   day 1). Reaching 200 a day means most emails use the "opening new weekly games" variant from across London.
