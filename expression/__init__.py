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

import math

from expression.parser import ExpressionParser as _GeneratedParser
from expression.tokenizer import ExpressionTokenizer
from expression.helpers import (
    with_type, is_typed, is_string_type,
    validate_number, validate_types, maybe_regex,
)


class ExpressionParserExt(_GeneratedParser):
    KEYWORDS = ('true', 'false', 'null')
    SOFT_KEYWORDS = ()

    def __init__(self, tokenizer, variables, constants, functions, source_text):
        super().__init__(tokenizer, verbose=False)
        self.variables = variables
        self.constants = constants
        self.functions = functions
        self._source_text = source_text

    def regex_literal(self):
        tok = self._tokenizer.peek()
        if tok.type == ExpressionTokenizer.REGEX_TOKEN_TYPE:
            return self._tokenizer.getnext()
        return None

    def function_assignment(self):
        mark = self._mark()
        name_tok = self.name()
        if name_tok is None:
            self._reset(mark)
            return None
        if not self.expect('('):
            self._reset(mark)
            return None
        params = []
        rparen = self.expect(')')
        if not rparen:
            p = self.name()
            if p is None:
                self._reset(mark)
                return None
            params.append(p.string)
            while self.expect(','):
                p = self.name()
                if p is None:
                    self._reset(mark)
                    return None
                params.append(p.string)
            rparen = self.expect(')')
            if not rparen:
                self._reset(mark)
                return None
        eq = self.expect('=')
        if not eq:
            self._reset(mark)
            return None
        next_tok = self._tokenizer.peek()
        if next_tok.string in ('=', '~'):
            self._reset(mark)
            return None
        body_start = next_tok.start[1]
        body = self._source_text[body_start:].rstrip(';').strip()
        while self._tokenizer.peek().string != '' and self._tokenizer.peek().type != 0:
            self._tokenizer.getnext()
        return self._func_assign(name_tok.string, params, body)

    def _func_assign(self, name, params, body=None):
        if body is None:
            body_start = self._tokenizer.peek().start[1]
            body = self._source_text[body_start:].rstrip(';').strip()

        captured_params = list(params)
        captured_body = body

        def func(*args):
            expr = Expression()
            for i, p in enumerate(captured_params):
                expr.variables[p] = args[i]
            return expr.evaluate(captured_body)

        self.functions[name] = func
        return with_type(True)

    def _var_assign(self, name, value):
        if name in self.constants:
            raise Exception(f"Can't assign value to constant '{name}'")
        self.variables[name] = value
        return value

    def _resolve_var(self, name):
        if name in ('true', 'false', 'null'):
            return None
        if name in self.constants:
            return with_type(self.constants[name])
        if name in self.variables:
            return with_type(self.variables[name])
        raise Exception(f"Variable '{name}' not found")

    def _parse_string(self, tok):
        raw = tok.string
        if raw.startswith('"'):
            value = raw[1:-1].replace('\\"', '"').replace('\\\\', '\\')
        else:
            value = raw[1:-1].replace("\\'", "'").replace('\\\\', '\\')
        return maybe_regex(value)

    def _parse_number(self, tok):
        s = tok.string
        if s.startswith('0x') or s.startswith('0X'):
            return with_type(int(s, 16))
        if s.startswith('0b') or s.startswith('0B'):
            return with_type(int(s, 2))
        if '.' in s or 'e' in s.lower():
            return with_type(float(s))
        return with_type(int(s))

    def _compare_op(self, op, a, b, fn):
        validate_types(['integer', 'double', 'boolean'], op, a)
        validate_types(['integer', 'double', 'boolean'], op, b)
        return with_type(fn(a['value'], b['value']))

    def _shift_op(self, op, a, b, fn):
        validate_number(op, a)
        validate_number(op, b)
        return with_type(fn(int(a['value']), int(b['value'])))

    def _plus(self, a, b):
        if is_string_type(b):
            return with_type(str(a['value']) + b['value'])
        validate_number('+', b)
        validate_number('+', a)
        return with_type(a['value'] + b['value'])

    def _minus(self, a, b):
        validate_number('-', b)
        validate_number('-', a)
        return with_type(a['value'] - b['value'])

    def _mul(self, a, b):
        validate_number('*', a)
        validate_number('*', b)
        return with_type(a['value'] * b['value'])

    def _div(self, a, b):
        validate_number('/', a)
        validate_number('/', b)
        if b['value'] == 0:
            raise ZeroDivisionError("Division by zero")
        return with_type(a['value'] / b['value'])

    def _mod(self, a, b):
        validate_number('%', a)
        validate_number('%', b)
        return with_type(a['value'] % b['value'])

    def _property_access(self, obj, prop):
        validate_types(['array'], '[', obj)
        validate_types(['string', 'double', 'integer', 'boolean'], '[', prop)
        return with_type(obj['value'][prop['value']])

    def _implicit_mul(self, a, b):
        validate_number('[*]', a)
        validate_number('[*]', b)
        return with_type(a['value'] * b['value'])

    def _unary_minus(self, a):
        validate_number('-', a)
        return with_type(a['value'] * -1)

    def _unary_plus(self, a):
        if is_string_type(a):
            return with_type(float(a['value']))
        return a

    def _call_function(self, name, args):
        BUILTIN_MAP = {
            'arcsin': 'asin', 'arcsinh': 'asinh',
            'arccos': 'acos', 'arccosh': 'acosh',
            'arctan': 'atan', 'arctanh': 'atanh',
            'ln': 'log',
        }
        BUILTIN_FUNCTIONS = [
            'sin', 'sinh', 'asin', 'asinh',
            'cos', 'cosh', 'acos', 'acosh',
            'tan', 'tanh', 'atan', 'atanh',
            'sqrt', 'abs', 'ln', 'log',
        ]
        resolved = BUILTIN_MAP.get(name, name)
        is_builtin = resolved in BUILTIN_FUNCTIONS
        is_custom = name in self.functions
        if not is_builtin and not is_custom:
            raise Exception(f"function '{name}' doesn't exist")
        arg_values = [a['value'] for a in args]
        if is_builtin:
            if resolved == 'abs':
                func = abs
            else:
                func = getattr(math, resolved)
            result = func(*arg_values)
        else:
            result = self.functions[name](*arg_values)
        return with_type(result)

    def _build_json_obj(self, key_tok, value, rest):
        key = self._json_string_val(key_tok)
        d = {key: value}
        d.update(rest)
        return d

    def _make_obj(self, key_tok, value):
        key = self._json_string_val(key_tok)
        return {key: value}

    def _json_string_val(self, tok):
        raw = tok.string
        if raw.startswith('"'):
            return raw[1:-1].replace('\\"', '"').replace('\\\\', '\\')
        return raw[1:-1].replace("\\'", "'").replace('\\\\', '\\')

    def _json_number_val(self, tok):
        s = tok.string
        if '.' in s or 'e' in s.lower():
            return float(s)
        return int(s)

    def _merge_obj(self, key_tok, value, rest):
        key = self._json_string_val(key_tok)
        d = {key: value}
        d.update(rest)
        return d


class Expression:
    def __init__(self):
        self.constants = {"e": math.e, "pi": math.pi}
        self.variables = {}
        self.functions = {}
        self.suppress_errors = False
        self.last_error = ""

    def evaluate(self, expr):
        if not expr or not expr.strip():
            return None
        text = expr.strip()
        tokenizer = ExpressionTokenizer(text)
        parser = ExpressionParserExt(
            tokenizer, self.variables, self.constants, self.functions, text
        )
        try:
            result = parser.start()
            if result is None:
                raise Exception(f"invalid syntax: {expr}")
            self.variables = parser.variables
            self.functions = parser.functions
            if is_typed(result):
                return result['value']
            return result
        except ZeroDivisionError:
            raise
        except Exception as e:
            self.last_error = str(e) + f" in expression: {expr}"
            if not self.suppress_errors:
                raise
            return None
