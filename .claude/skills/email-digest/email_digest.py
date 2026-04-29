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
