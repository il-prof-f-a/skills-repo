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
    _, priority = classify('Urgente: verifica account', 'noreply@bank.com')
    assert priority == 'Alta'
