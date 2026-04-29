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
