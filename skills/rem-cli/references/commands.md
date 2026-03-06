# Command Flag Reference

## rem add (aliases: create, new)

| Flag | Short | Description | Default |
|------|-------|-------------|---------|
| `--list` | `-l` | List name | System default |
| `--due` | `-d` | Due date (natural language or ISO) | None |
| `--priority` | `-p` | high, medium, low, none | none |
| `--notes` | `-n` | Notes/body text | Empty |
| `--url` | `-u` | URL (stored in body with `URL: ` prefix) | None |
| `--flagged` | `-f` | Flag the reminder | false |

## rem list (alias: ls)

| Flag | Short | Description | Default |
|------|-------|-------------|---------|
| `--list` | `-l` | Filter by list | All |
| `--incomplete` | | Only incomplete | false |
| `--completed` | | Only completed | false |
| `--flagged` | | Only flagged | false |
| `--due-before` | | Due before date | None |
| `--due-after` | | Due after date | None |
| `--search` | `-s` | Search title+notes | None |
| `--output` | `-o` | table, json, plain | table |

## rem show (alias: get)

| Flag | Short | Description | Default |
|------|-------|-------------|---------|
| `--output` | `-o` | table, json, plain | table |

## rem update (alias: edit)

| Flag | Short | Description | Default |
|------|-------|-------------|---------|
| `--name` | | New title | — |
| `--due` | `-d` | New due date (`none` to clear) | — |
| `--notes` | `-n` | New notes | — |
| `--priority` | `-p` | high, medium, low, none | — |
| `--url` | `-u` | New URL | — |
| `--flagged` | | true/false | — |

## rem delete (aliases: rm, remove)

| Flag | Description | Default |
|------|-------------|---------|
| `--force` | Skip confirmation | false |

## rem complete (alias: done) / uncomplete / flag / unflag

No flags. Takes reminder ID as argument.

## rem search

| Flag | Short | Description | Default |
|------|-------|-------------|---------|
| `--list` | `-l` | Search within list | All |
| `--incomplete` | | Only incomplete | false |
| `--output` | `-o` | table, json, plain | table |

## rem overdue / upcoming

| Flag | Description | Default |
|------|-------------|---------|
| `--days` | (upcoming only) Days ahead | 7 |
| `--output` / `-o` | table, json, plain | table |

## rem stats

| Flag | Description | Default |
|------|-------------|---------|
| `--output` / `-o` | plain, json | plain |

## rem lists

| Flag | Short | Description | Default |
|------|-------|-------------|---------|
| `--count` | `-c` | Show count per list | false |
| `--output` | `-o` | table, json, plain | table |

## rem list-mgmt

- `create "name"` — Create list
- `rename "old" "new"` — Rename list
- `delete "name" --force` — Delete list (use --force)

## rem export

| Flag | Description | Default |
|------|-------------|---------|
| `--list` / `-l` | Export from list | All |
| `--format` | json, csv | json |
| `--output-file` | File path | stdout |
| `--incomplete` | Only incomplete | false |

## rem import

| Flag | Description | Default |
|------|-------------|---------|
| `--list` / `-l` | Import all into list | Original |
| `--dry-run` | Preview only | false |
