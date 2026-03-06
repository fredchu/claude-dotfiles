---
name: ical-cli
description: "Manages macOS Apple Calendar events via the local `ical` CLI at /Users/fredchu/bin/ical. Full CRUD for calendar events: create, query, update, delete. Use this skill whenever the user mentions 行事曆, 行程, 加行程, 改行程, 刪行程, 查行程, 這週行程, or asks what's on their schedule. Also triggers on: 'today's events', recurring event setup, calendar search, or JSON export of events. Does NOT handle: Reminders/待辦 (use rem-cli), Apple Notes/記事 (use apple-notes), or Google Calendar free-time queries (use Google Calendar MCP). Prefer this over Google Calendar MCP for any event modification (create/update/delete) or fast local calendar reads."
---

# ical CLI — macOS Calendar

**Binary**: `/Users/fredchu/bin/ical` — always use full path.

## Gotchas (Read First)

1. **`delete` needs `--force`** — without it, blocks on interactive confirmation and hangs
2. **`update` has NO `--force` flag** — changes apply immediately, just run it
3. **`--id` and positional arg are mutually exclusive** — never pass both
4. **Calendar JSON field is `title`**, not `name`
5. **Never use `-i` (interactive mode)** — it requires terminal input, use flags instead
6. **Row numbers reset** on every list/today/upcoming command

## Commands

### Querying

```bash
/Users/fredchu/bin/ical today                                    # Today's events
/Users/fredchu/bin/ical today -o json                            # JSON for parsing
/Users/fredchu/bin/ical list --from today --to "next friday"     # Date range
/Users/fredchu/bin/ical upcoming --days 7                        # Next N days
/Users/fredchu/bin/ical show 2                                   # Details for row #2
/Users/fredchu/bin/ical search "meeting" --from "jan 1" --to "dec 31"
/Users/fredchu/bin/ical calendars -o json                        # List calendars
```

### Creating

```bash
/Users/fredchu/bin/ical add "會議" \
  --start "tomorrow at 2pm" --end "tomorrow at 3pm" \
  --calendar Work --alert 15m --location "Office"

# Recurring
/Users/fredchu/bin/ical add "Standup" \
  --start "next monday at 9am" --end "next monday at 9:30am" \
  --repeat weekly --repeat-days mon,wed,fri
```

### Updating

```bash
# By row number (NO --force needed, changes apply immediately)
/Users/fredchu/bin/ical update 1 --title "新標題"
/Users/fredchu/bin/ical update 2 --start "tomorrow at 3pm" --end "tomorrow at 4pm"
/Users/fredchu/bin/ical update 1 --location ""        # Clear a field
/Users/fredchu/bin/ical update 1 --alert none          # Clear alerts
/Users/fredchu/bin/ical update 1 --repeat none         # Remove recurrence

# By exact ID (for scripts)
/Users/fredchu/bin/ical update --id "FULL_EVENT_ID" --title "New"

# Recurring: update this + future occurrences
/Users/fredchu/bin/ical update 2 --span future --start "next monday at 9am"
```

### Deleting

```bash
# ALWAYS pass --force to avoid interactive prompt
/Users/fredchu/bin/ical delete 1 --force
/Users/fredchu/bin/ical delete --id "FULL_EVENT_ID" --force

# Recurring: delete this + future
/Users/fredchu/bin/ical delete 3 --span future --force
```

## Key Flags Reference

**Filtering** (list / today / upcoming / search):
- `--calendar` `-c` — filter by calendar name
- `--from` `-f`, `--to` `-t` — date range
- `--exclude-calendar` — exclude by name (repeatable)
- `-o json` — JSON output

**Creating** (add):
- `--start` `-s` (required), `--end` `-e` (default: start + 1h)
- `--calendar` `-c`, `--location` `-l`, `--notes` `-n`, `--url` `-u`
- `--alert` (e.g., `15m`, `1h`, `1d`) — repeatable
- `--all-day` `-a`
- `--repeat` (`daily`/`weekly`/`monthly`/`yearly`)
- `--repeat-interval`, `--repeat-days` (e.g., `mon,wed`), `--repeat-count`, `--repeat-until`

**Event selection** (show / update / delete):
- Number → row from last listing (e.g., `2`)
- `--id "FULL_ID"` → exact match (preferred for scripting)
- Never combine both

## Date Syntax

Natural language: `today`, `tomorrow`, `now`, `eod`, `eow`, `next monday`, `in 3 hours`, `2 days ago`, `mar 15 at 2pm`, `5pm`, `next friday at 3:30pm`, `end of week`

ISO: `2026-03-15`, `2026-03-15T14:30:00`

## JSON Fields

**Event**: `id`, `title`, `start_date`, `end_date`, `calendar`, `calendar_id`, `location`, `notes`, `url`, `all_day`, `recurrence`, `alerts`

**Calendar**: `id`, `title`, `type`, `color`, `source`, `readOnly`
