#!/usr/bin/env python3
"""Install and activate a NoPic brand pack for the current project."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tempfile
import zipfile


MAX_FILE_BYTES = 50 * 1024 * 1024
MAX_PACK_BYTES = 500 * 1024 * 1024
SAFE_ID = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-')


def project_root(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            cwd=Path.cwd(), capture_output=True, text=True, check=True,
        )
        return Path(result.stdout.strip()).resolve()
    except (OSError, subprocess.CalledProcessError):
        return Path.cwd().resolve()


def safe_value(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or any(char not in SAFE_ID for char in value):
        raise ValueError(f'Invalid brand pack {field}')
    return value


def safe_member(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or not path.parts:
        raise ValueError(f'Unsafe archive path: {name}')
    return path


def is_symlink(info: zipfile.ZipInfo) -> bool:
    mode = (info.external_attr >> 16) & 0xFFFF
    return (mode & 0o170000) == 0o120000


def validate_manifest(root: Path) -> dict:
    manifest_file = root / 'manifest.json'
    if not manifest_file.is_file():
        raise ValueError('Brand pack must contain manifest.json at its root')
    manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
    if not isinstance(manifest, dict) or manifest.get('schema_version') != 1:
        raise ValueError('Unsupported brand pack schema_version; expected 1')
    pack_id = safe_value(manifest.get('id'), 'id')
    version = safe_value(manifest.get('version'), 'version')
    manifest['id'] = pack_id
    manifest['version'] = version
    if not isinstance(manifest.get('display_name', pack_id), str):
        raise ValueError('Brand pack display_name must be a string')

    files = []
    for section in ('logos', 'backgrounds', 'references', 'fonts', 'examples'):
        entries = manifest.get(section, [])
        if not isinstance(entries, list):
            raise ValueError(f'Brand pack {section} must be a list')
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError(f'Brand pack {section} contains an invalid entry')
            asset_paths = [entry.get('file')]
            if entry.get('render_file'):
                asset_paths.append(entry['render_file'])
            for asset_path in asset_paths:
                relative = safe_member(str(asset_path or ''))
                file = root.joinpath(*relative.parts).resolve()
                if not file.is_relative_to(root.resolve()) or not file.is_file():
                    raise ValueError(f'Brand pack file is missing: {relative}')
                files.append(str(relative))
            if 'id' in entry:
                safe_value(entry['id'], f'{section} id')

    defaults = manifest.get('defaults', {})
    if not isinstance(defaults, dict):
        raise ValueError('Brand pack defaults must be an object')
    ids = {section: {entry.get('id') for entry in manifest.get(section, [])}
           for section in ('logos', 'backgrounds')}
    for key, section in (('logo', 'logos'), ('partner_logo', 'logos'), ('background', 'backgrounds')):
        value = defaults.get(key)
        if value is not None and value not in ids[section]:
            raise ValueError(f'Brand pack default {key} does not reference a declared asset')
    manifest['_validated_files'] = sorted(set(files))
    return manifest


def extract_zip(source: Path, destination: Path) -> Path:
    total = 0
    with zipfile.ZipFile(source) as archive:
        infos = archive.infolist()
        for info in infos:
            relative = safe_member(info.filename)
            if is_symlink(info):
                raise ValueError(f'Symbolic links are not allowed in brand packs: {relative}')
            total += info.file_size
            if info.file_size > MAX_FILE_BYTES or total > MAX_PACK_BYTES:
                raise ValueError('Brand pack exceeds the supported size limit')
            target = destination.joinpath(*relative.parts).resolve()
            if not target.is_relative_to(destination.resolve()):
                raise ValueError(f'Unsafe archive path: {relative}')
            if not info.is_dir():
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as source_file, target.open('wb') as target_file:
                    shutil.copyfileobj(source_file, target_file)
    direct = destination / 'manifest.json'
    if direct.is_file():
        return destination
    candidates = [path.parent for path in destination.glob('*/manifest.json')]
    if len(candidates) == 1:
        return candidates[0]
    raise ValueError('Brand pack must contain one root manifest.json')


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def install(source: Path, target_project: Path) -> dict:
    if not source.is_file() or source.suffix.lower() != '.zip':
        raise ValueError('Provide a .zip brand pack')
    with tempfile.TemporaryDirectory(prefix='nopic-brand-pack-') as temporary:
        extracted = extract_zip(source, Path(temporary))
        manifest = validate_manifest(extracted)
        pack_id, version = manifest['id'], manifest['version']
        packs_root = target_project / '.nopic/brand-packs' / pack_id
        destination = packs_root / version
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            existing = validate_manifest(destination)
            if existing.get('_validated_files') != manifest.get('_validated_files'):
                raise ValueError(f'Brand pack already exists with different contents: {destination}')
            reused = True
        else:
            temporary_destination = packs_root / ('.' + version + '.tmp')
            if temporary_destination.exists():
                shutil.rmtree(temporary_destination)
            shutil.copytree(extracted, temporary_destination)
            validate_manifest(temporary_destination)
            temporary_destination.replace(destination)
            reused = False

        manifest_path = destination / 'manifest.json'
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        active = {
            'schema_version': 1,
            'pack_id': pack_id,
            'version': version,
            'display_name': manifest['display_name'],
            'pack_root': str(destination),
            'manifest': str(manifest_path),
            'source_archive': str(source.resolve()),
            'source_sha256': digest,
        }
        active_path = target_project / '.nopic/active-brand-pack.json'
        write_json(active_path, active)
        return {
            'pack_id': pack_id,
            'version': version,
            'display_name': manifest['display_name'],
            'pack_root': str(destination),
            'manifest': str(manifest_path),
            'active_config': str(active_path),
            'source_sha256': digest,
            'reused': reused,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--project-root')
    args = parser.parse_args()
    receipt = install(args.archive.expanduser().resolve(), project_root(args.project_root))
    print(json.dumps(receipt, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError, zipfile.BadZipFile) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False))
        raise SystemExit(1)
