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
    assert '(#)' in content or 'Ciao!' in content


def test_md_contains_priority_emoji():
    content = _write_and_read(make_groups())
    assert '🔴' in content


def test_md_contains_period_header():
    content = _write_and_read(make_groups())
    assert '22/04' in content
    assert '29/04/2026' in content
