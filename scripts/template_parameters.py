"""Named template snapshots and per-project layer geometry. No image rendering here."""
import copy
import json
import re
from organization_assets import read_catalog
from project_assets import catalog_asset

SLUG = re.compile(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z')
EDITABLE_FIELDS = {
    'text': {'x', 'y', 'width', 'height', 'font_size_max', 'font_size_min', 'align'},
    'image': {'x', 'y', 'width', 'height', 'horizontal_align', 'vertical_align'},
    'glyph': {'x', 'y', 'font_size'},
    'line': {'x', 'y', 'width', 'line_width'},
}


def load_template(layout, config=None, start=None):
    index = read_catalog('templates', config, start)
    selected_id = (config or {}).get('template_id')
    for entry in index['templates']:
        if (entry.get('legacy_layout') == layout and
                (selected_id is None or entry.get('id') == selected_id)):
            path = catalog_asset(entry['file'], 'templates', config, start)
            return json.loads(path.read_text(encoding='utf-8'))
    raise ValueError('Organization pack has no matching template: ' + str(selected_id or layout))


def _normalize_logo_layer(template, overrides):
    """Migrate older snapshot IDs by their declared image role."""
    layers = template['layers']
    candidates = [key for key, layer in layers.items() if isinstance(layer, dict)
                  and layer.get('type') == 'image' and layer.get('asset_field') == 'logo']
    if 'brand-logo' in layers or len(candidates) != 1:
        return {}
    old_id = candidates[0]
    layers['brand-logo'] = layers.pop(old_id)
    for group in template.get('logo_variants', {}).values():
        if old_id in group:
            group['brand-logo'] = group.pop(old_id)
    if old_id in overrides:
        if not isinstance(overrides[old_id], dict) or not isinstance(overrides.get('brand-logo', {}), dict):
            raise ValueError('Logo layer override must be an object')
        overrides['brand-logo'] = {**overrides.pop(old_id), **overrides.get('brand-logo', {})}
    return {old_id: 'brand-logo'}


def _integer(value, label, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(label + ' must be an integer >= ' + str(minimum))
    return value


def _validate_layer(layer_id, layer, canvas):
    label = layer.get('display_name', layer_id) + ' (' + layer_id + ')'
    kind = layer.get('type')
    if kind not in EDITABLE_FIELDS:
        raise ValueError(label + ': unsupported layer type')
    for key in ('x', 'y'):
        _integer(layer.get(key), label + '.' + key)
    for key in EDITABLE_FIELDS[kind] - {'x', 'y', 'align', 'horizontal_align', 'vertical_align'}:
        _integer(layer.get(key), label + '.' + key, 1)
    if layer['x'] >= canvas['width'] or layer['y'] >= canvas['height']:
        raise ValueError(label + ': position is outside the canvas')
    if kind in ('text', 'image', 'line') and layer['x'] + layer['width'] > canvas['width']:
        raise ValueError(label + ': width extends outside the canvas')
    if kind in ('text', 'image') and layer['y'] + layer['height'] > canvas['height']:
        raise ValueError(label + ': height extends outside the canvas')
    if kind == 'text':
        if layer['font_size_min'] > layer['font_size_max']:
            raise ValueError(label + ': font_size_min exceeds font_size_max')
        if layer['font_size_max'] > canvas['height']:
            raise ValueError(label + ': font_size_max exceeds the canvas height')
        if layer.get('align') not in ('left', 'center', 'right'):
            raise ValueError(label + ': align must be left, center or right')
    if kind == 'glyph' and layer['font_size'] > canvas['height']:
        raise ValueError(label + ': font_size exceeds the canvas height')
    if kind == 'image':
        if layer.get('horizontal_align') not in ('left', 'center', 'right'):
            raise ValueError(label + ': invalid horizontal_align')
        if layer.get('vertical_align') not in ('top', 'center', 'bottom'):
            raise ValueError(label + ': invalid vertical_align')


def _expand_sections(config, template):
    """Bind repeated layers to persistent section IDs, independent of list indices."""
    pattern = template.get('section_pattern')
    if not pattern:
        return
    sections = config.get('sections', [])
    if not isinstance(sections, list) or not pattern['min_count'] <= len(sections) <= pattern['max_count']:
        raise ValueError('Summary section count is outside the template range')
    existing = {section.get('id') for section in sections if isinstance(section, dict) and section.get('id')}
    reserved = existing | {layer.get('section_id') for layer in template['layers'].values() if layer.get('section_id')}
    used = set()
    for section in sections:
        if not isinstance(section, dict):
            raise ValueError('Each summary section must be an object')
        section_id = section.get('id')
        if section_id is None:
            number = 1
            while 'takeaway-' + str(number).zfill(2) in reserved:
                number += 1
            section_id = 'takeaway-' + str(number).zfill(2)
            section['id'] = section_id
            reserved.add(section_id)
        if not isinstance(section_id, str) or not SLUG.fullmatch(section_id) or section_id in used:
            raise ValueError('Each summary section needs a unique meaningful id, e.g. takeaway-01')
        used.add(section_id)
    old_generated = {key for key, layer in template['layers'].items() if layer.get('section_id')}
    template['layers'] = {key: layer for key, layer in template['layers'].items() if key not in old_generated}
    row_height = pattern['total_height'] // len(sections)
    generated = {}
    for index, section in enumerate(sections):
        for suffix, original in pattern['layers'].items():
            layer_id = section['id'] + '-' + suffix
            if layer_id in template['layers'] or layer_id in generated:
                raise ValueError('Summary layer id collision: ' + layer_id)
            layer = copy.deepcopy(original)
            layer['display_name'] = layer['display_name'].format(number=index + 1)
            layer['section_id'] = section['id']
            layer['y'] = pattern['top'] + index * row_height + layer.pop('y_offset')
            if 'height_inset' in layer:
                layer['height'] = row_height - layer.pop('height_inset')
            generated[layer_id] = layer
    template['layers'].update(generated)
    # A deleted takeaway's overrides must never attach to a newly added takeaway.
    overrides = config.get('layer_overrides')
    if isinstance(overrides, dict):
        for deleted in old_generated - generated.keys():
            overrides.pop(deleted, None)


def resolve_template(config, layout, size, assignments=(), reset_layers=(), start=None):
    """Use the project's snapshot, then apply explicit overrides without changing defaults."""
    template = copy.deepcopy(config['template']) if 'template' in config else load_template(layout, config, start)
    if not isinstance(template, dict) or template.get('schema_version') != 1:
        raise ValueError('Unsupported template snapshot schema')
    if template.get('legacy_layout') != layout:
        raise ValueError('Template snapshot belongs to another layout; choose a matching template')
    if not isinstance(template.get('id'), str) or not SLUG.fullmatch(template['id']):
        raise ValueError('Template id must be a meaningful lowercase name')
    if config.get('template_id', template['id']) != template['id']:
        raise ValueError('template_id does not match the saved template snapshot')
    if not isinstance(template.get('display_name'), str) or not template['display_name'].strip():
        raise ValueError('Template needs a readable display_name')
    _integer(template.get('version'), 'template.version', 1)
    canvas = template.get('canvas', {})
    if not isinstance(canvas, dict) or (canvas.get('width'), canvas.get('height')) != tuple(size) or canvas.get('unit') != 'px':
        raise ValueError('Template canvas must match this layout and use pixel coordinates')
    if not isinstance(template.get('layers'), dict):
        raise ValueError('Template layers must be an object keyed by meaningful IDs')
    overrides = copy.deepcopy(config.get('layer_overrides', {}))
    if not isinstance(overrides, dict):
        raise ValueError('layer_overrides must be an object')
    aliases = _normalize_logo_layer(template, overrides)
    config['layer_overrides'] = overrides
    _expand_sections(config, template)
    variants = template.get('logo_variants')
    if variants:
        variant = 'paired' if config.get('logo') and config.get('partner_logo') else 'single'
        for layer_id, fields in variants[variant].items():
            template['layers'][layer_id].update(fields)
    for layer_id in reset_layers:
        layer_id = aliases.get(layer_id, layer_id)
        if layer_id not in template['layers']:
            raise ValueError('Unknown layer to reset: ' + layer_id)
        overrides.pop(layer_id, None)
    for assignment in assignments:
        if '=' not in assignment or '.' not in assignment.split('=', 1)[0]:
            raise ValueError('--layer expects LAYER_ID.PROPERTY=VALUE')
        target, raw_value = assignment.split('=', 1)
        layer_id, key = target.rsplit('.', 1)
        layer_id = aliases.get(layer_id, layer_id)
        if layer_id not in template['layers']:
            raise ValueError('Unknown layer: ' + layer_id)
        try:
            value = json.loads(raw_value)
        except json.JSONDecodeError:
            value = raw_value
        overrides.setdefault(layer_id, {})[key] = value
    resolved = copy.deepcopy(template['layers'])
    for layer_id, layer in template['layers'].items():
        if not isinstance(layer_id, str) or not SLUG.fullmatch(layer_id):
            raise ValueError('Layer id must be a meaningful lowercase name')
        if not isinstance(layer, dict):
            raise ValueError('Each template layer must be an object')
        _validate_layer(layer_id, layer, canvas)
    for layer_id, fields in overrides.items():
        if layer_id not in resolved:
            raise ValueError('Unknown layer override: ' + str(layer_id))
        if not isinstance(fields, dict):
            raise ValueError('Layer override must be an object: ' + layer_id)
        unsupported = fields.keys() - EDITABLE_FIELDS[resolved[layer_id]['type']]
        if unsupported:
            raise ValueError('Unsupported layer property: ' + layer_id + '.' + sorted(unsupported)[0])
        resolved[layer_id].update(fields)
        _validate_layer(layer_id, resolved[layer_id], canvas)
    config['template'] = template
    config['template_id'] = template['id']
    return resolved


def text_box(layer):
    return tuple(layer[key] for key in ('x', 'y', 'width', 'height', 'font_size_max', 'font_size_min'))


def image_box(layer):
    return tuple(layer[key] for key in ('x', 'y', 'width', 'height'))


def content_value(config, layer):
    field = layer['content_field']
    if isinstance(field, list):
        return '\n'.join(config.get(key, '') for key in field if config.get(key))
    return config.get(field, '')
