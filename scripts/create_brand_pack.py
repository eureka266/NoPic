#!/usr/bin/env python3
"""Create a portable NoPic brand pack ZIP from a curated source directory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from install_brand_pack import validate_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='Directory containing manifest.json and declared assets')
    parser.add_argument('output', type=Path, help='Destination .zip file')
    args = parser.parse_args()
    source = args.source.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if not source.is_dir():
        raise ValueError(f'Brand pack source directory not found: {source}')
    manifest = validate_manifest(source)
    files = {'manifest.json', *manifest['_validated_files']}
    readme = source / 'README.md'
    if readme.is_file():
        files.add('README.md')
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for relative in sorted(files):
            archive.write(source / relative, relative)
    print(json.dumps({
        'archive': str(output),
        'pack_id': manifest['id'],
        'version': manifest['version'],
        'file_count': len(files),
    }, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError, zipfile.BadZipFile) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False))
        raise SystemExit(1)
