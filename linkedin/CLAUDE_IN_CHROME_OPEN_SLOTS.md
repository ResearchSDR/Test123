I need you to find open after-work pitch slots at 9 football venues in London. Look them up only. Do not book, reserve, hold, enter payment details or submit any form.

## Window
- Weekdays only (Mon–Fri), from Mon 28 Sep 2026 to Fri 23 Oct 2026
- Kick-off between 17:30 and 20:30
- Stop at 23 Oct because the clocks go back on 25 Oct. After that, unlit pitches are dark by about 16:45

## Venues
| # | Venue | Address |
|---|---|---|
| 1 | Haggerston Park | Yorkton St, E2 8NH |
| 2 | Whitechapel | Richard St, E1 2JR |
| 3 | Shoreditch Rooftop | Britannia Leisure Centre, Pitfield Street, N1 5FT |
| 4 | Rosemary Gardens 3G - Islington | Southgate Road, N1 3JP |
| 5 | Stepney 3G | Globe Road, E1 4DZ |
| 6 | Old St - Moreland Primary School | Gard Street, EC1V 8DW |
| 7 | Hackney | Homerton High St, E9 6JQ |
| 8 | COLA Shoreditch Park | Hyde Rd, N1 5JU |
| 9 | Market Road | Market Rd, N7 9PL |

## Steps for each venue
1. Find where the pitch is actually booked. Search the venue name, address and "pitch hire" or "book pitch". It will usually be one of these: the council or leisure operator (Better / GLL, Hackney Council, Islington Council, Tower Hamlets), Playfinder, ClubSpark, Powerleague, or a school lettings page.
2. Open the booking calendar and list every free slot in the window above. Include pitch size (5/6/7/8/11-a-side) and the hire price where it's shown.
3. Check whether the pitch has floodlights. Say so explicitly, especially for Haggerston Park.
4. If you can't see availability without an account, or it's by enquiry only, don't guess. Write down the phone number, email or enquiry form URL and mark the venue `Contact required`.
5. Spend no more than about 5 minutes per venue. If you can't find the booking system, mark it `Not found` and move on.

## Return format
Reply with **only** the two blocks below, exactly as formatted, so they can be pasted straight back into another tool.

Block 1 has one row per open slot. For a venue with no slots found, add one row with the date/time columns left empty and the status filled in.

```csv
venue,date,day,start,end,pitch_format,hire_price_gbp,floodlit,status,booking_source,booking_url,notes
Haggerston Park,2026-09-29,Tue,18:00,19:00,7-a-side,65,no,Available,Hackney Council,https://...,
Whitechapel,,,,,,,,Contact required,Tower Hamlets,https://...,call 020 ... to check
```

`status` must be one of: `Available`, `Contact required`, `No availability`, `Not found`.
Prices are per slot for the whole pitch, as a number with no £ sign. Use `yes`, `no` or `unknown` for `floodlit`.

Block 2 has one row per venue with who to contact to confirm a booking:

```csv
venue,booking_contact_name,phone,email,cancellation_terms,booking_deadline,notes
```

Leave any field you can't find empty. Don't estimate it.
