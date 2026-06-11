# Copyright (C) 2026 Jakub T. Jankiewicz <https://jcu.bi/>
#
# This file is part of expression.py.
#
# expression.py is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# expression.py is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with expression.py. If not, see <https://www.gnu.org/licenses/>.

import json
import re


class Typed(dict):
    pass


def with_type(value, typ=None):
    if isinstance(value, Typed) and set(value.keys()) == {'type', 'value'}:
        return value
    if typ is not None:
        t = typ
    elif isinstance(value, bool):
        t = 'boolean'
    elif isinstance(value, int):
        t = 'integer'
    elif isinstance(value, float):
        t = 'double'
    elif isinstance(value, str):
        t = 'string'
    elif isinstance(value, (list, dict)):
        t = 'array'
    elif value is None:
        t = 'NULL'
    else:
        t = type(value).__name__
    return Typed(type=t, value=value)


def is_typed(value):
    return isinstance(value, Typed) and set(value.keys()) == {'type', 'value'}


def is_type(typ, value):
    return is_typed(value) and value['type'] == typ


def is_number(value):
    return is_type('double', value) or is_type('integer', value)


def is_string_type(value):
    return is_type('string', value)


def is_array_type(value):
    return is_type('array', value)


def validate_types(types, operation, obj):
    if not is_typed(obj):
        raise Exception(f"Internal error: Invalid object {obj}")
    t = obj['type']
    if t not in types:
        if len(types) == 1:
            valid = types[0]
        else:
            valid = 'any of ' + ', '.join(types)
        raise Exception(
            f"Invalid operand to {operation} operation expecting {valid} got {t}"
        )


def validate_number(operation, obj):
    validate_types(['double', 'integer'], operation, obj)


def maybe_regex(value):
    if re.match(r'^(\W).*\1[imsxUXJ]*$', value, re.DOTALL):
        return with_type(value, 'regex')
    return with_type(value, 'string')


def loose_equal(a, b):
    if type(a) is type(b):
        return a == b
    try:
        if isinstance(a, str) and isinstance(b, (int, float)):
            return float(a) == b
        if isinstance(b, str) and isinstance(a, (int, float)):
            return a == float(b)
    except (ValueError, TypeError):
        pass
    return a == b


def do_check_equal(left, right, fn):
    a = right['value']
    b = left['value']
    if is_array_type(right) or is_array_type(left):
        return with_type(
            fn(
                json.dumps(a, separators=(',', ':')),
                json.dumps(b, separators=(',', ':')),
            )
        )
    return with_type(fn(a, b))


def do_match(left, right, variables):
    validate_types(['string'], '=~', left)
    validate_types(['regex', 'string'], '=~', right)
    regex_str = right['value']
    flags_str = ''
    if regex_str.startswith('/'):
        last_slash = regex_str.rfind('/')
        if last_slash > 0:
            flags_str = regex_str[last_slash + 1:]
            regex_str = regex_str[1:last_slash]
    flags = 0
    if 'i' in flags_str:
        flags |= re.IGNORECASE
    if 'm' in flags_str:
        flags |= re.MULTILINE
    if 's' in flags_str:
        flags |= re.DOTALL
    if 'x' in flags_str:
        flags |= re.VERBOSE
    try:
        match = re.search(regex_str, left['value'], flags)
    except re.error:
        raise Exception(f"Invalid regular expression: {right['value']}")
    old_keys = [k for k in variables if k.startswith('$')]
    for k in old_keys:
        del variables[k]
    if match:
        variables['$0'] = match.group(0)
        for i, g in enumerate(match.groups(), 1):
            if g is not None:
                variables[f'${i}'] = g
        return with_type(True)
    return with_type(False)


def do_power(base, exp):
    validate_number('**', base)
    validate_number('**', exp)
    result = base['value'] ** exp['value']
    if (
        isinstance(result, float)
        and result == int(result)
        and isinstance(base['value'], int)
    ):
        result = int(result)
    return with_type(result)
