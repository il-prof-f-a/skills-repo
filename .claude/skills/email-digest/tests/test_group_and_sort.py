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
