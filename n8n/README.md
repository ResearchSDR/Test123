# FC Urban outreach batch — n8n

Import `fcurban-outreach-workflow.json` into n8n (Workflows → ⋯ → Import from File).

Press **Execute workflow** and it sends the next 300 not-yet-emailed leads, in sheet
order, then writes the result back to the same row.

## What it does

```
Execute  →  Get leads from sheet  →  Build send queue  →  Loop over leads ─┬─ done → Run summary
                                                                          │
                                            ┌─────────────────────────────┘
                                            └→ Compose email → Send email ─┬─ ok   → Mark as emailed → (Colour row green) ─┐
                                                                           └─ fail → Mark as failed ───────────────────────┤
                                                                                                          Wait 20s ←───────┘
                                                                                                             └→ back to loop
```

* **Build send queue** skips rows with no `Email`, rows that already have a `Status`,
  and duplicate addresses. Takes the first 300 that remain, top to bottom.
* **Compose email** personalises greeting, city, nearest venue and walking time
  from the sheet. It only claims a venue/walk distance when those cells are filled.
  Every lead is greeted as `Hi <Company> team,` — a trailing parenthetical is
  stripped first, so `MOO Print Limited (UK)` becomes `MOO Print Limited`.
* **Send email** has a real error output, so a bounce or a bad address does not kill
  the run — that row gets `Failed` instead of `Emailed`.
* **Wait between sends** throttles to one email per 20s.
* **Replies go to `joep@fcurban.com`** via a `Reply-To` header. The *From*
  address is still whatever Google account the Gmail credential holds — n8n
  cannot change that — so a reply is only redirected when the recipient's mail
  client honours `Reply-To`, which all mainstream ones do. The Unit field must say
  **seconds** — n8n defaults it to *hours*, and a wait over 65s makes n8n park the
  execution in the database instead of sleeping in process, so the run appears to
  "succeed" after one email and resumes hours later.

`Compose email` runs in **Run Once for Each Item** mode — it handles one lead and
returns one item. Leave it there. In "Run Once for All Items" it still works
while `Loop over leads` has Batch Size 1, but raise that batch size and it would
compose the first lead of each batch and silently drop the rest.

## How sent leads are tracked

The sheet is the record, written **per lead, as the run goes** — not at the end.

| Outcome | `Status` | `Sent at` | `Send error` |
|---|---|---|---|
| Gmail accepted it | `Emailed` | timestamp | empty |
| Gmail rejected it | `Failed` | timestamp | the error |
| Never reached | empty | empty | empty |

The row is matched by `row_number`, so the result always lands on the lead it
belongs to even though the sheet is 6,000 rows deep.

What this buys you:

* **Interrupting a run is safe.** Close the tab, hit stop, lose the connection —
  every lead already sent is already marked. Press Execute again and
  `Build send queue` skips anything with a `Status`, so it picks up where it
  stopped instead of re-sending.
* **A broken tracker stops the run.** If the sheet write fails (wrong columns,
  revoked access), the workflow halts rather than carrying on sending
  untracked emails. It retries 3× with a 5s gap first, so a transient Google
  blip doesn't stop you.
* **`Run summary`** reports `queued` / `sent` / `failed` / `notReached` at the end,
  plus the address and error for each failure. `notReached > 0` means the run
  stopped early — the sheet tells you exactly where.

The **worst case is one unrecorded email**: Gmail accepts a lead, then the sheet
write fails all 3 retries. That lead gets emailed twice if you re-run. Sending
happens one at a time, so it can never be more than one.

## Target sheet (already wired in)

| | |
|---|---|
| Spreadsheet | `1Knj2jXfZLK6-rgyQtyCXYu_Kg7WwqqZp9CqG0wn5F6g` |
| Tab | London, gid `163781985` |
| Link | https://docs.google.com/spreadsheets/d/1Knj2jXfZLK6-rgyQtyCXYu_Kg7WwqqZp9CqG0wn5F6g/edit?gid=163781985 |

Both Sheets nodes address the tab by **gid**, not by name, so renaming the tab
won't break anything. To run a different city, change the `sheetName` value on
`Get leads from sheet`, `Mark as emailed` and `Mark as failed` to that tab's gid.

## Setup (3 things)

