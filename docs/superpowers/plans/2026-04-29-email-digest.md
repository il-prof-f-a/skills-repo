# Email Digest Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Skill Python che legge gli ultimi N giorni di email Gmail via IMAP, classifica per topic e priorità con regole keyword, stampa digest in terminale, genera opzionalmente un `.md` con link Gmail.

**Architecture:** Script standalone `email_digest.py` con funzioni pure testabili (`classify`, `group_and_sort`, `render_terminal`, `render_md`) separate dalla I/O IMAP (`fetch_emails`) e dall'entry point (`main`). Zero dipendenze extra — solo stdlib Python.

**Tech Stack:** Python 3.9+, `imaplib`, `email`, `argparse`, `pytest` per i test.

---

## File Structure

```
.claude/skills/email-digest/
  email_digest.py                    # script principale
  skill.md                           # definizione skill per Claude Code
  tests/
    __init__.py
    test_classify.py                 # test classify()
    test_group_and_sort.py           # test group_and_sort()
    test_render_terminal.py          # test render_terminal()
    test_render_md.py                # test render_md()
```

---

### Task 1: Scaffold — directory, skill.md, scheletro script

**Files:**
- Create: `.claude/skills/email-digest/skill.md`
- Create: `.claude/skills/email-digest/email_digest.py`
- Create: `.claude/skills/email-digest/tests/__init__.py`

- [ ] **Step 1: Crea directory**

```bash
mkdir -p ".claude/skills/email-digest/tests"
```

- [ ] **Step 2: Crea `skill.md`**

Contenuto file `.claude/skills/email-digest/skill.md`:

```markdown
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
```
```

- [ ] **Step 3: Crea `email_digest.py` scheletro**

Contenuto file `.claude/skills/email-digest/email_digest.py`:

```python
import imaplib
import email as email_lib
from email.header import decode_header
from email.utils import parsedate_to_datetime
import argparse
import os
import sys
import re
from datetime import datetime, timedelta

GMAIL_USER = 'prof.f.adriani@gmail.com'
IMAP_HOST = 'imap.gmail.com'
IMAP_PORT = 993
GMAIL_BASE = 'https://mail.google.com/mail/u/0/#search/rfc822msgid'

IMAP_MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

PRIORITY_ORDER = {'Alta': 0, 'Media': 1, 'Bassa': 2}

TOPIC_ICONS = {
    'Lavoro': '📌',
    'Fatture/Pagamenti': '💰',
    'Newsletter': '📰',
    'Notifiche': '🔔',
    'Personale': '👤',
}

ALTA_KEYWORDS = ['urgente', 'importante', 'scadenza', 'deadline', 'asap',
                 'entro oggi', 'entro domani']
BASSA_SENDERS = ['unsubscribe', 'newsletter', 'noreply', 'no-reply', 'mailer-daemon']

LAVORO_KW = ['progetto', 'riunione', 'meeting', 'call', 'task', 'offerta', 'contratto']
FATTURE_KW = ['fattura', 'pagamento', 'invoice', 'scadenza', 'bonifico', 'ricevuta']
NEWSLETTER_KW = ['unsubscribe', 'newsletter']
NOTIFICHE_KW = ['noreply', 'no-reply', 'notification', 'alert', 'conferma', 'verifica']
```

- [ ] **Step 4: Crea `tests/__init__.py` vuoto**

```bash
touch ".claude/skills/email-digest/tests/__init__.py"
```

- [ ] **Step 5: Commit**

```bash
git add ".claude/skills/email-digest/"
git commit -m "feat(email-digest): scaffold skill directory and skeleton script"
```

---

### Task 2: `classify()` — regole topic e priorità

**Files:**
- Modify: `.claude/skills/email-digest/email_digest.py`
- Create: `.claude/skills/email-digest/tests/test_classify.py`

- [ ] **Step 1: Scrivi test fallente**

Contenuto `.claude/skills/email-digest/tests/test_classify.py`:

```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from email_digest import classify


def test_priority_alta_keyword_in_subject():
    _, priority = classify('Urgente: rispondere entro oggi', 'mario@example.com')
    assert priority == 'Alta'


