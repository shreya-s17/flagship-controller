"""Build an explicit, deterministic multipart evidence archive for private use.

Only listed regular files under results/ are admitted. No recursive workspace
collection, credentials, benchmark inputs or implicit overwrite is permitted.
"""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def package(root, bundle, paths, scope):
    root = Path(root).resolve()
    if not bundle or Path(bundle).name != bundle or bundle in ('.', '..'):
        raise ValueError('Invalid bundle name')
    destination = root/'artifacts'/bundle
    if destination.exists():
        raise ValueError('Refuse existing bundle')
    if not paths or len(set(paths)) != len(paths):
        raise ValueError('Empty or duplicate path list')
    files = {}
    for name in sorted(paths):
        if not isinstance(name, str):
            raise ValueError('String results path required')
        relative = PurePosixPath(name)
        if not relative.parts or relative.is_absolute() or '..' in relative.parts or relative.parts[0] != 'results' or str(relative) != name:
            raise ValueError('Only explicit normalized results paths admitted')
        path = root/name
        if any(part.is_symlink() for part in (path, *path.parents) if part != root and part.is_relative_to(root)):
            raise ValueError('Symlink evidence refused')
        if not path.is_file() or not path.resolve().is_relative_to(root/'results'):
            raise ValueError('Regular results file required')
        files[name] = path.read_bytes()
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode='w', format=tarfile.USTAR_FORMAT) as archive:
        for name, data in files.items():
            entry = tarfile.TarInfo(name)
            entry.size = len(data)
            entry.mode = 0o644
            entry.mtime = 0
            archive.addfile(entry, io.BytesIO(data))
    compressed = io.BytesIO()
    with gzip.GzipFile(fileobj=compressed, mode='wb', filename='', mtime=0) as output:
        output.write(raw.getvalue())
    data = compressed.getvalue()
    manifest = {'scope': scope, 'archive_sha256': digest(data), 'parts': [],
                'files': {name: digest(content) for name, content in files.items()},
                'generator': 'scripts/package_live_evidence.py',
                'generator_sha256': digest(Path(__file__).read_bytes()),
                'format': 'sorted USTAR regular files, fixed metadata, gzip timestamp0, 32768-byte parts; no scientific validation'}
    destination.mkdir(parents=True, exist_ok=False)
    for index, start in enumerate(range(0, len(data), 32768)):
        part = data[start:start+32768]
        name = f'evidence.tar.gz.part{index:03d}'
        (destination/name).write_bytes(part)
        manifest['parts'].append({'file': name, 'bytes': len(part), 'sha256': digest(part)})
    (destination/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--bundle', required=True)
    parser.add_argument('--paths-from', type=Path, required=True, help='JSON array of explicit relative paths')
    parser.add_argument('--scope', required=True)
    args = parser.parse_args()
    result = package(args.root, args.bundle, json.loads(args.paths_from.read_text()), args.scope)
    print(json.dumps({'files': len(result['files']), 'parts': len(result['parts']),
                      'archive_sha256': result['archive_sha256']}, indent=2))