1. **Add the tracking columns.** The sheet ships with 13 columns, `A` Business
   through `M` From list. Type these into row 1, exact spelling, no trailing
   spaces:

   | Cell | Header |
   |---|---|
   | `N1` | `Status` |
   | `O1` | `Sent at` |
   | `P1` | `Send error` |
   | `Q1` | `WhatsApp status` — only if you enable the WhatsApp branch |
   | `R1` | `WhatsApp at` — same |

   The workflow only sends to rows where `Status` is empty, and writes into the
   rest afterwards. **Without these columns the Sheets update writes nothing and
   returns nothing, n8n skips the whole rest of the loop, and the run reports
   success after one unrecorded email.** That is the single most common way this
   workflow appears broken.

   After adding them, open `Mark as emailed` and `Mark as failed` once so n8n
   reloads the column list from the live sheet (setup step 3).
2. **Credentials** — pick your Google Sheets OAuth2 credential on both Sheets
   nodes, and your Gmail OAuth2 credential on **Send email**. The account must
   have edit access to the spreadsheet above.
3. **Re-pick the update columns** — open **Mark as emailed** / **Mark as failed**,
   let the column list load once, and confirm the mapping is
   `row_number` (matching) + `Status` / `Sent at` / `Send error`.

## WhatsApp branch (disabled — read this before enabling)

Hangs off `Mark as emailed` as a side branch, so it can never affect email
sending or tracking: `Has a mobile number?` → `Send WhatsApp` → `Mark WhatsApp status`.

Two more sheet columns: `WhatsApp status`, `WhatsApp at`.

**Only 10% of your numbers can receive WhatsApp.** It delivers to mobiles only,
and this sheet is mostly switchboards:

| Tab | Rows | Mobile | Landline | Blank |
|---|---|---|---|---|
| London | 6,211 | 433 (7%) | 4,381 (70%) | 1,341 (21%) |
| Amsterdam | 4,220 | 459 (10%) | 2,758 (65%) | 967 (22%) |
| Stockholm | 4,337 | 732 (16%) | 2,849 (65%) | 734 (16%) |
| Munich | 1,881 | 112 (5%) | 1,389 (73%) | 376 (19%) |

`Compose email` normalises `Phone (international)` to E.164 and keeps it only if
the prefix is a mobile range (UK `447`, NL `316`, SE `467`, DE `4915-4917`,
ES `346/347`, BE `324`). Everything else becomes `''` and the IF node routes it
past the branch. Dry run over London: **434 messaged, 5,777 skipped.**

**Why it ships disabled.** The WhatsApp Business Cloud API rejects free-form
messages to people who have not messaged you in the last 24 hours. Cold outreach
*must* use a Meta-approved template. So before enabling:

1. In Meta WhatsApp Manager, create a **Marketing** template. Submit something like:

   > Hi {{1}}, Joe here from FC Urban. We run social football games near {{2}}
   > and are looking for local companies to play after work. We sort the pitch,
   > payments and organisation. Interested in trying it? Reply STOP to opt out.

2. Wait for approval (hours to days).
3. Un-disable **Send WhatsApp** and **Mark WhatsApp status** (both — enabling only
   the first sends without recording it).
4. On `Send WhatsApp`: attach your WhatsApp Business Cloud credential, set
   `phoneNumberId`, and pick the approved template from the dropdown. Map
   `{{1}}` → `{{ $('Compose email').item.json.waName }}` and
   `{{2}}` → `{{ $('Compose email').item.json.waVenue }}`. The variable fields
   only appear once the template is selected, which is why they are not pre-filled.

**The risk is real.** Marketing templates to scraped numbers that never opted in
get marked "block/report" fast. That drops your quality rating, then your
messaging limit, and Meta can disable the number — the same number you would use
for real customer conversations. Email bounces cost you nothing comparable. If
you run it, run it on a separate number, in small batches, and watch the quality
rating in WhatsApp Manager. Under UK PECR and GDPR, messaging a personal mobile
is closer to SMS marketing than to B2B email, and the consent bar is higher.

## If it sends one email and stops

**First check: do `Status`, `Sent at` and `Send error` actually exist in the tab,
spelled exactly like that, in row 1?** (In the current sheet they are `N1`-`P1`.) If they don't, the Sheets update node
writes nothing and returns nothing. n8n skips every node downstream of an empty
output — including the loop-back — and still reports "Workflow executed
successfully". One email goes out, the row is never marked, and the next run
sends that same lead again.

`Confirm row marked` now catches this: it halts the run with a named row and a
description rather than letting it continue.



