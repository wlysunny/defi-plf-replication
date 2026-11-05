"""Remove unlicensed forum text from the Git history (run once, before the repository is made public).

redact_governance_texts.py removes the text from the current files; this script removes it from the
files as they were committed earlier, so that no commit in the published history contains it.
Commit dates and messages are kept; the hashes of the commits that touched these files, and of all
later commits, change. git filter-repo writes the old-to-new map to .git/filter-repo/commit-map.

Usage, in a fresh clone, from the repository root:
  1. python scripts/rewrite_governance_history.py prepare PAIRS   (before redacting: records each
     unlicensed text and its placeholder in PAIRS, a file kept OUTSIDE the repository)
  2. python scripts/redact_governance_texts.py, then commit the result
  3. python scripts/rewrite_governance_history.py rewrite PAIRS FIRST BRANCH...   (rewrites, with
     git filter-repo, only the commits from FIRST, the first commit containing the texts, to the tip of
     each BRANCH; earlier commits, including the original authors', keep their hashes and signatures)
  4. python scripts/rewrite_governance_history.py verify PAIRS    (searches every commit on local branches and tags, i.e. what will be pushed)
Requires git-filter-repo (pip install git-filter-repo).
"""
import json
import subprocess
import sys

from redact_governance_texts import (MANIFEST, RAW_DIR, UNITS, json_variants, placeholder, posts, sha,
                                     CC0)

PATHS = ('data/governance/', 'annotation/llm_raw_outputs')


def prepare(out):
    manifest = json.load(open(MANIFEST))
    pairs, licensed = [], {}
    for topic, meta in manifest.items():
        text = open(f'{RAW_DIR}/{topic}.md', encoding='utf-8').read()
        if sha(text) != meta['sha256']:
            raise SystemExit(f'{RAW_DIR}/{topic}.md is not the original; run prepare before redacting.')
        for n, _, _, start, end in posts(text):
            body, url = text[start:end], f'https://governance.aave.com/t/{topic}/{n}'
            licensed[url] = bool(CC0.search(body))
            if not licensed[url]:
                # anchored on the post's header line ("user | time | #n"), which is unique, so that
                # a short body cannot match text elsewhere
                head = text[text.rfind('\n', 0, start) + 1:start]
                pairs.append((head + body, head + placeholder(url, sha(body))))
    for line in open(UNITS, encoding='utf-8'):
        u = json.loads(line)
        if not licensed[u['source']]:
            new = placeholder(u['source'], sha(u['text'])).strip()
            pairs += list(zip(json_variants(u['text']), json_variants(new)))
    pairs.sort(key=lambda p: -len(p[0]))          # whole posts before the excerpts they contain
    json.dump(pairs, open(out, 'w'), ensure_ascii=False)
    print(f'{len(pairs)} replacements written to {out} (keep this file outside the repository)')


CALLBACK = '''
if "pairs" not in value.data:
    import json
    value.data["pairs"] = [(a.encode("utf-8"), b.encode("utf-8")) for a, b in json.load(open(%r, encoding="utf-8"))]
if filename.decode("utf-8", "replace").startswith(%r):
    old = value.get_contents_by_identifier(blob_id)
    new = old
    for a, b in value.data["pairs"]:
        new = new.replace(a, b)
    if new != old:
        blob_id = value.insert_file_with_contents(new)
return (filename, mode, blob_id)
'''


def rewrite(pairs_path, first, branches):
    import os
    body = CALLBACK % (os.path.abspath(pairs_path), PATHS)
    refs = [f'{first}^..{b}' for b in branches]
    subprocess.run(['git', 'filter-repo', '--force', '--refs', *refs, '--file-info-callback', body], check=True)


def verify(pairs_path):
    pairs = json.load(open(pairs_path, encoding='utf-8'))
    # one long line from each original text (git grep matches line by line)
    probes = sorted({max(a.split('\n'), key=len).strip() for a, _ in pairs if '\n' in a or len(a) > 60})
    probes = [p for p in probes if len(p) >= 60]
    commits = subprocess.run(['git', 'rev-list', '--branches', '--tags'], capture_output=True, text=True, check=True).stdout.split()
    found = 0
    for probe in probes:
        r = subprocess.run(['git', 'grep', '-l', '-F', probe, *commits], capture_output=True, text=True)
        if r.stdout.strip():
            found += 1
            print('STILL PRESENT:', probe[:60], '->', r.stdout.split()[0])
    print(f'Checked {len(probes)} passages in {len(commits)} commits: '
          + ('none found.' if not found else f'{found} still present.'))
    return found == 0


if __name__ == '__main__':
    cmd, path = sys.argv[1], sys.argv[2]
    if cmd == 'prepare':
        prepare(path)
    elif cmd == 'rewrite':
        rewrite(path, sys.argv[3], sys.argv[4:])
    elif cmd == 'verify':
        sys.exit(0 if verify(path) else 1)
