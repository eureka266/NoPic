"""Resolve organization-owned resources outside the methodology repository."""
import json
import os
from pathlib import Path


def pack_root(config=None, start=None, required=True):
    config = config or {}
    explicit = config.get('brand_pack') or os.environ.get('NOPIC_BRAND_PACK')
    if explicit:
        root = Path(explicit).expanduser().resolve()
    else:
        base = Path(start or Path.cwd()).expanduser().resolve()
        if base.is_file():
            base = base.parent
        root = None
        for parent in (base, *base.parents):
            active = parent / '.nopic/active-brand-pack.json'
            if active.is_file():
                value = json.loads(active.read_text(encoding='utf-8')).get('pack_root')
                if not value:
                    raise ValueError('Active organization pack has no pack_root')
                path = Path(value).expanduser()
                root = (path if path.is_absolute() else parent / path).resolve()
                break
    if root is None:
        if required:
            raise ValueError('No organization asset pack is active; install a pack or provide brand_pack / NOPIC_BRAND_PACK')
        return None
    if not (root / 'manifest.json').is_file():
        raise ValueError('Organization pack manifest is missing')
    return root


def asset_path(relative, config=None, start=None):
    root = pack_root(config, start)
    source = Path(relative)
    if source.is_absolute():
        raise ValueError('Organization resource must use a pack-relative path')
    path = (root / source).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError('Organization resource is missing or outside the pack: ' + str(relative))
    return path


def catalog_path(name, config=None, start=None):
    root = pack_root(config, start)
    manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
    catalogs = manifest.get('catalogs', {})
    relative = catalogs.get(name)
    if not isinstance(relative, str) or not relative:
        raise ValueError('Organization pack does not declare catalog: ' + name)
    return asset_path(relative, config={'brand_pack': str(root)})


def read_catalog(name, config=None, start=None):
    return json.loads(catalog_path(name, config, start).read_text(encoding='utf-8'))
