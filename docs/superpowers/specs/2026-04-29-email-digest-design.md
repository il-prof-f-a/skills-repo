# Email Digest Skill — Design Spec
**Date:** 2026-04-29  
**Status:** Approved

## Obiettivo

Script Python standalone che legge le email degli ultimi 7 giorni da `prof.f.adriani@gmail.com` via IMAP, le classifica per topic e priorità con regole keyword, e stampa una sintesi in terminale. Opzionalmente genera un file `.md` con link diretti Gmail.

## Struttura file

```
.claude/skills/email-digest/
  email_digest.py      # script principale
  skill.md             # definizione skill per Claude Code
```

## Dipendenze

Solo stdlib Python: `imaplib`, `email`, `argparse`, `datetime`, `re`.  
Credenziali: `GMAIL_APP_PASSWORD` da `settings.local.json` (già presente).

## Componenti

### `fetch_emails()`
- Connette a `imap.gmail.com:993` SSL
- Login con `prof.f.adriani@gmail.com` + `GMAIL_APP_PASSWORD`
- IMAP SEARCH `SINCE <date-7d>` su INBOX
- Fetch: `RFC822` (headers + body)
- Ritorna lista di dict con: `id`, `subject`, `sender`, `date`, `body_snippet`, `message_id`

### `classify(msg) → (topic, priority)`
Priorità (valutata per prima sul subject + sender):

| Livello | Trigger |
|---|---|
| Alta | urgente, importante, scadenza, deadline, ASAP, entro oggi, entro domani |
| Bassa | unsubscribe, newsletter, noreply, no-reply nel sender |
| Media | tutto il resto |

Topic (valutato su subject + sender domain):

| Topic | Keywords |
|---|---|
| Lavoro | progetto, riunione, meeting, call, task, offerta, contratto |
| Fatture/Pagamenti | fattura, pagamento, invoice, scadenza, bonifico, ricevuta |
| Newsletter | unsubscribe, newsletter |
| Notifiche | noreply, no-reply, notification, alert, conferma, verifica |
| Personale | (fallback) |

### `group_and_sort(emails)`
Raggruppa per topic → ordina ogni gruppo per priorità (Alta → Media → Bassa) → ordina per data desc.

### `render_terminal(groups)`
Stampa digest formattato con emoji per topic, contatori per priorità, elenco email.

```
=== DIGEST EMAIL — 7 giorni (23/04 - 29/04/2026) ===

📌 LAVORO [Alta: 2 | Media: 5 | Bassa: 0]
  [ALTA] "Riunione domani ore 10" — mario@example.com (27/04)
  [MEDIA] "Update progetto X" — team@company.it (25/04)

💰 FATTURE/PAGAMENTI [Alta: 1 | Media: 0 | Bassa: 0]
  [ALTA] "Scadenza fattura #123" — billing@acme.com (26/04)
```

### `render_md(groups, filepath)`
Scrive file Markdown con tabella per topic. Link Gmail: `https://mail.google.com/mail/u/0/#inbox/<message_id>`

```markdown
# Email Digest — 23/04 - 29/04/2026

## 📌 Lavoro

| Priorità | Oggetto | Mittente | Data |
|---|---|---|---|
| 🔴 Alta | [Riunione domani ore 10](https://mail.google.com/...) | mario@example.com | 27/04 |
```

### `main()`
`argparse`:
- `--md` (flag opzionale, default: `email_digest_YYYY-MM-DD.md`)
- `--md <filepath>` (file custom)
- `--days N` (default: 7)

## Invocazione

```bash
python email_digest.py                    # solo terminale
python email_digest.py --md               # + file email_digest_2026-04-29.md
python email_digest.py --md report.md     # file custom
python email_digest.py --days 14          # ultimi 14 giorni
```

## Skill definition (skill.md)

Trigger: `/email-digest`, "digest email", "leggi email settimana", "sintesi email".  
Esegue: `cd ".claude/skills/email-digest" && python email_digest.py [args]`

## Gestione errori

| Caso | Comportamento |
|---|---|
| `GMAIL_APP_PASSWORD` mancante | Exit con messaggio chiaro |
| Connessione IMAP fallita | Exit con errore |
| Nessuna email nel periodo | Messaggio "Nessuna email negli ultimi N giorni" |
| Email con encoding anomalo | Skip con warning, continua |

## Vincoli

- Solo INBOX (no Spam, Sent, ecc.)
- Body snippet: primi 200 caratteri del testo plain
- Max 500 email per performance (IMAP SEARCH già filtra per data)
- Link Gmail funzionano solo se autenticato nel browser