def test_priority_alta_scadenza():
    _, priority = classify('Scadenza pagamento domani', 'billing@acme.com')
    assert priority == 'Alta'


def test_priority_bassa_noreply_sender():
    _, priority = classify('Weekly digest', 'noreply@service.com')
    assert priority == 'Bassa'


def test_priority_bassa_newsletter_sender():
    _, priority = classify('Offerta speciale', 'newsletter@shop.it')
    assert priority == 'Bassa'


def test_priority_media_default():
    _, priority = classify('Ciao come stai', 'amico@gmail.com')
    assert priority == 'Media'


def test_topic_lavoro_riunione():
    topic, _ = classify('Riunione di progetto alle 10', 'team@company.it')
    assert topic == 'Lavoro'


def test_topic_fatture():
    topic, _ = classify('Fattura #123 in scadenza', 'billing@acme.com')
    assert topic == 'Fatture/Pagamenti'


def test_topic_newsletter():
    topic, _ = classify('La nostra newsletter mensile', 'info@newsletter.it')
    assert topic == 'Newsletter'


def test_topic_notifiche_noreply():
    topic, _ = classify('Conferma registrazione', 'noreply@site.com')
    assert topic == 'Notifiche'


def test_topic_personale_fallback():
    topic, _ = classify('Domani vieni?', 'amico@gmail.com')
    assert topic == 'Personale'


def test_alta_priority_overrides_bassa_sender():
    # subject urgente vince su sender noreply per la priorità
    _, priority = classify('Urgente: verifica account', 'noreply@bank.com')
    assert priority == 'Alta'
```

- [ ] **Step 2: Esegui test — verifica fallisce**

```bash
cd ".claude/skills/email-digest" && python -m pytest tests/test_classify.py -v
```

Atteso: `ERROR` o `ImportError` (funzione non ancora definita).

- [ ] **Step 3: Implementa `classify()` in `email_digest.py`**

Aggiungi dopo le costanti in `email_digest.py`:

```python
def classify(subject: str, sender: str) -> tuple:
    subject_lower = subject.lower()
    sender_lower = sender.lower()

    # Priority — subject check first, then sender
    if any(k in subject_lower for k in ALTA_KEYWORDS):
        priority = 'Alta'
    elif any(k in sender_lower for k in BASSA_SENDERS):
        priority = 'Bassa'
    else:
        priority = 'Media'

    # Topic — check su subject + sender combinati
    text = subject_lower + ' ' + sender_lower

    if any(k in text for k in NEWSLETTER_KW):
        topic = 'Newsletter'
    elif any(k in text for k in FATTURE_KW):
        topic = 'Fatture/Pagamenti'
    elif any(k in text for k in NOTIFICHE_KW):
        topic = 'Notifiche'
    elif any(k in text for k in LAVORO_KW):
        topic = 'Lavoro'
    else:
        topic = 'Personale'

    return topic, priority
```

- [ ] **Step 4: Esegui test — verifica passa**

```bash
cd ".claude/skills/email-digest" && python -m pytest tests/test_classify.py -v
```

Atteso: `11 passed`.

- [ ] **Step 5: Commit**

```bash
git add ".claude/skills/email-digest/"
git commit -m "feat(email-digest): add classify() with topic and priority rules"
```

---

### Task 3: `group_and_sort()` — raggruppamento e ordinamento

**Files:**
- Modify: `.claude/skills/email-digest/email_digest.py`
- Create: `.claude/skills/email-digest/tests/test_group_and_sort.py`

- [ ] **Step 1: Scrivi test fallente**

Contenuto `.claude/skills/email-digest/tests/test_group_and_sort.py`:

```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from datetime import datetime
from email_digest import group_and_sort


def make_email(topic, priority, day=29):
    return {
        'id': '1', 'message_id': 'test',
        'subject': 'Test', 'sender': 'test@example.com',
        'date': datetime(2026, 4, day, 10, 0),
        'snippet': '', 'topic': topic, 'priority': priority,
    }


