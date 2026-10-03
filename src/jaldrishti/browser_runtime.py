"""Offline browser adapter: identical Engine, verification snapshotted at build time."""
from .answer import Engine

class BrowserRuntime:
    def __init__(self, data):
        self.data = data
        self.records = {e['id']: e for e in data['evidence']}
        self.engines = {}
        for scope in ('library', 'reference'):
            allowed = set(data['scopes'][scope])
            self.engines[scope] = Engine([e for e in data['evidence'] if e['doc'] in allowed], data['metas'], self.verify)

    def verify(self, item, meta):
        record = self.records.get(item.get('evidence_id'))
        return bool(record and record.get('page_verified'))

    def ask(self, question, scope='library'):
        if scope not in self.engines: raise ValueError('Unknown evidence scope')
        if not isinstance(question, str) or not question.strip(): raise ValueError('Enter a question')
        if len(question) > 2000: raise ValueError('Question must be at most 2000 characters')
        return self.engines[scope].ask(question)
