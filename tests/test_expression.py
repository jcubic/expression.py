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

import sys
import pytest

from expression import Expression


def php_eval(expr_str):
    """Evaluate an expression the way PHP would, returning a Python equivalent."""
    result = eval(expr_str)
    return result


class TestExpression:
    def array_test(self, expressions):
        """Test a list of expressions by comparing with Python eval."""
        expr = Expression()
        for s in expressions:
            result = expr.evaluate(s)
            expected = php_eval(s)
            assert result == expected, f"Failed for expression: {s}"

    # ------------------------------------------------------------------
    def test_stash(self):
        expr = Expression()
        expr.evaluate("x = 10")
        assert expr.evaluate("x+2") == 12

    # ------------------------------------------------------------------
    def test_access_function(self):
        expr = Expression()
        expr.evaluate("f(x, y) = x + y")
        assert expr.functions["f"](10, 20) == 30

    # ------------------------------------------------------------------
    def test_numerics(self):
        specs = {
            "0xFF": 255,
            "0xF0F0": 61680,
            "0b001": 1,
            "0b11111111": 255,
            "0b101": 5,
        }
        expr = Expression()
        for s, value in specs.items():
            assert expr.evaluate(s) == value, f"Failed for: {s}"

    # ------------------------------------------------------------------
    def test_implicit_multiplication(self):
        specs = [
            ("f(x) = 2x", True),
            ("f(10)", 20),
            ("2(f(10))", 40),
            ("x = 2", 2),
            ("2x+f(10)", 24),
            ("2f(10)", 40),
        ]
        expr = Expression()
        for s, value in specs:
            assert expr.evaluate(s) == value, f"Failed for: {s}"
        assert expr.evaluate("-8(5/2)^2*(1-sqrt(4))-8") == 42

    # ------------------------------------------------------------------
    def test_integers(self):
        ints = ["100", "3124123", str(sys.maxsize), "-1000"]
        expr = Expression()
        for s in ints:
            result = expr.evaluate(s)
            assert result == int(s), f"Failed for: {s}"

    # ------------------------------------------------------------------
    def test_floats(self):
        floats = ["10.10", "0.01", ".1", "1.", "-100.100", "1.10e2", "-0.10e10"]
        expr = Expression()
        for s in floats:
            result = expr.evaluate(s)
            assert result == float(s), f"Failed for: {s}"

    # ------------------------------------------------------------------
    def test_arithmetic_operators(self):
        expressions = [
            ("-10", -10),
            ("20+20", 40),
            ("-20+20", 0),
            ("-0.1+0.1", 0.0),
            (".1+.1", 0.2),
            ("1.+1.", 2.0),
            ("0.1+(-0.1)", 0.0),
            ("20*20", 400),
            ("-20*20", -400),
            ("20*(-20)", -400),
            ("1.*1.", 1.0),
            (".1*.1", 0.010000000000000002),
            ("20-20", 0),
            ("-20-20", -40),
            ("20/20", 1.0),
            ("-20/20", -1.0),
            ("10%20", 10),
            ("10%9", 1),
            ("20%9", 2),
            ("100 >> 2", 25),
            ("100 << 2", 400),
        ]
        expr = Expression()
        for s, expected in expressions:
            result = expr.evaluate(s)
            assert result == expected, f"Failed for: {s}"

        expr2 = Expression()
        expr2.suppress_errors = True
        with pytest.raises(Exception):
            expr2.evaluate("10/0")

    # ------------------------------------------------------------------
    def test_power_operator(self):
        expressions = {
            "2 ** 2": 4,
            "2 ^ 2": 4,
            "2 ** 10": 1024,
        }
        expr = Expression()
        for s, value in expressions.items():
            assert expr.evaluate(s) == value, f"Failed for: {s}"

    # ------------------------------------------------------------------
    def test_semicolon(self):
        expr = Expression()
        result = expr.evaluate("10+10;")
        assert result == 20

    # ------------------------------------------------------------------
    def test_boolean_comparators(self):
        expressions = [
            ("10 == 10", True),
            ("10 == 20", False),
            ("0.1 == 0.1", True),
            ("0.1 == 0.2", False),
            ("10 != 10", False),
            ("20 != 10", True),
            ("0.1 != 0.1", False),
            ("0.1 != 0.2", True),
            ("10 < 10", False),
            ("20 < 10", False),
            ("10 < 20", True),
            ("0.1 < 0.2", True),
            ("0.2 < 0.1", False),
            ("0.1 < 0.1", False),
            ("10 > 10", False),
            ("20 > 10", True),
            ("10 > 20", False),
            ("0.1 > 0.2", False),
            ("0.2 > 0.1", True),
            ("0.1 > 0.1", False),
            ("10 <= 10", True),
            ("20 <= 10", False),
            ("10 <= 20", True),
            ("0.1 <= 0.2", True),
            ("0.2 <= 0.1", False),
            ("0.1 <= 0.1", True),
            ("10 >= 10", True),
            ("20 >= 10", True),
            ("10 >= 20", False),
            ("0.1 >= 0.2", False),
            ("0.2 >= 0.1", True),
            ("0.1 >= 0.1", True),
        ]
        expr = Expression()
        for s, expected in expressions:
            result = expr.evaluate(s)
            assert result == expected, f"Failed for: {s}"

    # ------------------------------------------------------------------
    def test_boolean_operators(self):
        # In the PHP version, comparisons return 1/0 (truthy integers).
        # We test that the boolean truthiness matches.
        expressions = [
            ("10 == 10 && 10 == 10", True),
            ("10 != 10 && 10 != 10", False),
            ("10 == 20 && 10 == 10", False),
            ("10 == 10 && 10 == 20", False),
            ("0.1 == 0.1 && 0.1 == 0.1", True),
            ("0.1 == 0.2 && 0.1 == 0.1", False),
            ("0.1 == 0.1 && 0.1 == 0.2", False),
            ("10 == 10 || 10 == 10", True),
            ("10 == 20 || 10 == 10", True),
            ("10 == 10 || 10 == 20", True),
            ("0.1 == 0.1 || 0.1 == 0.1", True),
            ("0.1 == 0.2 || 0.1 == 0.1", True),
            ("0.1 == 0.1 || 0.1 == 0.2", True),
        ]
        expr = Expression()
        for s, expected in expressions:
            result = expr.evaluate(s)
            assert bool(result) == expected, f"Failed for: {s}"

        # Type-aware comparisons
        expr2 = Expression()
        # '2' == 2 should be true (loose comparison like PHP)
        assert bool(expr2.evaluate("'2' == 2")) is True
        # '2' !== 2 should be true (strict not-equal: different types)
        assert bool(expr2.evaluate("'2' !== 2")) is True
        # 2 === 2 should be true (strict equal: same type and value)
        assert bool(expr2.evaluate("2 === 2")) is True

        # Short-circuit with string values
        string_expressions = {
            '("foo" == "foo") && "a" || "b"': "a",
            '("foo" == "bar") && "a" || "b"': "b",
        }
        expr3 = Expression()
        for s, expected in string_expressions.items():
            result = expr3.evaluate(s)
            assert result == expected, f"Failed for: {s}"

    # ------------------------------------------------------------------
    def test_priority_operands(self):
        data = {
            "2+2*2": 6,
            "2-2+2*2+2/2*-1+2": 5,
            "2+1 > 2+2": False,
            "2+1 < 2+2": True,
            "2+2*2-2/2 >= 2*2+-2/2*2": True,
        }
        expr = Expression()
        for formula, expected in data.items():
            assert expr.evaluate(formula) == expected, f"Failed for: {formula}"

    # ------------------------------------------------------------------
    def test_keywords(self):
        # Truthy expressions
        truthy_expressions = [
            "1 == true",
            "true == true",
            "false == false",
            "false != true",
            "null == null",
            "null != true",
        ]
        expr = Expression()
        for s in truthy_expressions:
            result = expr.evaluate(s)
            assert bool(result), f"Expected truthy for: {s}"

        # Assignment and retrieval of keyword values
        keyword_assignments = {
            "foo = true": True,
            "foo = false": False,
            "foo = null": None,
        }
        for s, value in keyword_assignments.items():
            expr2 = Expression()
            expr2.evaluate(s)
            result = expr2.evaluate("foo")
            assert result == value, f"Failed for: {s}"

    # ------------------------------------------------------------------
    def test_negation(self):
        expressions = [
            ("!(10 == 10)", False),
            ("!1", False),
            ("!0", True),
        ]
        expr = Expression()
        for s, expected in expressions:
            result = expr.evaluate(s)
            assert bool(result) == expected, f"Failed for: {s}"

    # ------------------------------------------------------------------
    def test_strings(self):
        # String comparisons
        string_comparisons = [
            ('"foo" == "foo"', True),
            ('"foo\\"bar" == "foo\\"bar"', True),
            ('"f\\"oo" != "f\\"oo"', False),
            ('"foo\\"" != "foo\\"bar"', True),
            ("'foo\"bar' == 'foo\"bar'", True),
            ("'foo' == 'foo'", True),
            ("'foo\\'foo' != 'foo'", True),
            ('"foo\\\\" == "foo\\\\"', True),
            ("'foo\\\\' == 'foo\\\\'", True),
        ]
        expr = Expression()
        for s, expected in string_comparisons:
            result = expr.evaluate(s)
            assert bool(result) == expected, f"Failed for: {s}"

        # String concatenation
        string_concat = {
            '"foo" + "bar"': "foobar",
            "'foo' + 'bar'": "foobar",
            '"foo\\"bar" + "baz"': 'foo"barbaz',
        }
        expr2 = Expression()
        for s, expected in string_concat.items():
            result = expr2.evaluate(s)
            assert result == expected, f"Failed for: {s}"

        # Regex match on string with escaped characters
        result = expr2.evaluate('"foo\\"ba\\\\\\\\\\"r" =~ /foo/')
        assert bool(result) is True

    # ------------------------------------------------------------------
    def test_matchers(self):
        expressions = {
            '"Foobar" =~ /([fo]+)/i': "Foo",
            '"foobar" =~ /([0-9]+)/': None,
            '"1020" =~ /([0-9]+)/': "1020",
            '"1020" =~ /([a-z]+)/': None,
        }
        for s, group in expressions.items():
            expr = Expression()
            result = expr.evaluate(s)
            if group is None:
                assert not bool(result), f"Expected falsy for: {s}"
            else:
                assert expr.evaluate("$1") == group, f"Failed $1 for: {s}"

    # ------------------------------------------------------------------
    def test_variable_assignment(self):
        expressions = {
            'foo = "bar"': ("foo", "bar"),
            "foo = 10": ("foo", 10),
            "foo = 0.1": ("foo", 0.1),
            "foo = 10 == 10": ("foo", 1),
            "foo = 10 != 10": ("foo", 0),
            'foo = "foo" =~ "/[fo]+/"': ("foo", 1),
            "foo = 10 + 10": ("foo", 20),
        }
        for s, (var, value) in expressions.items():
            expr = Expression()
            expr.evaluate(s)
            assert expr.evaluate(var) == value, f"Failed for: {s}"

    # ------------------------------------------------------------------
    def test_variables(self):
        expr = Expression()
        expr.variables = {
            "f_price": 500,
            "f_width": 500,
            "f_turndown_0_2_f_count": 2,
            "f_length_metal_f_length": 1400,
        }
        formula = "f_price*(f_width+f_turndown_0_2_f_count*10)*f_length_metal_f_length/1000000"
        assert expr.evaluate(formula) == 364

    # ------------------------------------------------------------------
    def test_json(self):
        import json

        # Round-trip JSON structures
        structures = [
            {"foo": "bar"},
            {'foo\\"bar': "baz"},
            {"foo}": "bar"},
            [10, 20, 30, 40],
            [10, "]", 30],
            [10, {"foo": "bar"}, 30],
        ]
        expr = Expression()
        for structure in structures:
            json_str = json.dumps(structure)
            result = expr.evaluate(json_str)
            assert json.dumps(result) == json_str, f"Failed for: {json_str}"

        # JSON comparisons
        json_comparisons = {
            '{"foo":"bar"} == {"foo":"bar"}': True,
            '{"foo2":"bar2"} == {"foo": "bar"}': False,
            '{"f}o2":"ba{r2"} != {"foo": "bar"}': True,
            "[10,20] != [20,30]": True,
        }
        for s, expected in json_comparisons.items():
            result = expr.evaluate(s)
            assert bool(result) == expected, f"Failed for: {s}"

        # JSON property/index access
        json_access = {
            '{"foo":"bar"}["foo"]': "bar",
            "[10,20][0]": 10,
        }
        for s, expected in json_access.items():
            result = expr.evaluate(s)
            assert result == expected, f"Failed for: {s}"

        # Variable holding JSON
        expr.evaluate('foo = {"foo": "bar"}')
        result = expr.evaluate('foo["foo"]')
        assert result == "bar"

    # ------------------------------------------------------------------
    def test_custom_functions(self):
        function_defs = {
            "square(x) = x*x": {
                "square(10)": 100,
                "square(-10)": 100,
                "square(10) == 100": 1,
            },
            "plus(x,y) = x+y": {
                "plus(-1, -1)": -2,
                "plus(10, 10)": 20,
                "plus(-10, -10)": -20,
            },
            'string() = "foo"': {
                'string() =~ "/[fo]+/"': 1,
                'string() == "foo"': 1,
                'string() != "bar"': 1,
            },
            'number(x) = x =~ "/^[0-9]+$/"': {
                'number("10")': 1,
                'number("10foo")': 0,
            },
            'logic(x, y) = x == "foo" || x == "bar"': {
                'logic( "foo", 1 )': 1,
                'logic("bar", 1)': 1,
                'logic("lorem", 1)': 0,
            },
        }
        for func_def, tests in function_defs.items():
            expr = Expression()
            expr.evaluate(func_def)
            for fn, value in tests.items():
                assert expr.evaluate(fn) == value, f"Failed for: {fn}"

    # ------------------------------------------------------------------
    def test_custom_closures(self):
        expr = Expression()
        expr.functions["even"] = lambda a: a % 2 == 0
        values = {10: True, 20: True, 1: False, 3: False, 4: True}
        for number, expected in values.items():
            result = expr.evaluate(f"even({number})")
            assert bool(result) == expected, f"Failed for: even({number})"

    # ------------------------------------------------------------------
    def test_formula_with_brackets(self):
        expr = Expression()
        expr.suppress_errors = True
        expr.functions = {
            "p1": lambda p1, p2, p3, p4, p5: p1,
            "p2": lambda p1, p2, p3, p4, p5: p2,
            "p3": lambda p1, p2, p3, p4, p5: p3,
            "p4": lambda p1, p2, p3, p4, p5: p4,
            "p5": lambda p1, p2, p3, p4, p5: p5,
        }
        data = {
            "p1(1, 2, 3, 4, 5)": 1,
            "p2(1, 2, 3, 4, 5)": 2,
            "p3(1, 2, 3, 4, 5)": 3,
            "p4(1, 2, 3, 4, 5)": 4,
            "p5(1, 2, 3, 4, 5)": 5,
        }
        for formula, expected in data.items():
            assert expr.evaluate(formula) == expected, f"Failed for: {formula}"

    # ------------------------------------------------------------------
    def test_function_order_parameters(self):
        expr = Expression()
        expr.suppress_errors = True
        expr.functions = {
            "min": lambda v1, v2: min(v1, v2),
            "max": lambda v1, v2: max(v1, v2),
        }
        data = {
            "max(2,(2+2)*2)": 8,
            "max((2),(0))": 2,
            "max((2+2)*2,(3+2)*2)": 10,
            "max((4+2)*2,(3+2)*2)": 12,
            "min(max((2+2)*2,(3+2)*2), 1)": 1,
            "min(1, max(2,3))": 1,
            "min(1, max((4+2)*2,(3+2)*2))": 1,
            "min(max((2+2)*2,(3+2)*2), max((4+2)*2,(3+2)*2))": 10,
            "max( min((2+2)*2,(3+2)*2), min((4+2)*2,(3+2)*2) )": 10,
            "1 + max( min(2-(2+2)*2,(3+2)*2), min((4+2)*2,(3+2)*2) ) - 2": 9,
            "max(1,max(2,max(3,4)))": 4,
            "max( min(1 + 2, 4), 5)": 5,
            "min(2,(2+2)*2)": 2,
        }
        for formula, expected in data.items():
            assert expr.evaluate(formula) == expected, f"Failed for: {formula}"

    # ------------------------------------------------------------------
    def test_empty_formula(self):
        expr = Expression()
        expr.suppress_errors = True
        assert expr.evaluate("") is None