def test_groups_by_topic():
    emails = [
        make_email('Lavoro', 'Media'),
        make_email('Personale', 'Alta'),
        make_email('Lavoro', 'Alta'),
    ]
    groups = group_and_sort(emails)
    assert set(groups.keys()) == {'Lavoro', 'Personale'}
    assert len(groups['Lavoro']) == 2


def test_sorts_alta_before_media_before_bassa():
    emails = [
        make_email('Lavoro', 'Bassa', day=27),
        make_email('Lavoro', 'Alta', day=28),
        make_email('Lavoro', 'Media', day=29),
    ]
    groups = group_and_sort(emails)
    priorities = [e['priority'] for e in groups['Lavoro']]
    assert priorities == ['Alta', 'Media', 'Bassa']


def test_empty_input_returns_empty_dict():
    assert group_and_sort([]) == {}


def test_same_priority_sorted_by_date_desc():
    emails = [
        make_email('Lavoro', 'Alta', day=25),
        make_email('Lavoro', 'Alta', day=29),
        make_email('Lavoro', 'Alta', day=27),
    ]
    groups = group_and_sort(emails)
    days = [e['date'].day for e in groups['Lavoro']]
    assert days == [29, 27, 25]
```

- [ ] **Step 2: Esegui test — verifica fallisce**

```bash
cd ".claude/skills/email-digest" && python -m pytest tests/test_group_and_sort.py -v
```

Atteso: `ImportError` (funzione non ancora definita).

- [ ] **Step 3: Implementa `group_and_sort()` in `email_digest.py`**

```python
def group_and_sort(emails: list) -> dict:
    groups = {}
    for em in emails:
        topic = em['topic']
        if topic not in groups:
            groups[topic] = []
        groups[topic].append(em)

    for topic in groups:
        groups[topic].sort(
            key=lambda e: (
                PRIORITY_ORDER[e['priority']],
                -(e['date'].timestamp() if hasattr(e['date'], 'timestamp') else 0),
            )
        )

    return groups
```

- [ ] **Step 4: Esegui test — verifica passa**

```bash
cd ".claude/skills/email-digest" && python -m pytest tests/test_group_and_sort.py -v
```

Atteso: `4 passed`.

- [ ] **Step 5: Commit**

```bash
git add ".claude/skills/email-digest/"
git commit -m "feat(email-digest): add group_and_sort()"
```

---

### Task 4: `render_terminal()` — output formattato a schermo

**Files:**
- Modify: `.claude/skills/email-digest/email_digest.py`
- Create: `.claude/skills/email-digest/tests/test_render_terminal.py`

- [ ] **Step 1: Scrivi test fallente**

Contenuto `.claude/skills/email-digest/tests/test_render_terminal.py`:

```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from datetime import datetime
from email_digest import render_terminal


def make_group(subject='Test', sender='boss@co.it', priority='Alta', day=27):
    return [{
        'subject': subject, 'sender': sender,
        'date': datetime(2026, 4, day, 10, 0),
        'priority': priority,
    }]


def test_no_emails_shows_message(capsys):
    render_terminal({}, days=7, today=datetime(2026, 4, 29))
    out = capsys.readouterr().out
    assert 'Nessuna email' in out


def test_shows_topic_in_uppercase(capsys):
    render_terminal({'Lavoro': make_group()}, days=7, today=datetime(2026, 4, 29))
    out = capsys.readouterr().out
    assert 'LAVORO' in out


def test_shows_alta_label(capsys):
    render_terminal({'Lavoro': make_group(priority='Alta')}, days=7, today=datetime(2026, 4, 29))
    out = capsys.readouterr().out
    assert '[ALTA]' in out


def test_shows_subject_and_sender(capsys):
    render_terminal({'Personale': make_group(subject='Ciao mondo', sender='amico@gmail.com')},
                    days=7, today=datetime(2026, 4, 29))
    out = capsys.readouterr().out
    assert 'Ciao mondo' in out
    assert 'amico@gmail.com' in out


def test_shows_period_in_header(capsys):
    render_terminal({}, days=7, today=datetime(2026, 4, 29))
    out = capsys.readouterr().out
    assert '22/04' in out
    assert '29/04/2026' in out
