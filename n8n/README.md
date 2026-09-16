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
* **Send email** has a real error output, so a bounce or a bad address does not kill
  the run — that row gets `Failed` instead of `Emailed`.
* **Wait between sends** throttles to one email per 20s.

## Setup (5 things)

1. **Add three columns** to the sheet, to the right of the existing 13:
   `Status`, `Sent at`, `Send error`. The workflow only sends to rows where
   `Status` is empty, and writes into all three afterwards.
2. **Spreadsheet ID** — replace `PASTE_YOUR_SPREADSHEET_ID_HERE` in the two Google
   Sheets nodes (and in the optional HTTP node's URL). It's the long id in the
   sheet URL between `/d/` and `/edit`.
3. **Tab name** — the nodes are set to `London`. Change it if you run another city.
4. **Credentials** — pick your Google Sheets OAuth2 credential on both Sheets nodes,
   and your Gmail OAuth2 credential on **Send email**.
5. **Re-pick the update columns** — open **Mark as emailed** / **Mark as failed**,
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
  Sheets API `batchUpdate` to paint the row directly. Enable it, set the
  spreadsheet id in the URL, and set `sheetId` in the JSON body to the tab's `gid`
  (the number at the end of the sheet URL). Its credential is the same Google
  Sheets OAuth2 one.

## Things to change

| What | Where |
|---|---|
| Batch size (300) | `Build send queue` → `const LIMIT` |
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
* Test first: set `LIMIT = 2` and point `Get leads` at a copy of the sheet.
