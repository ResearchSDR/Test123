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
  Greeting uses a first name only when the mailbox local part matches a real
  first-name list — `Email type = person_or_other` is not trustworthy on its own
  (it holds `wholesale@`, `flowers@`, `getstuffed@`, `myqueryto@`). Across the
  6,211 London rows that is 129 by first name, 6,082 as `Hi <Company> team,`.
* **Send email** has a real error output, so a bounce or a bad address does not kill
  the run — that row gets `Failed` instead of `Emailed`.
* **Wait between sends** throttles to one email per 20s.

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
| Tab | gid `1397729834` |
| Link | https://docs.google.com/spreadsheets/d/1Knj2jXfZLK6-rgyQtyCXYu_Kg7WwqqZp9CqG0wn5F6g/edit?gid=1397729834 |

Both Sheets nodes address the tab by **gid**, not by name, so renaming the tab
won't break anything. To run a different city, change the `sheetName` value on
`Get leads from sheet`, `Mark as emailed` and `Mark as failed` to that tab's gid.

## Setup (3 things)

1. **Add three columns** to the tab, to the right of the existing 13:
   `Status`, `Sent at`, `Send error`. The workflow only sends to rows where
   `Status` is empty, and writes into all three afterwards. Without them nothing
   gets marked and every run re-sends the same leads.
2. **Credentials** — pick your Google Sheets OAuth2 credential on both Sheets
   nodes, and your Gmail OAuth2 credential on **Send email**. The account must
   have edit access to the spreadsheet above.
3. **Re-pick the update columns** — open **Mark as emailed** / **Mark as failed**,
   let the column list load once, and confirm the mapping is
   `row_number` (matching) + `Status` / `Sent at` / `Send error`.

## Marking rows green

Two options:

* **Conditional formatting (recommended, no code).** In the sheet: Format →
  Conditional formatting, range `A2:P`, rule *Custom formula is*
  `=$N2="Emailed"` → green fill. (`$N` = your `Status` column; adjust the letter.)
  Rows turn green the moment the workflow writes `Emailed`. Add a second red rule
  for `=$N2="Failed"`.
* **The `Colour row green (optional)` node.** Disabled by default. It calls the
  Sheets API `batchUpdate` to paint the row directly. Spreadsheet id and
  `sheetId: 1397729834` are already filled in — just enable it and pick the same
  Google Sheets OAuth2 credential.

## Things to change

| What | Where |
|---|---|
| Batch size (now **2**, for testing) | `Build send queue` → `const LIMIT` |
| Delay between sends | `Wait between sends` → Amount |
| Email copy / subject | `Compose email` → the `body` array |
| Which rows count as "done" | `Build send queue` → `STATUS_COL` check |

## Before you run 300

* 300 × 20s ≈ **100 minutes** of wall clock. A manual execution has to stay open
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
