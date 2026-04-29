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
