"""Restore large trace files from a versioned, hash-checked multipart bundle.

Existing files are never overwritten. Extraction accepts only manifest paths,
regular files under results/, and original content hashes; no tar.extract use.
"""
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def restore(root, bundle='live-evidence-2026-10-16'):
    root=Path(root).resolve()
    if Path(bundle).name!=bundle:raise ValueError('Invalid bundle name')
    folder=root/'artifacts'/bundle
    manifest=json.loads((folder/'manifest.json').read_text())
    chunks=[]
    for part in manifest['parts']:
        name=part['file']
        if Path(name).name!=name:raise ValueError('Invalid part path')
        data=(folder/name).read_bytes()
        if len(data)!=part['bytes'] or digest(data)!=part['sha256']:raise ValueError('Part integrity failure')
        chunks.append(data)
    data=b''.join(chunks)
    if digest(data)!=manifest['archive_sha256']:raise ValueError('Archive integrity failure')
    files={}
    with tarfile.open(fileobj=io.BytesIO(gzip.decompress(data)),mode='r:') as archive:
        for item in archive:
            target=(root/item.name).resolve()
            if not item.isfile() or item.name not in manifest['files'] or not target.is_relative_to(root/'results') or item.name in files:
                raise ValueError('Invalid archive member')
            content=archive.extractfile(item).read()
            if digest(content)!=manifest['files'][item.name]:raise ValueError('File integrity failure')
            if target.exists() and target.read_bytes()!=content:raise ValueError('Refuse to overwrite changed file')
            files[item.name]=(target,content)
    if set(files)!=set(manifest['files']):raise ValueError('Archive members missing')
    for target,content in files.values():
        target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():
            with target.open('xb') as output:output.write(content)
    return len(files)


if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    total=restore(root)
    for bundle in ('baseline-evidence-2026-10-16','indexed-baseline-evidence-2026-10-16','common-state-evidence-2026-10-16','harder-common-evidence-2026-10-16','obligation-evidence-2026-10-17'):
        if (root/'artifacts'/bundle/'manifest.json').exists():
            total+=restore(root,bundle)
    print('Verified/restored',total,'original trace files')
