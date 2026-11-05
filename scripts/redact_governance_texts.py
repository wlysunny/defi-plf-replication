"""Remove forum text without a stated licence from the published governance data.

Usage, from the repository root (run once, on the files written by collect_governance_threads.py
and build_governance_units.py):
    python scripts/redact_governance_texts.py

Why: posts on the Aave governance forum carry no licence unless their author adds one. Of the
annotated posts, those ending in a CC0 waiver ("Copyright and related rights waived via CC0") are
kept in full; every other post is replaced by a placeholder giving its URL and the SHA-256 of its
exact original text. The annotation remains verifiable: scripts/restore_governance_texts.py
re-downloads the threads, checks each post against these hashes, and rebuilds the files byte for byte,
so that data/governance/manifest.json (hashes of the threads as first retrieved) applies again.

Writes, in place: data/governance/raw/<topic>.md, data/governance/units.jsonl,
data/governance/units_for_labelling.md; and data/governance/post_manifest.json (one record per post).
"""
import glob
import hashlib
import json
import re

from build_governance_units import POST_HEADER, SEPARATOR, RAW_DIR, MANIFEST

CC0 = re.compile(r'rights waived via \[?cc0', re.I)
UNITS = 'data/governance/units.jsonl'
UNITS_MD = 'data/governance/units_for_labelling.md'
POST_MANIFEST = 'data/governance/post_manifest.json'
RAW_OUTPUTS = 'annotation/llm_raw_outputs*.jsonl'     # model prompts embed the unit texts
RECORD = 'data/governance/redaction_record.json'     # SHA-256 of each model-output file before redaction


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def placeholder(url, digest):
    return (f'\n\n[Text not redistributed: the post states no licence. Source: {url}. '
            f'SHA-256 of the original text: {digest}. Restore with scripts/restore_governance_texts.py.]\n')


def json_variants(text):
    """The forms a string can take inside a JSON file: raw, and escaped with and without ASCII escapes."""
    return [text, json.dumps(text, ensure_ascii=False)[1:-1], json.dumps(text)[1:-1]]


def unit_replacements(units):
    """(original, placeholder) pairs, in every JSON form, for the units that are not redistributed."""
    pairs = []
    for u in units:
        if not u['redistributed']:
            new = placeholder(u['source'], u['text_sha256']).strip()
            pairs += list(zip(json_variants(u['original_text']), json_variants(new)))
    return pairs


def posts(text):
    """(number, user, time, start, end) of each post body, where text[start:end] is the exact body."""
    headers = list(POST_HEADER.finditer(text))
    out = []
    for i, h in enumerate(headers):
        stop = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        cut = text.find(SEPARATOR, h.end(), stop)
        out.append((int(h['n']), h['user'], h['time'], h.end(), cut if cut >= 0 else stop))
    return out


def main():
    manifest = json.load(open(MANIFEST))
    records, licensed = [], {}
    for topic, meta in manifest.items():
        path = f'{RAW_DIR}/{topic}.md'
        text = open(path, encoding='utf-8').read()
        if sha(text) != meta['sha256']:
            raise SystemExit(f'{path} does not match {MANIFEST}; it may already be redacted.')
        pieces, last = [], 0
        for n, user, time, start, end in posts(text):
            body = text[start:end]
            url = f'https://governance.aave.com/t/{topic}/{n}'
            ok = bool(CC0.search(body))
            licensed[url] = ok
            records.append({'topic': topic, 'post': n, 'author': user, 'posted_utc': time, 'url': url,
                            'cc0': ok, 'redistributed': ok, 'sha256': sha(body)})
            pieces.append(text[last:start])
            pieces.append(body if ok else placeholder(url, sha(body)))
            last = end
        pieces.append(text[last:])
        with open(path, 'w', encoding='utf-8') as f:
            f.write(''.join(pieces))
    units = [json.loads(line) for line in open(UNITS, encoding='utf-8')]
    for u in units:
        ok = licensed[u['source']]
        u['text_sha256'], u['redistributed'], u['original_text'] = sha(u['text']), ok, u['text']
    pairs = unit_replacements(units)
    record = {}
    for path in sorted(glob.glob(RAW_OUTPUTS)):
        raw = open(path, encoding='utf-8').read()
        record[path] = sha(raw)
        new = raw
        for a, b in pairs:
            new = new.replace(a, b)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new)
        print(f'{path}: {sum(raw.count(a) for a, _ in pairs)} unit texts replaced')
    for u in units:
        if not u['redistributed']:
            u['text'] = placeholder(u['source'], u['text_sha256']).strip()
        del u['original_text']
    with open(UNITS, 'w', encoding='utf-8') as f:
        for u in units:
            f.write(json.dumps(u, ensure_ascii=False) + '\n')
    with open(UNITS_MD, 'w', encoding='utf-8') as f:     # same layout as build_governance_units.py
        f.write('# Annotation units: governance rationales for kink changes\n\n'
                'Label each unit with the codebook in analysis_plans/governance_rationale_codebook.md.\n\n')
        for u in units:
            f.write(f"---\n\n## {u['action']} | {u['assets']} | kink {u['kink_change']} | effective {u['effective_date_utc']}\n\n"
                    f"Source: {u['source']} ({u['author']}, {u['posted_utc']} UTC){' — excerpt' if u['excerpt'] else ''}\n\n"
                    f"{u['text']}\n\n")
    with open(POST_MANIFEST, 'w') as f:
        json.dump(records, f, indent=1)
    with open(RECORD, 'w') as f:
        json.dump({'raw_outputs_sha256_before_redaction': record}, f, indent=1)
    kept = sum(r['cc0'] for r in records)
    print(f'Posts: {len(records)}, kept (CC0) {kept}, replaced {len(records) - kept}.')
    print(f"Units: {len(units)}, kept {sum(u['redistributed'] for u in units)}, replaced "
          f"{[u['action'] for u in units if not u['redistributed']]}.")


if __name__ == '__main__':
    main()
