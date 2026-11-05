"""Restore the governance texts removed by redact_governance_texts.py.

Usage, from the repository root:
    python scripts/restore_governance_texts.py

Re-downloads each thread from the forum's raw endpoint, takes the exact text of every post that was
not redistributed, checks it against the SHA-256 in data/governance/post_manifest.json, and puts it
back in place. If every post matches, each thread is again byte-identical to the file first retrieved
(checked against data/governance/manifest.json), and build_governance_units.py is run to rebuild the
annotation units, whose texts are checked against the hashes in units.jsonl. Posts edited or deleted
on the forum since retrieval are reported and the file is left unchanged.
"""
import glob
import hashlib
import json

import build_governance_units as build
from collect_governance_threads import fetch_raw

from redact_governance_texts import POST_MANIFEST, RAW_OUTPUTS, RECORD, UNITS, json_variants, placeholder, posts

POST_HEADER, SEPARATOR, RAW_DIR, MANIFEST = build.POST_HEADER, build.SEPARATOR, build.RAW_DIR, build.MANIFEST


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def main():
    manifest = json.load(open(MANIFEST))
    records = json.load(open(POST_MANIFEST))
    expected = {(r['topic'], r['post']): r for r in records if not r['redistributed']}
    redacted_units = [json.loads(l) for l in open(UNITS, encoding='utf-8')]
    hashes_before = {u['action']: u['text_sha256'] for u in redacted_units}
    failed = []
    for topic, meta in manifest.items():
        path = f'{RAW_DIR}/{topic}.md'
        stored = open(path, encoding='utf-8').read()
        missing = {n for (t, n) in expected if t == topic}
        if not missing:
            continue
        fresh = fetch_raw(topic)
        bodies = {n: fresh[s:e] for n, _, _, s, e in posts(fresh)}
        restored = stored
        for n in sorted(missing):
            r = expected[(topic, n)]
            body = bodies.get(n)
            if body is None or sha(body) != r['sha256']:
                failed.append(r['url'])
                continue
            restored = restored.replace(placeholder(r['url'], r['sha256']), body, 1)
        if sha(restored) == meta['sha256']:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(restored)
            print(f'{path}: restored, matches {MANIFEST}')
        else:
            print(f'{path}: not restored ({len(missing)} posts expected)')
    if failed:
        raise SystemExit('Changed or missing on the forum since retrieval: ' + ', '.join(failed))
    build.main()
    after = {json.loads(l)['action']: hashlib.sha256(json.loads(l)['text'].encode('utf-8')).hexdigest()
             for l in open(UNITS, encoding='utf-8')}
    bad = [a for a in hashes_before if hashes_before[a] != after.get(a)]
    print('Unit texts match the recorded hashes.' if not bad else f'Unit texts differ: {bad}')
    if bad:
        return
    texts = {json.loads(l)['action']: json.loads(l)['text'] for l in open(UNITS, encoding='utf-8')}
    record = json.load(open(RECORD))['raw_outputs_sha256_before_redaction']
    for path in sorted(glob.glob(RAW_OUTPUTS)):          # put the texts back into the model prompts
        raw = open(path, encoding='utf-8').read()
        # the placeholder has one form; the original text had one of three JSON forms, identified by
        # the file's recorded hash
        for form in (2, 1, 0):
            candidate = raw
            for u in redacted_units:
                if not u['redistributed']:
                    candidate = candidate.replace(u['text'], json_variants(texts[u['action']])[form])
            if sha(candidate) == record.get(path):
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(candidate)
                print(f'{path}: restored, matches {RECORD}')
                break
        else:
            print(f'{path}: not restored (no form matches the recorded hash)')


if __name__ == '__main__':
    main()
