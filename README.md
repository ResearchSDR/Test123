# FC Urban — outreach and booking

Two halves of the same pipeline: find firms who want to play, then find them a
pitch.

| | What it is | Where |
|---|---|---|
| **Outreach** | n8n workflow that emails the next 300 untouched leads and writes the result back to the sheet | [`n8n/`](n8n/README.md) |
| **Venue sweep** | Claude skill that turns a positive reply into a shortlist of bookable slots | [`.claude/skills/venue-sweep/`](.claude/skills/venue-sweep/SKILL.md) |

The handover between them is a reply naming a location and a rough date. From
there the sweep needs a head count and a preferred evening before it opens a tab.

`hireapitch.com` is behind Cloudflare, so the booking half cannot be an n8n HTTP
node — it runs in a real browser session. The skill explains why and how.
