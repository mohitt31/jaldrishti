"""Summarise consented human observations; never infer scores or silently drop failures."""
import argparse
import json
import statistics
from pathlib import Path

TASKS = {t['id']: t for t in json.loads((Path(__file__).resolve().parents[1] / 'reports/user_pilot/packet/tasks.json').read_text())['tasks']}


def summarize(records):
    seen = set()
    conditions = {c: {'attempted': 0, 'correct_unassisted': 0, 'unscored': 0, 'timeouts': 0, 'assisted': 0, 'interrupted': 0} for c in 'AB'}
    pairs = {}
    for r in records:
        if r.get('kind') != 'human' or r.get('consent') is not True:
            raise ValueError('Only consented human records may enter a pilot summary; synthetic checks are not participants.')
        if r.get('packet') != 'pilot-v1' or r.get('round') != 'initial':
            raise ValueError('Use the locked initial packet only; retests need a separate report and protocol.')
        pid, tid, cond = r.get('participant_id'), r.get('task_id'), r.get('condition')
        if not isinstance(pid, str) or not pid.startswith('P') or not pid[1:].isdigit() or tid not in TASKS or cond not in conditions:
            raise ValueError('Invalid participant, task or condition')
        key = (pid, tid)
        if key in seen: raise ValueError('Duplicate attempt; do not replace or combine retests')
        seen.add(key)
        duration = r.get('elapsed_seconds')
        if not isinstance(duration, (float, int)) or isinstance(duration, bool) or not 0 <= duration < 86400:
            raise ValueError('Invalid elapsed time')
        if r.get('status') not in ('completed', 'timeout', 'interrupted'): raise ValueError('Invalid status')
        if not isinstance(r.get('assisted'), bool): raise ValueError('Record whether assistance occurred')
        criteria = r.get('criteria', {})
        if set(criteria) != set(TASKS[tid]['criteria']) or any(v not in ('yes', 'no', 'pending') for v in criteria.values()):
            raise ValueError('Complete the task-specific rubric; unknown fields are not scores')
        if not r.get('build') or not r.get('snapshot'): raise ValueError('Missing build/snapshot identity')
        c = conditions[cond]; c['attempted'] += 1
        c['unscored'] += 'pending' in criteria.values()
        c['timeouts'] += r['status'] == 'timeout' or duration > 240
        c['interrupted'] += r['status'] == 'interrupted'
        c['assisted'] += r['assisted']
        correct = r['status'] == 'completed' and duration <= 240 and not r['assisted'] and all(v == 'yes' for v in criteria.values())
        c['correct_unassisted'] += correct
        pkey = (pid, TASKS[tid]['pair'])
        if cond in pairs.setdefault(pkey, {}): raise ValueError('Duplicate condition in a task pair')
        pairs[pkey][cond] = {'correct': correct, 'seconds': duration, 'instance': TASKS[tid]['instance']}
    matched = []
    for (pid, pair), p in pairs.items():
        if set(p) == {'A','B'}:
            if p['A']['instance'] == p['B']['instance']: raise ValueError('Same instance in both conditions; allocation violation')
            if p['A']['correct'] and p['B']['correct']:
                matched.append({'participant_id': pid, 'pair': pair, 'A_seconds': p['A']['seconds'], 'B_seconds': p['B']['seconds'], 'A_minus_B_seconds': p['A']['seconds']-p['B']['seconds']})
    return {'label': 'small formative pilot; developer-authored tasks and scoring; no population inference', 'status': 'no sessions' if not records else 'scoring incomplete' if any(c['unscored'] for c in conditions.values()) else 'descriptive only', 'participants': len({r['participant_id'] for r in records}), 'conditions': conditions, 'paired_correct_only': matched, 'paired_denominator': len(matched), 'median_paired_A_minus_B_seconds': statistics.median(x['A_minus_B_seconds'] for x in matched) if matched else None, 'limitations': ['Failures, timeouts, assistance and interrupted attempts retained in denominators.', 'Paired times include only both-correct unassisted pairs; not unconditional time savings.', 'Source/task familiarity, fixed category order and convenience recruitment can bias outcomes.']}

if __name__ == '__main__':
    p = argparse.ArgumentParser();p.add_argument('input', type=Path);p.add_argument('--output', type=Path, required=True);a=p.parse_args()
    data=json.loads(a.input.read_text()); report=summarize(data['records']);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print(report['status'])
