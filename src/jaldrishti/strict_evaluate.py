"""Tuple-level development scoring; never changes the frozen v0.1/v0.2 scorer."""
from __future__ import annotations
import re
from decimal import Decimal, InvalidOperation
from .gazetteer import compact, norm
from .question import _dates


def period_key(value):
    if not value or norm(value) == 'unknown': return None
    s = norm(value)
    if re.fullmatch(r'\d{4}-\d{2}(?:-\d{2})?', s): return s
    dates = _dates(s)
    if dates: return dates[0]
    return compact(s)


def unit_key(value):
    s = norm(value).replace('μ', 'µ')
    return {'ppb': 'µg/l', 'ppm': 'mg/l'}.get(s, s)


def tuple_checks(item, fact, annotations=None):
    """Report every failed field. UNKNOWN sampling time must remain unknown."""
    gold = dict(fact) | (annotations or {})
    try:
        equal_value = Decimal(str(item.get('value')).replace(',', '')) == Decimal(str(gold['value']).replace(',', ''))
    except (InvalidOperation, ValueError): equal_value = False
    place = norm(gold.get('block_or_village', ''))
    item_place = norm(item.get('location') or item.get('place') or '')
    stat = lambda s: {'min': 'range_min', 'max': 'range_max'}.get(s, s)
    checks = {
        'value': equal_value,
        'unit': unit_key(item.get('unit', '')) == unit_key(gold.get('unit', '')),
        'contaminant': item.get('contaminant') == gold.get('contaminant'),
        'district': norm(item.get('district')) == norm(gold.get('district')),
        'location': not place or bool(re.search(r'(?<!\w)' + re.escape(place) + r'(?!\w)', item_place)),
        'statistic': stat(item.get('statistic')) == stat(gold.get('statistic')),
        'sampling_period': period_key(item.get('date') or item.get('period')) == period_key(gold.get('sampling_period')),
        'source_url': item.get('url') == gold.get('source_url'),
        'physical_page': str(item.get('page')) == str(gold.get('pdf_page_number')),
        'page_verified': item.get('page_verified') is True,
    }
    for field in ('well_id', 'source_type', 'aquifer'):
        if field in (annotations or {}): checks[field] = compact(item.get(field) or '') == compact(gold[field] or '')
    return checks


def score_strict(question, answer, facts, annotations=None):
    annotations = annotations or {}
    ids = [x for x in question['supporting_fact_ids'].split(';') if x]
    items = answer.get('items', [])
    pairs = [[tuple_checks(i, facts[f], annotations.get(f)) for f in ids] for i in items]
    matches = [[all(c.values()) for c in row] for row in pairs]
    covered = all(any(row[j] for row in matches) for j in range(len(ids)))
    no_extra = all(any(row) for row in matches)
    expected = question['expected_answer_type']
    type_ok = answer.get('answer_type') == expected
    if expected == 'insufficient_evidence': correct = type_ok and not items
    else:
        correct = type_ok and bool(ids) and covered and no_extra
        if expected == 'not_comparable': correct = correct and len(items) == 2 and bool(answer.get('reasons'))
    return {'id': question['question_id'], 'correct': correct, 'type_ok': type_ok,
            'all_gold_tuples_covered': covered, 'no_extra_items': no_extra,
            'items': [{'matches': [f for f,ok in zip(ids,row) if ok],
                       'failures_by_fact': {f: [k for k,v in c.items() if not v] for f,c in zip(ids,checks)}}
                      for row,checks in zip(matches,pairs)]}
