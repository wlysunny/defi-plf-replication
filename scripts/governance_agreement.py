"""Agreement between the researcher's and the model's independent labels (route 2).

Usage, from the repository root:  python scripts/governance_agreement.py
Writes results/governance_agreement.json: for each label, percentage agreement, Cohen's kappa and
the confusion table, computed on the labels before arbitration. INVALID model replies are kept as
a model-only category (counted as disagreements); kappa is null where it is undefined.
"""
import csv
import json
import os
from collections import Counter


EXPECTED = {f'A{i:02d}' for i in range(1, 17)}
ALLOWED = {'rationale': {'LIQUIDITY_BUFFER', 'CAPITAL_EFFICIENCY', 'RATE_STABILITY', 'ALIGNMENT', 'OTHER', 'NOT_STATED'},
           'kink_framing': {'SETTLE_AT', 'KEEP_BELOW', 'PARAMETER_ONLY'},
           'temporary': {'yes', 'no'}}


def read(path, allow_invalid):
    with open(path, newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    actions = [r['action'].strip() for r in rows]
    duplicates = sorted({a for a in actions if actions.count(a) > 1})
    if duplicates:
        raise SystemExit(f'{path}: duplicate units {duplicates}')
    if set(actions) != EXPECTED:
        raise SystemExit(f'{path}: units differ from A01-A16 (missing {sorted(EXPECTED - set(actions))}, '
                         f'extra {sorted(set(actions) - EXPECTED)})')
    for r in rows:
        for label, allowed in ALLOWED.items():
            value = r[label].strip()
            if value not in allowed and not (allow_invalid and value == 'INVALID'):
                raise SystemExit(f'{path}: {r["action"]} has invalid {label} {value!r}')
    return {r['action'].strip(): r for r in rows}


def cohen_kappa(a, b):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / n ** 2
    return None if pe == 1 else (po - pe) / (1 - pe)


def main():
    researcher = read('annotation/researcher_labels.csv', allow_invalid=False)
    model = read('annotation/llm_labels.csv', allow_invalid=True)
    actions = sorted(EXPECTED)
    out = {}
    for label in ('rationale', 'kink_framing', 'temporary'):
        a = [researcher[x][label].strip() for x in actions]
        b = [model[x][label].strip() for x in actions]
        out[label] = {
            'n': len(actions),
            'agreement': sum(x == y for x, y in zip(a, b)),
            'percent_agreement': round(100 * sum(x == y for x, y in zip(a, b)) / len(actions), 1),
            'cohen_kappa': None if cohen_kappa(a, b) is None else round(cohen_kappa(a, b), 3),
            'confusion_researcher_by_model': {f'{x} | {y}': c for (x, y), c in sorted(Counter(zip(a, b)).items())},
            'disagreements': [x for x, p, q in zip(actions, a, b) if p != q],
        }
        k = out[label]['cohen_kappa']
        print(f"{label:18} agreement {out[label]['agreement']}/{len(actions)}  kappa {k}  "
              f"disagreements {out[label]['disagreements']}")
    os.makedirs('results', exist_ok=True)
    with open('results/governance_agreement.json', 'w') as f:
        json.dump(out, f, indent=2)
    print('Saved results/governance_agreement.json')


if __name__ == '__main__':
    main()
