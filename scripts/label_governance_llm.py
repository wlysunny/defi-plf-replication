"""Label the governance-rationale units with a locally run open-weight model (route 2).

Codebook: analysis_plans/governance_rationale_codebook.md. Requires Ollama running locally with
qwen2.5:7b-instruct pulled. Usage, from the repository root:
    python scripts/label_governance_llm.py

Refuses to run unless annotation/researcher_labels.csv is complete and committed, and unless the
units, the codebook and this script are unchanged since the commit that added those labels, so that
the model's output cannot be seen before the researcher's labels are fixed and both label sets rest
on the same texts and rules. Refuses to overwrite existing outputs. Each request and response is
appended to the raw file as soon as it is received. Writes
annotation/llm_raw_outputs.jsonl (every request and response) and annotation/llm_labels.csv.
"""
import csv
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

import requests

OLLAMA = 'http://localhost:11434'
MODEL = 'qwen2.5:7b-instruct'
OPTIONS = {'temperature': 0, 'seed': 8240, 'num_ctx': 8192}
UNITS = 'data/governance/units.jsonl'
RESEARCHER = 'annotation/researcher_labels.csv'
CODEBOOK_PATH = 'analysis_plans/governance_rationale_codebook.md'
RAW_OUT = 'annotation/llm_raw_outputs.jsonl'
LABELS_OUT = 'annotation/llm_labels.csv'
RATIONALES = ['LIQUIDITY_BUFFER', 'CAPITAL_EFFICIENCY', 'RATE_STABILITY', 'ALIGNMENT', 'OTHER', 'NOT_STATED']
FRAMINGS = ['SETTLE_AT', 'KEEP_BELOW', 'PARAMETER_ONLY']
YES_NO = ['yes', 'no']

SYSTEM = """You are annotating governance forum posts from the Aave lending protocol. Each post proposes a change to the "optimal usage ratio" (also called UOptimal, Uopt, optimal ratio or kink) of an interest-rate model: the utilisation level above which the borrow rate rises steeply. Label what the text says, not whether the reason is correct or was accepted by others. Answer only with a JSON object."""

CODEBOOK = """Give three labels.

1. rationale: the main reason given for this change of the kink.
Consider the reason attached to the kink change itself: sentences about the optimal ratio, UOptimal, Uopt or kink, or a purpose stated for the whole proposal that applies to all of its parameter changes (for example "to be competitive"). A purpose that concerns something else (for example onboarding a different asset) does not count.
- LIQUIDITY_BUFFER: keep or restore room between the kink and full utilisation, so that suppliers can withdraw and liquidations can be carried out; reduce the risk of 100% utilisation. Typical wording: "mitigate liquidity risks", "capacity for liquidations", "liquidity buffer".
- CAPITAL_EFFICIENCY: let more of the supplied funds be borrowed before rates rise steeply; increase revenue, borrowing or competitiveness. Typical wording: "capital efficiency", "increase borrow revenue", "competitive".
- RATE_STABILITY: dampen borrow-rate spikes or volatility that occur when utilisation is above the kink, for example after large withdrawals. Typical wording: "reduce rate volatility", "mitigate rate spikes", "buffer market stability".
- ALIGNMENT: match the parameters used in other markets or for other assets, or restore a standard or previous value, with no other reason given. Typical wording: "align with other markets", "revert to its parameters from before", "standard target".
- OTHER: a reason is given for the kink change, but it fits none of the categories above.
- NOT_STATED: no reason is given for the kink change.
If several reasons are given, choose the one presented as the purpose of the kink change (for example after "to", "in order to", "aims to"); if several are so presented, choose the first. When one reason is presented as the means and another as its intended outcome, code the outcome that is stated; do not infer an unstated outcome from the mechanism. If the change covers several assets and the text gives different reasons for them, code the first reason given for a kink change. A vague reason that can be assigned to a category is coded with that category; NOT_STATED is used only when no reason for the kink change is given. For a change that reverses an earlier temporary change, label the reason given for the reversal: if the text says only that the earlier condition has ended and the previous or standard value is restored, use ALIGNMENT; if it gives another reason (for example restoring a liquidity buffer), use that.

2. kink_framing: how does the text frame the kink relative to utilisation?
- SETTLE_AT: the kink is described as the level at which utilisation settles, or is intended or expected to settle: an equilibrium or target utilisation. Typical wording: "equilibrium around the optimal utilization", "our utilization target", "standard target of 92%".
- KEEP_BELOW: utilisation is meant to stay below the kink, or utilisation above the kink is presented as the problem the change addresses, without the kink being described as a target or equilibrium. Typical wording: "stabilize borrows under the UOptimal point", "revert utilization below the kink", "utilization above Uoptimal".
- PARAMETER_ONLY: the kink is mentioned only as a parameter value, with no statement about where utilisation should be relative to it.
If a text contains both kinds of statement, code SETTLE_AT only if it explicitly calls the kink (or the new value) a target or equilibrium level of utilisation; otherwise code KEEP_BELOW. Mentioning the parameter's name ("optimal utilization") is not sufficient for either.

3. temporary: does the text say that this change is intended to be reversed later?
"yes" only if the change itself is described as temporary or short-term. A change that is a step in rolling back an earlier temporary change is "no" unless it is itself described as temporary.

Answer with a JSON object with exactly these keys:
{"rationale": one of LIQUIDITY_BUFFER, CAPITAL_EFFICIENCY, RATE_STABILITY, ALIGNMENT, OTHER, NOT_STATED,
 "kink_framing": one of SETTLE_AT, KEEP_BELOW, PARAMETER_ONLY,
 "temporary": "yes" or "no",
 "evidence": a short verbatim quote from the text supporting the rationale label, or "" if NOT_STATED}"""


