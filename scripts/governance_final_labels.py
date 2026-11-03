"""Final labels for the governance-rationale annotation (route 2), after arbitration.

Usage, from the repository root:  python scripts/governance_final_labels.py
Reads annotation/researcher_labels.csv and annotation/arbitration.csv. For each unit and label,
the final label is the researcher's label where the researcher and the model agreed, and the
arbitrated label where they disagreed. Writes annotation/final_labels.csv and
results/governance_final_summary.json (distribution of each label overall, for the six changes
made through governance votes in 2023-2024, A01-A06, and for the ten made through the Risk
Steward process in 2025, A07-A16).
"""
import csv
import json
import os
from collections import Counter

LABELS = ('rationale', 'kink_framing', 'temporary')
GROUPS = {'all': [f'A{i:02d}' for i in range(1, 17)],
          'governance_votes_2023_2024': [f'A{i:02d}' for i in range(1, 7)],
          'risk_steward_2025': [f'A{i:02d}' for i in range(7, 17)]}


def main():
    with open('annotation/researcher_labels.csv', newline='', encoding='utf-8') as f:
        researcher = {r['action']: r for r in csv.DictReader(f)}
    with open('annotation/llm_labels.csv', newline='', encoding='utf-8') as f:
        model = {r['action']: r for r in csv.DictReader(f)}
    with open('annotation/arbitration.csv', newline='', encoding='utf-8') as f:
        arbitration = {(r['action'], r['label']): r for r in csv.DictReader(f)}

    final = []
    for action in GROUPS['all']:
        row = {'action': action}
        for label in LABELS:
            a, b = researcher[action][label], model[action][label]
            key = (action, label)
            if a == b:
                if key in arbitration:
                    raise SystemExit(f'{key} was arbitrated although both labels agree.')
                row[label], row[f'{label}_source'] = a, 'agreement'
            else:
                if key not in arbitration:
                    raise SystemExit(f'{key} is a disagreement without an arbitration record.')
                arb = arbitration[key]
                if (arb['researcher'], arb['model']) != (a, b):
                    raise SystemExit(f'{key}: arbitration record does not match the label files.')
                row[label] = arb['final']
                row[f'{label}_source'] = ('researcher' if arb['final'] == a else
                                          'model' if arb['final'] == b else 'neither')
        final.append(row)
    unused = set(arbitration) - {(r['action'], l) for r in final for l in LABELS
                                  if researcher[r['action']][l] != model[r['action']][l]}
    if unused:
        raise SystemExit(f'Arbitration records without a disagreement: {sorted(unused)}')

    with open('annotation/final_labels.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(final[0]))
        w.writeheader()
        w.writerows(final)

    by_action = {r['action']: r for r in final}
    summary = {g: {l: dict(Counter(by_action[a][l] for a in acts).most_common()) for l in LABELS}
               for g, acts in GROUPS.items()}
    summary['arbitration_outcomes'] = dict(Counter(r[f'{l}_source'] for r in final for l in LABELS
                                                   if r[f'{l}_source'] != 'agreement'))
    os.makedirs('results', exist_ok=True)
    with open('results/governance_final_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    for g in GROUPS:
        print(g)
        for l in LABELS:
            print(f'  {l:13} {summary[g][l]}')
    print('arbitration outcomes:', summary['arbitration_outcomes'])
    print('Saved annotation/final_labels.csv and results/governance_final_summary.json')


if __name__ == '__main__':
    main()