`Mark as emailed` fans out to three branches, and only one of them — `Wait
between sends` — carries the loop back to `Loop over leads`. n8n queues
branches by canvas position, top first, so **`Wait between sends` must sit
above `Has a mobile number?` and `Colour row green`**. Below them, anything
that stalls or errors in an optional branch takes the loop with it and the run
stops after one lead.

If you move nodes around, keep the Wait node the highest of the three.

Other things that produce the same one-and-stop symptom:

* **Wait Unit set to Hours.** n8n's default. Over 65 seconds n8n parks the
  execution in the database instead of sleeping in process, so the run reports
  success after one email and resumes much later. Must read **Seconds**.
* **A node that returns zero items.** n8n skips everything downstream and calls
  the run a success. The two `Mark as` nodes set `alwaysOutputData` so they
  always emit something, and `Confirm row marked` turns a silent no-write into a
  loud stop.
* **An error in a side branch.** Open the execution and look for a red node.
  The WhatsApp and colour branches read back with
  `$('Compose email').first()` rather than `.item` precisely because `.item`
  asks n8n to trace pairedItem through both Gmail and Sheets, which can fail
  and halt the run. `.first()` is safe only while `Loop over leads` has
  Batch Size 1.

## Venue links

The closing line hyperlinks **FC Urban** and **the nearest venue**. The email
goes out as HTML (`Send email` → Email Type: HTML, body `{{ $json.html }}`).

`VENUE_SLUGS` in `Compose email` maps a venue name, spelled exactly as the sheet
spells it, to its `fcurban.com/location/<slug>` slug. **108 venues across all 15
city tabs**, every slug taken from `fcurban.com/sitemap.xml` and confirmed to
return HTTP 200 with a page title matching the venue.

Slugs are not derivable from the name — Brixton is `brixton-03dac` — so the map
is explicit rather than generated. A venue missing from it renders as plain
text, never as a broken link.

London coverage is complete: all 26 venues, all 6,209 queued leads linked.
To add a venue later, find it in `fcurban.com/sitemap.xml` and add the pair.

Company and venue names are HTML-escaped, so `Catherine Walker & Co` cannot
break the message.

## Marking rows green

Two options:

* **Conditional formatting (recommended, no code).** In the sheet: Format →
  Conditional formatting, range `A2:P`, rule *Custom formula is*
  `=$N2="Emailed"` → green fill. (`$N` = your `Status` column; adjust the letter.)
  Rows turn green the moment the workflow writes `Emailed`. Add a second red rule
  for `=$N2="Failed"`.
* **The `Colour row green (optional)` node.** Disabled by default. It calls the
  Sheets API `batchUpdate` to paint the row directly. Spreadsheet id and
  `sheetId: 163781985` are already filled in — just enable it and pick the same
  Google Sheets OAuth2 credential.

## Things to change

| What | Where |
|---|---|
| Batch size (now **75**) | `Build send queue` → `const LIMIT` |
| Delay between sends | `Wait between sends` → Amount **and Unit** (see below) |
| Email copy / subject | `Compose email` → the `paras` array |
| Where replies land | `Send email` → options → `replyTo` |
| Venue page links | `Compose email` → `VENUE_SLUGS` |
| The FC Urban link | `Compose email` → `FC_URBAN_URL` |
| The opt-out line | `Compose email` → `OPT_OUT` (set to `''` to drop) |
| Leads per loop pass | `Loop over leads` → Batch Size (keep at 1) |
| Which rows count as "done" | `Build send queue` → `STATUS_COL` check |
| Addresses to never email | `Build send queue` → `SKIP_EMAILS` |

## Before you run 300

* 75 × 20s ≈ **25 minutes** of wall clock. A manual execution has to stay open
  that long. Either lower the wait, or swap the Manual Trigger for a Schedule
  Trigger and let it run in the background.
* Gmail caps external recipients at 500/day (personal) or 2,000/day (Workspace) —
  300 fits, but 300 near-identical cold emails from one mailbox in one sitting is
  exactly the pattern spam filters score on. The 50–80/day you were doing before is
  much safer for the domain. Set `LIMIT` to 75 and press execute four times over
  four days rather than once.
* **Test first with `LIMIT = 2`.** This is the run that proves tracking works —
  if the `Status` / `Sent at` / `Send error` columns are missing or misnamed, the
  `Mark as emailed` node errors and the run halts after the first email. Two test
  leads catches that; 300 catches it the expensive way. Check both rows went green
  and show a timestamp before raising the limit.
