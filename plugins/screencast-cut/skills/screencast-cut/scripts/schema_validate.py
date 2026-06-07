#!/usr/bin/env python3
"""Tiny JSON-Schema validator shared by the screencast-cut scripts.

Two jobs:
  - Validate each script's OUTPUT manifest against its schema before writing,
    so a contract regression fails loudly at the source instead of surfacing
    as a confusing `KeyError` three steps downstream in Remotion.
  - Validate the human-authored manual `events.json` on READ, so a typo in a
    hand-written file produces a precise "clicks[0].t_s: missing" message
    instead of a `KeyError`.

Zero new dependencies: if `jsonschema` happens to be installed we defer to it
(full draft support); otherwise a lightweight validator covers the subset of
JSON Schema these contracts actually use: `type` (incl. nullable via type
lists), `properties`, `required`, `items`, `enum`, `additionalProperties`
(bool), `minimum`/`maximum`, `minItems`. Unknown keywords are ignored — the
fallback is intentionally permissive about what it doesn't understand, strict
about what it does.
"""

import json
from pathlib import Path

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"


class SchemaError(Exception):
    """Raised on a validation failure, with a JSON-path-ish location."""


def load_schema(name):
    """Load a schema by bare name (e.g. 'timing') from the schemas/ dir."""
    path = SCHEMAS_DIR / f"{name}.schema.json"
    if not path.is_file():
        raise SchemaError(f"schema not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


_TYPE_CHECKS = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    # bool is a subclass of int in Python — exclude it from number/integer.
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "null": lambda v: v is None,
}


def _check_type(value, types, loc, errors):
    if isinstance(types, str):
        types = [types]
    if any(_TYPE_CHECKS.get(t, lambda v: True)(value) for t in types):
        return True
    errors.append(f"{loc or '<root>'}: expected type {types}, got {type(value).__name__}")
    return False


def _validate(value, schema, loc, errors):
    if not isinstance(schema, dict):
        return

    if "type" in schema:
        if not _check_type(value, schema["type"], loc, errors):
            return  # type wrong → downstream checks are noise

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{loc or '<root>'}: {value!r} not in enum {schema['enum']}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{loc}: {value} < minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{loc}: {value} > maximum {schema['maximum']}")

    if isinstance(value, dict):
        props = schema.get("properties", {})
        for req in schema.get("required", []):
            if req not in value:
                errors.append(f"{loc + '.' if loc else ''}{req}: required field missing")
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in props:
                    errors.append(f"{loc + '.' if loc else ''}{key}: unexpected field")
        for key, subschema in props.items():
            if key in value:
                child_loc = f"{loc + '.' if loc else ''}{key}"
                _validate(value[key], subschema, child_loc, errors)

    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{loc or '<root>'}: {len(value)} items < minItems {schema['minItems']}")
        items = schema.get("items")
        if isinstance(items, dict):
            for i, item in enumerate(value):
                _validate(item, items, f"{loc}[{i}]", errors)


def validate(instance, schema_name, *, what="data"):
    """Validate `instance` against the named schema.

    Raises SchemaError with a precise location on the first batch of failures.
    Uses `jsonschema` if importable, else the lightweight validator above.
    """
    schema = load_schema(schema_name)
    try:
        import jsonschema  # type: ignore

        try:
            jsonschema.validate(instance, schema)
        except jsonschema.ValidationError as e:  # pragma: no cover - dep-gated
            path = "".join(f"[{p!r}]" if isinstance(p, int) else f".{p}" for p in e.path)
            raise SchemaError(f"{what} failed schema '{schema_name}'{path}: {e.message}")
        return
    except ImportError:
        pass

    errors = []
    _validate(instance, schema, "", errors)
    if errors:
        joined = "\n  - ".join(errors)
        raise SchemaError(f"{what} failed schema '{schema_name}':\n  - {joined}")
