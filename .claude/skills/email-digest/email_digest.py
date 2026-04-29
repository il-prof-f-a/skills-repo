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


def classify(subject: str, sender: str) -> tuple:
    subject_lower = subject.lower()
    sender_lower = sender.lower()

    if any(k in subject_lower for k in ALTA_KEYWORDS):
        priority = 'Alta'
    elif any(k in sender_lower for k in BASSA_SENDERS):
        priority = 'Bassa'
    else:
        priority = 'Media'

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