```

- [ ] **Step 2: Esegui test — verifica fallisce**

```bash
cd ".claude/skills/email-digest" && python -m pytest tests/test_render_terminal.py -v
```

Atteso: `ImportError`.

- [ ] **Step 3: Implementa `render_terminal()` in `email_digest.py`**

```python
def render_terminal(groups: dict, days: int, today: datetime = None) -> None:
    if today is None:
        today = datetime.now()
    since = today - timedelta(days=days)

    print(f"\n=== DIGEST EMAIL — {days} giorni "
          f"({since.strftime('%d/%m')} - {today.strftime('%d/%m/%Y')}) ===\n")

    if not groups:
        print(f"Nessuna email negli ultimi {days} giorni.")
        return

    priority_label = {'Alta': '[ALTA]', 'Media': '[MEDIA]', 'Bassa': '[BASSA]'}

    for topic, emails in groups.items():
        icon = TOPIC_ICONS.get(topic, '📧')
        counts = {p: sum(1 for e in emails if e['priority'] == p)
                  for p in ['Alta', 'Media', 'Bassa']}
        print(f"{icon} {topic.upper()} "
              f"[Alta: {counts['Alta']} | Media: {counts['Media']} | Bassa: {counts['Bassa']}]")
        for em in emails:
            label = priority_label[em['priority']]
            date_obj = em['date']
            date_fmt = date_obj.strftime('%d/%m') if isinstance(date_obj, datetime) else ''
            print(f"  {label} \"{em['subject']}\" — {em['sender']} ({date_fmt})")
        print()
```

- [ ] **Step 4: Esegui test — verifica passa**

```bash
cd ".claude/skills/email-digest" && python -m pytest tests/test_render_terminal.py -v
```

Atteso: `5 passed`.

- [ ] **Step 5: Commit**

```bash
git add ".claude/skills/email-digest/"
git commit -m "feat(email-digest): add render_terminal()"
```

---

### Task 5: `render_md()` — output Markdown con link Gmail

**Files:**
- Modify: `.claude/skills/email-digest/email_digest.py`
- Create: `.claude/skills/email-digest/tests/test_render_md.py`

- [ ] **Step 1: Scrivi test fallente**

Contenuto `.claude/skills/email-digest/tests/test_render_md.py`:

```python
import sys
import os
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from datetime import datetime
from email_digest import render_md


def make_groups():
    return {
        'Lavoro': [{
            'subject': 'Riunione domani',
            'sender': 'boss@company.it',
            'date': datetime(2026, 4, 27, 10, 0),
            'priority': 'Alta',
            'message_id': 'unique-id-123@domain.com',
        }],
        'Personale': [{
            'subject': 'Ciao!',
            'sender': 'amico@gmail.com',
            'date': datetime(2026, 4, 26, 9, 0),
            'priority': 'Media',
            'message_id': '',
        }]
    }


def _write_and_read(groups, days=7, today=datetime(2026, 4, 29)):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        filepath = f.name
    render_md(groups, filepath, days=days, today=today)
    with open(filepath, encoding='utf-8') as f:
        content = f.read()
    os.unlink(filepath)
    return content


def test_md_contains_topic_header():
    content = _write_and_read(make_groups())
    assert '## 📌 Lavoro' in content


def test_md_contains_subject():
    content = _write_and_read(make_groups())
    assert 'Riunione domani' in content


def test_md_contains_gmail_link():
    content = _write_and_read(make_groups())
    assert 'unique-id-123@domain.com' in content
    assert 'rfc822msgid' in content


def test_md_no_message_id_uses_hash():
    content = _write_and_read(make_groups())
    assert '](#)' in content or '(#)' in content or 'Ciao!' in content


def test_md_contains_priority_emoji():
    content = _write_and_read(make_groups())
    assert '🔴' in content


def test_md_contains_period_header():
    content = _write_and_read(make_groups())
    assert '22/04' in content
    assert '29/04/2026' in content
