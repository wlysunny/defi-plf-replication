"""Build the annotation units for the governance-rationale labelling (route 2).

Usage, from the repository root:
    python scripts/build_governance_units.py

Each unit is one change of the optimal usage ratio (kink) on Aave V3 Ethereum Core, as detected
in data/aave_v3/aave_v3_rate_params_daily.csv, paired with the forum post that first specifies the
new kink value that was implemented. The whole post is used, except where it has separate headed
sections devoted to other assets, markets or parameters: those sections are removed, and the post's
summary or opening and the section on this kink are kept (segments listed below).
Image links and the Disclaimer and Copyright boilerplate are removed.

The raw threads are checked against data/governance/manifest.json (SHA-256) before use.
Writes data/governance/units.jsonl (for the model) and data/governance/units_for_labelling.md
(for the researcher), and an empty label sheet annotation/researcher_labels.csv if none exists.
"""
import csv
import hashlib
import json
import os
import re
import sys

RAW_DIR = 'data/governance/raw'
MANIFEST = 'data/governance/manifest.json'
END = None

# action, effective date (UTC, day before the first daily sample showing the change), assets,
# kink before -> after, topic, post number, segments [(start marker, end marker)] or None for the whole post
UNITS = [
    ('A01', '2023-05-22', 'USDT', '90% -> 80%', 12921, 1,
     [('# Simple Summary', '# Methodology'), ('## Objectives', '### Building Reserves'), ('### USDT', '### EURS')]),
    ('A02', '2023-08-28', 'DAI, WETH', '80% -> 90%', 14410, 1, None),
    ('A03', '2023-11-16', 'WETH', '90% -> 80%', 15110, 1, None),
    ('A04', '2023-11-27', 'USDT', '80% -> 90%', 15096, 2,
     [('Gauntlet supports the recommendations', '### On raising slope 1'), ('### On raising Uopt', '### On raising RF')]),
    ('A05', '2024-01-31', 'WETH', '80% -> 90%', 16168, 1,
     [('# **Summary**', '## Specification'), ('********WETH Ethereum********', '********WETH Arbitrum********')]),
    ('A06', '2024-04-10', 'DAI, USDC, USDT', '90% -> 92%', 16864, 2, [('# Increase Uoptimal to 92%', END)]),
    ('A07', '2025-06-09', 'USDT', '92% -> 95%', 22279, 2, None),
    ('A08', '2025-06-14', 'USDT', '95% -> 92%', 22279, 3, None),
    ('A09', '2025-08-13', 'USDT', '92% -> 94%', 22279, 16, None),
    ('A10', '2025-08-28', 'USDT', '94% -> 92%', 22279, 17, None),
    ('A11', '2025-07-16', 'WETH', '90% -> 93%', 22279, 6, None),
    ('A12', '2025-07-19', 'WETH', '93% -> 94%', 22279, 10,
     [('# **Summary**', '## Ethereum Prime'), ('## Recommendation', END)]),
    ('A13', '2025-07-22', 'WETH', '94% -> 95%', 22279, 12,
     [('# **Summary**', '# **Motivation**'), ('## WETH — Ethereum Core', '## WETH — Ethereum Prime')]),
    ('A14', '2025-07-30', 'WETH', '95% -> 94%', 22279, 13, None),
    ('A15', '2025-08-08', 'WETH', '94% -> 93%', 22279, 14, None),
    ('A16', '2025-08-11', 'WETH', '93% -> 92%', 22279, 15, None),
]

POST_HEADER = re.compile(r'^(?P<user>\S.*?) \| (?P<time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) UTC \| #(?P<n>\d+)$', re.M)
SEPARATOR = '\n-------------------------\n'


def load_thread(topic, manifest):
    with open(f'{RAW_DIR}/{topic}.md', encoding='utf-8') as f:
        text = f.read()
    if hashlib.sha256(text.encode('utf-8')).hexdigest() != manifest[str(topic)]['sha256']:
        sys.exit(f'{RAW_DIR}/{topic}.md does not match the SHA-256 in {MANIFEST}.')
    return text


def get_post(text, number):
    headers = list(POST_HEADER.finditer(text))
    for i, h in enumerate(headers):
        if int(h['n']) == number:
            end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
            body = text[h.end():end].split(SEPARATOR)[0]
            return h['user'], h['time'], body.strip()
    sys.exit(f'Post #{number} not found.')


def segment(body, start, end):
    i = body.find(start)
    if i < 0:
        sys.exit(f'Segment start not found: {start!r}')
    j = len(body) if end is None else body.find(end, i + len(start))
    if j < 0:
        sys.exit(f'Segment end not found: {end!r}')
    return body[i:j].strip()


def clean(text):
    text = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', text)
    text = re.split(r'\n#*\s*\**Disclaimer\**:?\**\s*\n', text, maxsplit=1)[0]
    text = re.split(r'\n#*\s*\**Copyright\**:?\**\s*\n', text, maxsplit=1)[0]
    return re.sub(r'\n{3,}', '\n\n', text).strip()


def main():
    with open(MANIFEST) as f:
        manifest = json.load(f)
    threads = {}
    units = []
    for action, date, assets, change, topic, post, segments in UNITS:
        if topic not in threads:
            threads[topic] = load_thread(topic, manifest)
        user, time, body = get_post(threads[topic], post)
        text = body if segments is None else '\n\n[...]\n\n'.join(segment(body, s, e) for s, e in segments)
        units.append({'action': action, 'effective_date_utc': date, 'assets': assets, 'kink_change': change,
                      'source': f'https://governance.aave.com/t/{topic}/{post}', 'author': user,
                      'posted_utc': time, 'excerpt': segments is not None, 'text': clean(text)})
    with open('data/governance/units.jsonl', 'w', encoding='utf-8') as f:
        for u in units:
            f.write(json.dumps(u, ensure_ascii=False) + '\n')
    with open('data/governance/units_for_labelling.md', 'w', encoding='utf-8') as f:
        f.write('# Annotation units: governance rationales for kink changes\n\n'
                'Label each unit with the codebook in analysis_plans/governance_rationale_codebook.md.\n\n')
        for u in units:
            f.write(f"---\n\n## {u['action']} | {u['assets']} | kink {u['kink_change']} | effective {u['effective_date_utc']}\n\n"
                    f"Source: {u['source']} ({u['author']}, {u['posted_utc']} UTC){' — excerpt' if u['excerpt'] else ''}\n\n"
                    f"{u['text']}\n\n")
    os.makedirs('annotation', exist_ok=True)
    sheet = 'annotation/researcher_labels.csv'
    if not os.path.exists(sheet):
        with open(sheet, 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['action', 'rationale', 'kink_framing', 'temporary', 'note'])
            for u in units:
                w.writerow([u['action'], '', '', '', ''])
    for u in units:
        print(f"{u['action']} {u['assets']:16} {u['kink_change']:11} {u['source']:45} {len(u['text']):>6} chars")
    print('Saved data/governance/units.jsonl, data/governance/units_for_labelling.md')


if __name__ == '__main__':
    main()
