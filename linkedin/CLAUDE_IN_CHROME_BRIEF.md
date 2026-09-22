# Brief for Claude in Chrome — FC Urban LinkedIn outreach

Paste everything below the line into Claude in Chrome together with
`city_of_london_finance_top100.csv`. It is written to be handed over as-is.

---

You are helping me with LinkedIn outreach for FC Urban. I have attached a CSV of
100 City of London companies. I am logged into LinkedIn as Joep.

## The file

One company per row. Columns you need:

| Column | Use |
|---|---|
| `Priority` | Work in this order, 1 first |
| `Company name` | The firm |
| `LinkedIn URL` | The contact's profile. **Blank on most rows — see below** |
| `Contact first name` | Blank — you fill it |
| `Connection note (<=300)` | The message, with a `{First}` placeholder |
| `Follow-up DM` | For after they accept |
| `LinkedIn status` | Blank — you fill it |

## What I want you to do

Work through rows in `Priority` order, **20 per session, then stop.**

For each row:

1. **Find the person** if `LinkedIn URL` is blank. Search LinkedIn for the
   company, then for someone with one of these titles, best first:
   - Office Manager, Workplace Experience, Head of Operations
   - HR Manager, People & Culture, Employee Engagement, Wellbeing
   - at firms under ~50 staff: a founder or partner
   Pick **one** person. Put their profile URL in `LinkedIn URL`, their first
   name in `Contact first name`, their title in `Contact job title`.
2. **Skip the row** if you cannot find a plausible person in about a minute.
   Write `No contact found` in `LinkedIn status` and move on. Do not guess.
3. **Send a connection request** with a note. Take the text from
   `Connection note (<=300)` and replace `{First}` with their actual first name.
   Do not rewrite it, do not add to it, do not exceed 300 characters.
4. **Record the outcome** in `LinkedIn status`: `Request sent`,
   `Already connected`, `No contact found`, or `Failed - <reason>`.
   Put today's date in `Connected at`.
5. **Wait 60–90 seconds** before the next row.

If someone is already a 1st-degree connection, do not send a request. Send the
`Follow-up DM` text instead and record `DM sent`.

## Rules

- **Never send more than 20 requests in one session, or 100 in a week.**
  LinkedIn restricts accounts over roughly 100–200 invites per week, and this is
  Joep's real profile.
- **Never edit the message wording.** The venue and walking distance in each note
  are specific to that company and are the reason the message works.
- **One person per company.** Do not message several people at the same firm.
- If LinkedIn shows any warning, rate-limit notice, or a CAPTCHA, **stop
  immediately** and tell me. Do not work around it.
- If a profile looks wrong for this (a recruiter, someone who has left, an
  obvious sales account), skip it rather than force a match.

## At the end

Give me back the CSV with `Contact first name`, `Contact job title`,
`LinkedIn URL`, `LinkedIn status` and `Connected at` filled in for the rows you
worked, plus a short summary: requests sent, already connected, skipped, failed.