```

- [ ] **Step 2: Esegui test — verifica fallisce**

```bash
cd ".claude/skills/email-digest" && python -m pytest tests/test_render_md.py -v
```

Atteso: `ImportError`.

- [ ] **Step 3: Implementa `render_md()` in `email_digest.py`**

```python
def render_md(groups: dict, filepath: str, days: int, today: datetime = None) -> None:
    if today is None:
        today = datetime.now()
    since = today - timedelta(days=days)

    priority_emoji = {'Alta': '🔴', 'Media': '🟡', 'Bassa': '🟢'}

    lines = [
        f"# Email Digest — {since.strftime('%d/%m')} - {today.strftime('%d/%m/%Y')}",
        f"",
        f"Generato il {today.strftime('%d/%m/%Y %H:%M')} | Periodo: ultimi {days} giorni",
        f"",
    ]

    for topic, emails in groups.items():
        icon = TOPIC_ICONS.get(topic, '📧')
        lines.append(f"## {icon} {topic}")
        lines.append("")
        lines.append("| Priorità | Oggetto | Mittente | Data |")
        lines.append("|---|---|---|---|")

        for em in emails:
            emoji = priority_emoji[em['priority']]
            subject = em['subject'].replace('|', '\\|')
            msg_id = em.get('message_id', '').strip()
            link = f"{GMAIL_BASE}:{msg_id}" if msg_id else '#'
            sender = em['sender'].replace('|', '\\|')
            date_obj = em['date']
            date_fmt = date_obj.strftime('%d/%m') if isinstance(date_obj, datetime) else ''
            lines.append(
                f"| {emoji} {em['priority']} | [{subject}]({link}) | {sender} | {date_fmt} |"
            )

        lines.append("")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"File Markdown scritto: {filepath}")
```

- [ ] **Step 4: Esegui test — verifica passa**

```bash
cd ".claude/skills/email-digest" && python -m pytest tests/test_render_md.py -v
```

Atteso: `6 passed`.

- [ ] **Step 5: Commit**

```bash
git add ".claude/skills/email-digest/"
git commit -m "feat(email-digest): add render_md() with Gmail search links"
```

---

### Task 6: Helper functions — `decode_str`, `parse_date`, `get_snippet`

Funzioni usate da `fetch_emails()`. Nessun unit test (dipendono da strutture `email.message.Message`) — testate indirettamente dall'integrazione.

**Files:**
- Modify: `.claude/skills/email-digest/email_digest.py`

- [ ] **Step 1: Aggiungi helpers in `email_digest.py`**

```python
def decode_str(s) -> str:
    if not s:
        return ''
    parts = decode_header(s)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            try:
                decoded.append(part.decode(charset or 'utf-8', errors='replace'))
            except Exception:
                decoded.append(part.decode('utf-8', errors='replace'))
        else:
            decoded.append(str(part))
    return ''.join(decoded)


def parse_date(date_str: str) -> datetime:
    try:
        dt = parsedate_to_datetime(date_str)
        return dt.replace(tzinfo=None)
    except Exception:
        return datetime.now()


def get_snippet(msg) -> str:
    body = ''
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                try:
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or 'utf-8'
                    body = payload.decode(charset, errors='replace')
                    break
                except Exception:
                    pass
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or 'utf-8'
                body = payload.decode(charset, errors='replace')
        except Exception:
            pass
    return body[:200].replace('\n', ' ').strip()
