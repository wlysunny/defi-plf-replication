"""
Compare the replicated UIP regression results with the original authors'
saved notebook output, pair by pair.

The original notebook on the `master` branch still contains the authors'
executed output, which matches Tables A2-A5 of the paper and gives unrounded
p-values. This script reads that output and the output of the replicated
notebook on the current branch, and reports for each of the four regressions
(daily/weekly x borrow/supply):

- differences in the number of observations,
- the number of pairs for which UIP (strict form) is rejected at 1% and 5%,
- the pairs whose test decision differs between the two runs.

It also writes all pair-level values to results/uip_comparison.csv.

Run from the repository root after executing 5_uip_compound.ipynb:
    python compare_uip.py
"""

import csv
import json
import os
import re
import subprocess

NOTEBOOK = 'notebooks/compound/5_uip_compound.ipynb'
ORIGINAL_REF = 'master'
REGRESSIONS = [('D', 'borrow'), ('D', 'supply'), ('W', 'borrow'), ('W', 'supply')]
THRESHOLDS = (0.01, 0.05)
OUT_PATH = 'results/uip_comparison.csv'


def load_notebook(ref=None):
    if ref is None:
        with open(NOTEBOOK) as f:
            return json.load(f)
    raw = subprocess.run(['git', 'show', f'{ref}:{NOTEBOOK}'],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(raw)


def cell_output(nb, frequency, side):
    call = f"regression_runner(frequency='{frequency}', side='{side}')"
    for cell in nb['cells']:
        if cell['cell_type'] == 'code' and call in ''.join(cell['source']):
            text = ''
            for o in cell.get('outputs', []):
                text += ''.join(o.get('text', '')) or ''.join(o.get('data', {}).get('text/plain', ''))
            return text
    raise ValueError(f'No output found for {call}')


def parse_output(text):
    """Return {pair: {'n', 'beta', 'p'}} from one regression's printed output."""
    pvalues = {}
    for block in re.findall(r'UIP (?:holds|does not hold): (\{.*\})', text):
        for pair, value in re.findall(r"'(\w+)': (?:np\.float64\(|array\()([0-9.eE+\-]+)", block):
            pvalues[pair] = float(value)
    rows = {}
    for line in text.splitlines():
        cells = [c.strip().replace('\\_', '_') for c in line.rstrip(' \\').split('&')]
        if len(cells) >= 9 and cells[0] in pvalues and cells[1].strip():
            rows[cells[0]] = {'n': int(cells[1]), 'beta': float(cells[3]), 'p': pvalues[cells[0]]}
    return rows


def main():
    original_nb = load_notebook(ORIGINAL_REF)
    replicated_nb = load_notebook()
    table = []
    for frequency, side in REGRESSIONS:
        name = f"{'daily' if frequency == 'D' else 'weekly'} {side}"
        orig = parse_output(cell_output(original_nb, frequency, side))
        repl = parse_output(cell_output(replicated_nb, frequency, side))
        pairs = [p for p in orig if p in repl]
        print(f'\n{name}: {len(pairs)} pairs compared')
        n_diff = {p: repl[p]['n'] - orig[p]['n'] for p in pairs if repl[p]['n'] != orig[p]['n']}
        print(f'  observations differing (replication minus original): {n_diff or "none"}')
        for t in THRESHOLDS:
            o_rej = {p for p in pairs if orig[p]['p'] < t}
            r_rej = {p for p in pairs if repl[p]['p'] < t}
            differ = sorted(o_rej ^ r_rej)
            print(f'  {int(t * 100)}% level: original rejects {len(o_rej)}, replication rejects {len(r_rej)}, '
                  f'same decision for {len(pairs) - len(differ)}/{len(pairs)}; differing: {differ or "none"}')
        for p in pairs:
            table.append([name, p, orig[p]['n'], repl[p]['n'], orig[p]['beta'], repl[p]['beta'],
                          orig[p]['p'], repl[p]['p']])
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['regression', 'pair', 'n_original', 'n_replication', 'beta_original',
                         'beta_replication', 'p_strict_original', 'p_strict_replication'])
        writer.writerows(table)
    print(f'\nPair-level comparison written to {OUT_PATH}')


if __name__ == '__main__':
    main()
