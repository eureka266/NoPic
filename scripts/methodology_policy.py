"""Shared file boundary for methodology auditing and release packaging."""
import json
from pathlib import Path

MEDIA = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.mp4', '.mov', '.ttf', '.otf',
         '.woff', '.woff2', '.svg', '.zip', '.pdf', '.mp3', '.wav', '.pem', '.key', '.p12', '.pfx'}
PRIVATE = {'.nopic', 'workspace', 'inbox', 'exports', 'node_modules', '.venv', '.venv-docs',
           '__pycache__', 'session-handoffs', 'background-studies', 'credentials.json', 'secrets.json', 'secrets.toml', 'auth.json', 'tokens.json'}
EXCEPTIONS = {'.gitignore', '.env.example', 'inbox/materials/README.md'}


def violation(relative, root=None):
    relative = Path(relative)
    name = relative.as_posix()
    if root is not None:
        base = Path(root).resolve()
        target = base / relative
        if any(parent.is_symlink() for parent in (target, *target.parents) if parent.is_relative_to(base)):
            return 'symbolic link in methodology resources'
    if name in EXCEPTIONS:
        return None
    if relative.parts[0] in {'assets', 'organization-assets'}:
        return 'organization resource library'
    if any(part in PRIVATE or (part.startswith('.') and part != '.github') for part in relative.parts):
        return 'private configuration, intake or runtime'
    if relative.suffix.lower() in MEDIA:
        return 'production media or sensitive material'
    if relative.suffix.lower() == '.json':
        is_protocol = False
        is_schema = False
        is_eval = False
        is_empty_pack_example = False
        path = Path(root) / relative if root is not None else None
        if path is not None and path.is_file():
            try:
                data = json.loads(path.read_text(encoding='utf-8'))
            except (ValueError, UnicodeError):
                return 'invalid JSON'
            if isinstance(data, dict):
                is_protocol = bool(data) and set(data).issubset({'schema_version', 'description', 'title'}) and all(
                    isinstance(value, str) if key != 'schema_version' else type(value) is int
                    for key, value in data.items())
                schema_keys = {'$schema', '$id', '$defs', '$ref', 'definitions', 'title', 'description', 'type',
                               'properties', 'required', 'additionalProperties', 'items', 'enum', 'const', 'allOf',
                               'anyOf', 'oneOf', 'not', 'minimum', 'maximum', 'minItems', 'maxItems', 'minLength',
                               'maxLength', 'pattern', 'format', 'default'}
                is_schema = isinstance(data.get('$schema'), str) and data['$schema'].startswith('https://json-schema.org/') and set(data).issubset(schema_keys)
                if set(data).issubset({'schema_version', 'skill_version', 'cases'}) and isinstance(data.get('cases'), list):
                    is_eval = all(isinstance(case, dict) and set(case).issubset({'id', 'request', 'artifacts', 'checks'})
                                  and isinstance(case.get('id'), str) and isinstance(case.get('request'), str)
                                  and isinstance(case.get('checks'), list) and all(isinstance(item, str) for item in case['checks'])
                                  and isinstance(case.get('artifacts'), list) and all(isinstance(item, str) and not Path(item).is_absolute()
                                  and not set(Path(item).parts).intersection(PRIVATE) for item in case['artifacts'])
                                  for case in data['cases'])
                pack_keys = {'schema_version', 'id', 'version', 'display_name', 'defaults', 'logos', 'backgrounds',
                             'templates', 'references', 'fonts', 'examples', 'catalogs', 'files'}
                is_empty_pack_example = name == 'schemas/organization-pack.example.json' and set(data) == pack_keys and data.get('id') == 'your-organization' and data.get('defaults') == {'logo': None, 'partner_logo': None, 'background': None} and all(data.get(key) == [] for key in ('logos', 'backgrounds', 'templates', 'references', 'fonts', 'examples', 'files')) and data.get('catalogs') == {}
                if 'canvas' in data and 'layers' in data:
                    return 'production template'
                if any(key in data for key in ('pack_root', 'current_project', 'pack_identity', 'source_archive')):
                    return 'user project or activation state'
                if any(data.get(key) for key in ('templates', 'presets', 'portrait_presets', 'assets', 'logos', 'backgrounds', 'references', 'fonts', 'examples')):
                    return 'production catalog'
                if 'id' in data and 'version' in data and any(data.get(key) for key in ('logos', 'backgrounds', 'fonts', 'examples', 'catalogs')):
                    return 'organization pack manifest'
        allowed = is_protocol or (is_schema and relative.parts[0] == 'schemas') or (is_eval and 'evals' in relative.parts and relative.parts[0] == 'skills') or is_empty_pack_example
        if not allowed and name not in {'package.json', 'package-lock.json', 'tsconfig.json'}:
            return 'JSON outside methodology schemas and evaluation protocols'
    return None