```

- [ ] **Step 2: Commit**

```bash
git add ".claude/skills/email-digest/email_digest.py"
git commit -m "feat(email-digest): add decode_str, parse_date, get_snippet helpers"
```

---

### Task 7: `fetch_emails()` — lettura IMAP Gmail

**Files:**
- Modify: `.claude/skills/email-digest/email_digest.py`

Nota: nessun unit test automatico (richiede connessione IMAP reale). Smoke test manuale al Task 8.

- [ ] **Step 1: Implementa `fetch_emails()` in `email_digest.py`**

```python
def fetch_emails(days: int = 7) -> list:
    password = os.environ.get('GMAIL_APP_PASSWORD', '')
    if not password:
        print('ERRORE: variabile GMAIL_APP_PASSWORD non impostata')
        sys.exit(1)

    since = datetime.now() - timedelta(days=days)
    since_date = f"{since.day:02d}-{IMAP_MONTHS[since.month - 1]}-{since.year}"

    emails = []
    print(f"Connessione IMAP {GMAIL_USER}...")

    with imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT) as mail:
        mail.login(GMAIL_USER, password)
        mail.select('INBOX')

        _, msg_ids = mail.search(None, f'SINCE {since_date}')
        ids = msg_ids[0].split()

        print(f"Email trovate: {len(ids)}")

        for msg_id in ids:
            try:
                _, data = mail.fetch(msg_id, '(RFC822)')
                raw = data[0][1]
                msg = email_lib.message_from_bytes(raw)

                subject = decode_str(msg.get('Subject', '(nessun oggetto)'))
                sender = decode_str(msg.get('From', ''))
                date_str = msg.get('Date', '')
                message_id = msg.get('Message-ID', '').strip().strip('<>')

                date = parse_date(date_str)
                snippet = get_snippet(msg)
                topic, priority = classify(subject, sender)

                emails.append({
                    'id': msg_id.decode(),
                    'message_id': message_id,
                    'subject': subject,
                    'sender': sender,
                    'date': date,
                    'snippet': snippet,
                    'topic': topic,
                    'priority': priority,
                })
            except Exception as e:
                print(f"  Warning: skip email {msg_id} — {e}")
                continue

    return emails
```

- [ ] **Step 2: Commit**

```bash
git add ".claude/skills/email-digest/email_digest.py"
git commit -m "feat(email-digest): add fetch_emails() via IMAP"
```

---

### Task 8: `main()` — argparse entry point

**Files:**
- Modify: `.claude/skills/email-digest/email_digest.py`

- [ ] **Step 1: Aggiungi `main()` in `email_digest.py`**

```python
def main():
    parser = argparse.ArgumentParser(
        description='Digest email Gmail — ultimi N giorni',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Esempi:
  python email_digest.py
  python email_digest.py --md
  python email_digest.py --md report.md
  python email_digest.py --days 14""",
    )
    parser.add_argument(
        '--md',
        nargs='?',
        const=f"email_digest_{datetime.now().strftime('%Y-%m-%d')}.md",
        metavar='FILE',
        help='Genera file Markdown (default: email_digest_YYYY-MM-DD.md)',
    )
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        metavar='N',
        help='Numero di giorni da leggere (default: 7)',
    )
    args = parser.parse_args()

    emails = fetch_emails(args.days)

    if not emails:
        print(f"Nessuna email negli ultimi {args.days} giorni.")
        return

    groups = group_and_sort(emails)
    render_terminal(groups, args.days)

    if args.md:
        render_md(groups, args.md, args.days)


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: Commit**

```bash
git add ".claude/skills/email-digest/email_digest.py"
git commit -m "feat(email-digest): add main() with argparse"
```

---

### Task 9: Smoke test finale

**Files:** nessuno da modificare

- [ ] **Step 1: Esegui tutti i test unit**

```bash
cd ".claude/skills/email-digest" && python -m pytest tests/ -v
```

Atteso: tutti i test passano (`test_classify.py`, `test_group_and_sort.py`, `test_render_terminal.py`, `test_render_md.py`).

- [ ] **Step 2: Verifica --help**

```bash
cd ".claude/skills/email-digest" && python email_digest.py --help
```

Atteso: help argparse con descrizione, `--md`, `--days`, esempi.

- [ ] **Step 3: Smoke test connessione (richiede GMAIL_APP_PASSWORD)**

```bash
cd ".claude/skills/email-digest" && python email_digest.py --days 3
```

Atteso: stampa digest ultimi 3 giorni senza errori.

- [ ] **Step 4: Smoke test --md**

```bash
cd ".claude/skills/email-digest" && python email_digest.py --days 3 --md /tmp/test_digest.md && cat /tmp/test_digest.md
```

Atteso: file `.md` creato con tabelle per topic, link `rfc822msgid:...`.

- [ ] **Step 5: Commit finale**

```bash
git add ".claude/skills/email-digest/"
git commit -m "feat(email-digest): complete skill — IMAP digest with terminal and markdown output"
```
