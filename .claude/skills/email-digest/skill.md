---
name: email-digest
description: Legge email Gmail ultimi N giorni, sintetizza per topic e priorità, stampa digest in terminale. Opzionale --md per file Markdown con link Gmail.
---

## Execution

```bash
cd ".claude/skills/email-digest" && python email_digest.py [--md [FILE]] [--days N]
```

**Richiede:** `GMAIL_APP_PASSWORD` env var — impostata in `.claude/settings.local.json`.

## Config inside script

| Parametro | Valore |
|-----------|--------|
| Account | prof.f.adriani@gmail.com |
| IMAP host | imap.gmail.com:993 (SSL) |
| Default periodo | 7 giorni |

## Usage

```bash
python email_digest.py                    # solo terminale
python email_digest.py --md               # + email_digest_YYYY-MM-DD.md
python email_digest.py --md report.md     # file custom
python email_digest.py --days 14          # ultimi 14 giorni
```

## Common mistakes

- `GMAIL_APP_PASSWORD` vuota → script esce con errore, controllare settings.local.json
- Password con spazi: usare esatta (con spazi)