def require_researcher_labels():
    with open(RESEARCHER, newline='') as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 16 or any(not r[c].strip() for r in rows for c in ('rationale', 'kink_framing', 'temporary')):
        sys.exit(f'{RESEARCHER} is not complete (16 rows, three labels each). Label all units first.')
    for r in rows:
        if r['rationale'].strip() not in RATIONALES or r['kink_framing'].strip() not in FRAMINGS \
                or r['temporary'].strip() not in YES_NO:
            sys.exit(f'{RESEARCHER}: invalid code in row {r["action"]}.')
    tracked = subprocess.run(['git', 'ls-files', '--error-unmatch', RESEARCHER], capture_output=True)
    changed = subprocess.run(['git', 'status', '--porcelain', '--', RESEARCHER], capture_output=True, text=True)
    if tracked.returncode != 0 or changed.stdout.strip():
        sys.exit(f'{RESEARCHER} must be committed, unchanged, before the model is run.')
    label_commit = subprocess.run(['git', 'log', '--diff-filter=AM', '-1', '--format=%H', '--', RESEARCHER],
                                  capture_output=True, text=True).stdout.strip()
    locked = [UNITS, CODEBOOK_PATH, os.path.relpath(os.path.abspath(__file__))]
    for path in locked:
        dirty = subprocess.run(['git', 'status', '--porcelain', '--', path], capture_output=True, text=True).stdout
        diff = subprocess.run(['git', 'diff', '--quiet', label_commit, 'HEAD', '--', path])
        exists = subprocess.run(['git', 'cat-file', '-e', f'{label_commit}:{path}'], capture_output=True)
        if dirty.strip() or diff.returncode != 0 or exists.returncode != 0:
            sys.exit(f'{path} differs from the version at the commit of the researcher labels ({label_commit[:7]}).')
    return label_commit


def model_digest():
    tags = requests.get(f'{OLLAMA}/api/tags', timeout=30).json()
    for m in tags.get('models', []):
        if m['name'] == MODEL:
            return m['digest']
    sys.exit(f'{MODEL} is not available in Ollama. Run: ollama pull {MODEL}')


def valid(labels):
    """Validity of the labels, as defined in the codebook; the evidence field does not affect it."""
    return (isinstance(labels, dict) and labels.get('rationale') in RATIONALES
            and labels.get('kink_framing') in FRAMINGS and labels.get('temporary') in YES_NO)


def ask(unit):
    user = (f"Assets: {unit['assets']}\nKink change: {unit['kink_change']}\n"
            f"Effective date (UTC): {unit['effective_date_utc']}\n\nText:\n\"\"\"\n{unit['text']}\n\"\"\"\n\n{CODEBOOK}")
    request = {'model': MODEL, 'stream': False, 'format': 'json', 'options': OPTIONS,
               'messages': [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': user}]}
    r = requests.post(f'{OLLAMA}/api/chat', json=request, timeout=600)
    r.raise_for_status()
    return request, r.json()


def main():
    for path in (RAW_OUT, LABELS_OUT):
        if os.path.exists(path):
            sys.exit(f'{path} exists. Outputs are not overwritten; if a run was interrupted, rename the partial '
                     'file, document it, and rerun all units.')
    label_commit = require_researcher_labels()
    digest = model_digest()
    ollama_version = requests.get(f'{OLLAMA}/api/version', timeout=30).json().get('version')
    with open(UNITS, encoding='utf-8') as f:
        units = [json.loads(line) for line in f]
    labels = []
    raw_file = open(RAW_OUT, 'w', encoding='utf-8')
    for unit in units:
        for attempt in (1, 2):
            request, response = ask(unit)
            content = response.get('message', {}).get('content', '')
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError:
                parsed = None
            raw_file.write(json.dumps({'action': unit['action'], 'attempt': attempt, 'request': request,
                                       'response': response, 'model_digest': digest,
                                       'ollama_version': ollama_version, 'researcher_label_commit': label_commit,
                                       'run_utc': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')},
                                      ensure_ascii=False) + '\n')
            raw_file.flush()
            if valid(parsed):
                break
        if not valid(parsed):
            parsed = {'rationale': 'INVALID', 'kink_framing': 'INVALID', 'temporary': 'INVALID', 'evidence': ''}
        evidence = str(parsed.get('evidence', ''))
        labels.append({'action': unit['action'], 'rationale': parsed['rationale'],
                       'kink_framing': parsed['kink_framing'], 'temporary': parsed['temporary'],
                       'evidence': evidence[:300], 'evidence_verbatim': bool(evidence) and evidence in unit['text'],
                       'attempts': attempt})
        print(f"{unit['action']}: {parsed['rationale']:18} framing={parsed['kink_framing']:14} "
              f"temporary={parsed['temporary']:3} (attempts {attempt})")
    raw_file.close()
    with open(LABELS_OUT, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(labels[0]))
        w.writeheader()
        w.writerows(labels)
    print(f'Model {MODEL} digest {digest}, Ollama {ollama_version}. Saved {RAW_OUT} and {LABELS_OUT}')


if __name__ == '__main__':
    main()
