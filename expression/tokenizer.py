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

import re
import token
import tokenize


class ExpressionTokenizer:
    """Custom tokenizer for the expression language, compatible with pegen's Parser."""

    TOKEN_PATTERNS = [
        ('WHITESPACE', r'[ \t]+'),
        ('HEX', r'0x[0-9A-Fa-f]+'),
        ('BIN', r'0b[01]+'),
        ('FLOAT', r'(?:[0-9]+\.[0-9]*|\.[0-9]+)(?:e[+-]?[0-9]+)?|[0-9]+e[+-]?[0-9]+'),
        ('INT', r'[0-9]+'),
        ('DSTRING', r'"[^"\\]*(?:\\[\S\s][^"\\]*)*"'),
        ('SSTRING', r"'[^'\\]*(?:\\[\S\s][^'\\]*)*'"),
        ('REGEX', r'/(?:[^/\\]|\\.)+/[imsxUXJ]*'),
        ('STRICT_EQ', r'==='),
        ('STRICT_NE', r'!=='),
        ('EQ', r'=='),
        ('MATCH', r'=~'),
        ('NE', r'!='),
        ('NOT', r'!'),
        ('ASSIGN', r'='),
        ('AND', r'&&'),
        ('OR', r'\|\|'),
        ('POWER', r'\*\*'),
        ('SPACESHIP', r'<=>'),
        ('LSHIFT', r'<<'),
        ('RSHIFT', r'>>'),
        ('GE', r'>='),
        ('LE', r'<='),
        ('GT', r'>'),
        ('LT', r'<'),
        ('PLUS', r'\+'),
        ('MINUS', r'-'),
        ('TIMES', r'\*'),
        ('DIV', r'/'),
        ('MOD', r'%'),
        ('AMP', r'&'),
        ('PIPE', r'\|'),
        ('QUESTION', r'\?'),
        ('CARET', r'\^'),
        ('LPAREN', r'\('),
        ('RPAREN', r'\)'),
        ('LBRACKET', r'\['),
        ('RBRACKET', r'\]'),
        ('LBRACE', r'\{'),
        ('RBRACE', r'\}'),
        ('COMMA', r','),
        ('COLON', r':'),
        ('SEMICOLON', r';'),
        ('DOLLAR_NAME', r'\$[0-9A-Za-z_]+'),
        ('NAME', r'[A-Za-z_][A-Za-z_0-9]*'),
    ]

    _compiled = re.compile('|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_PATTERNS))

    OP_TOKENS = {
        'STRICT_EQ', 'STRICT_NE', 'EQ', 'MATCH', 'NE', 'NOT', 'ASSIGN',
        'AND', 'OR', 'POWER', 'SPACESHIP', 'LSHIFT', 'RSHIFT', 'GE', 'LE', 'GT', 'LT',
        'PLUS', 'MINUS', 'TIMES', 'DIV', 'MOD', 'AMP', 'PIPE', 'QUESTION', 'CARET',
        'LPAREN', 'RPAREN', 'LBRACKET', 'RBRACKET', 'LBRACE', 'RBRACE',
        'COMMA', 'COLON', 'SEMICOLON',
    }

    def __init__(self, text):
        self._text = text
        self._tokens = []
        self._index = 0
        self._tokenize(text)

    REGEX_TOKEN_TYPE = 100

    def _can_be_regex(self):
        if not self._tokens:
            return True
        last = self._tokens[-1]
        if last.type == token.NUMBER:
            return False
        if last.type == token.NAME:
            return False
        if last.type == token.STRING:
            return False
        if last.string in (')', ']'):
            return False
        return True

    def _tokenize(self, text):
        pos = 0
        line = text
        while pos < len(text):
            m = self._compiled.match(text, pos)
            if m is None:
                raise SyntaxError(f"Unexpected character: {text[pos]!r} at position {pos}")
            kind = m.lastgroup
            value = m.group()
            start = (1, pos)
            end = (1, pos + len(value))
            pos = m.end()
            if kind == 'WHITESPACE':
                continue
            if kind == 'REGEX':
                if self._can_be_regex():
                    tok = tokenize.TokenInfo(self.REGEX_TOKEN_TYPE, value, start, end, line)
                else:
                    div_end = (1, start[1] + 1)
                    tok = tokenize.TokenInfo(token.OP, '/', start, div_end, line)
                    self._tokens.append(tok)
                    pos = start[1] + 1
                    continue
            elif kind in ('HEX', 'BIN', 'FLOAT', 'INT'):
                tok = tokenize.TokenInfo(token.NUMBER, value, start, end, line)
            elif kind in ('DSTRING', 'SSTRING'):
                tok = tokenize.TokenInfo(token.STRING, value, start, end, line)
            elif kind in ('NAME', 'DOLLAR_NAME'):
                tok = tokenize.TokenInfo(token.NAME, value, start, end, line)
            elif kind in self.OP_TOKENS:
                tok = tokenize.TokenInfo(token.OP, value, start, end, line)
            else:
                tok = tokenize.TokenInfo(token.OP, value, start, end, line)
            self._tokens.append(tok)
        self._tokens.append(
            tokenize.TokenInfo(token.ENDMARKER, '', (1, pos), (1, pos), line)
        )

    def peek(self):
        if self._index < len(self._tokens):
            return self._tokens[self._index]
        return self._tokens[-1]

    def getnext(self):
        tok = self.peek()
        if self._index < len(self._tokens):
            self._index += 1
        return tok

    def mark(self):
        return self._index

    def reset(self, index):
        self._index = index

    def diagnose(self):
        if not self._tokens:
            return tokenize.TokenInfo(token.ENDMARKER, '', (1, 0), (1, 0), '')
        return self._tokens[min(self._index, len(self._tokens) - 1)]

    def get_last_non_whitespace_token(self):
        for i in range(self._index - 1, -1, -1):
            tok = self._tokens[i]
            if tok.type not in (token.ENDMARKER, token.NEWLINE, token.INDENT, token.DEDENT):
                return tok
        return self._tokens[0] if self._tokens else None
