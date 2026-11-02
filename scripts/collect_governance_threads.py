"""Download the Aave governance forum threads that contain the rationale for each change of the
optimal usage ratio (kink) on Aave V3 Ethereum Core, 2023-2025 (route 2 annotation).

Usage, from the repository root:
    python scripts/collect_governance_threads.py

For each thread it saves the raw Markdown of all posts, as served by the forum's public
endpoint https://governance.aave.com/raw/<topic_id>, to data/governance/raw/<topic_id>.md, and
writes data/governance/manifest.json with the URL, retrieval time (UTC) and SHA-256 of each file.
No account or key is used. Forum content belongs to its authors; it is stored here for the
purpose of annotation, with its source recorded.
"""
import hashlib
import json
import os
import time
from datetime import datetime, timezone

import requests

THREADS = {
    12921: 'Gauntlet interest rate curve recommendations (2023-04-27)',
    14410: 'sDAI Aave V3 onboarding (DAI and WETH optimal ratio)',
    15096: 'Increase optimal borrow rates for Ethereum stablecoin markets',
    15110: 'Upgrade Aave V3 ETH pool wETH parameters',
    16168: 'Update stETH and WETH risk params',
    16864: 'Stablecoin IR curve amendment on Aave V2 and V3',
    22279: 'Chaos Labs Risk Stewards - adjust USDT interest rate curve (2025 thread)',
    22625: 'Risk Stewards interest rate update - WETH and wstETH Ethereum (2025)',
}
OUT_DIR = 'data/governance/raw'
HEADERS = {'User-Agent': 'academic-replication-study (COMP8240, Macquarie University)'}


def fetch_raw(topic_id):
    """All pages of the raw thread. The endpoint returns up to 100 posts per page."""
    pages = []
    for page in range(1, 20):
        r = requests.get(f'https://governance.aave.com/raw/{topic_id}', params={'page': page},
                         headers=HEADERS, timeout=60)
        r.raise_for_status()
        text = r.text.strip()
        if not text or (pages and text == pages[-1]):
            break
        pages.append(text)
        if text.count('\n-------------------------\n') < 99:
            break
        time.sleep(1)
    return '\n\n'.join(pages) + '\n'


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    manifest = {}
    for topic_id, label in THREADS.items():
        text = fetch_raw(topic_id)
        path = f'{OUT_DIR}/{topic_id}.md'
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
        manifest[str(topic_id)] = {
            'label': label,
            'url': f'https://governance.aave.com/t/{topic_id}',
            'raw_endpoint': f'https://governance.aave.com/raw/{topic_id}',
            'retrieved_utc': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
            'n_chars': len(text),
        }
        print(f'{topic_id}: {len(text):>7} characters  {label}')
        time.sleep(1)
    with open('data/governance/manifest.json', 'w') as f:
        json.dump(manifest, f, indent=2)
    print('Saved', OUT_DIR, 'and data/governance/manifest.json')


if __name__ == '__main__':
    main()
