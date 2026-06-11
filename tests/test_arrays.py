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

from expression import Expression


def evaluate(expr_str):
    """Evaluate an expression with a fresh Expression instance."""
    return Expression().evaluate(expr_str)


# ----------------------------------------------------------------------
# Intersection (&)
# ----------------------------------------------------------------------
def test_intersection_basic():
    assert evaluate("[1, 1, 2, 3] & [3, 4]") == [3]


def test_intersection_strings():
    assert evaluate('["a", "b", "c"] & ["c", "a"]') == ["a", "c"]


def test_intersection_disjoint():
    assert evaluate("[1, 2] & [3, 4]") == []


def test_intersection_empty_left():
    assert evaluate("[] & [1, 2]") == []


def test_intersection_empty_right():
    assert evaluate("[1, 2] & []") == []


def test_intersection_preserves_left_order():
    assert evaluate("[3, 1, 2] & [2, 3, 1]") == [3, 1, 2]


def test_intersection_dedupes():
    assert evaluate("[1, 1, 2] & [1, 2]") == [1, 2]


# ----------------------------------------------------------------------
# Union (|)
# ----------------------------------------------------------------------
def test_union_basic():
    assert evaluate("[1, 2] | [2, 3]") == [1, 2, 3]


def test_union_dedupes():
    assert evaluate("[1, 1, 2] | [2, 3]") == [1, 2, 3]


def test_union_empty():
    assert evaluate("[] | [1, 2]") == [1, 2]
    assert evaluate("[1, 2] | []") == [1, 2]


def test_union_preserves_order():
    assert evaluate("[3, 1] | [2, 3]") == [3, 1, 2]


# ----------------------------------------------------------------------
# Difference (-)
# ----------------------------------------------------------------------
def test_difference_basic():
    assert evaluate("[1, 2, 2, 3] - [2]") == [1, 3]


def test_difference_no_overlap():
    assert evaluate("[1, 2, 3] - [4, 5]") == [1, 2, 3]


def test_difference_full_overlap():
    assert evaluate("[1, 2, 3] - [1, 2, 3]") == []


def test_difference_empty_right():
    assert evaluate("[1, 2] - []") == [1, 2]


# ----------------------------------------------------------------------
# Concatenation (+)
# ----------------------------------------------------------------------
def test_concat_basic():
    assert evaluate("[1, 2] + [2, 3]") == [1, 2, 2, 3]


def test_concat_preserves_dupes():
    assert evaluate("[1, 1] + [1, 1]") == [1, 1, 1, 1]


def test_concat_empty():
    assert evaluate("[] + [1]") == [1]
    assert evaluate("[1] + []") == [1]


def test_concat_chained():
    assert evaluate('["a"] + ["b"] + ["c"]') == ["a", "b", "c"]


# ----------------------------------------------------------------------
# Append (<<)
# ----------------------------------------------------------------------
def test_append_literal():
    assert evaluate("[1, 2] << 3") == [1, 2, 3]


def test_append_mutates_variable():
    expr = Expression()
    expr.evaluate("arr = [1, 2]")
    expr.evaluate("arr << 3")
    assert expr.evaluate("arr") == [1, 2, 3]


def test_append_chained():
    assert evaluate("[1] << 2 << 3") == [1, 2, 3]


def test_bitshift_still_works():
    # << must remain bitshift for integers
    assert evaluate("100 << 2") == 400


# ----------------------------------------------------------------------
# Multiplication / Join (*)
# ----------------------------------------------------------------------
def test_array_times_int():
    assert evaluate("[1, 2] * 3") == [1, 2, 1, 2, 1, 2]


def test_array_times_zero():
    assert evaluate("[1, 2] * 0") == []


def test_array_times_one():
    assert evaluate("[1, 2] * 1") == [1, 2]


def test_array_join_with_string():
    assert evaluate('["a", "b"] * "-"') == "a-b"


def test_array_join_single():
    assert evaluate('["a"] * ","') == "a"


def test_array_join_empty():
    assert evaluate('[] * "-"') == ""


def test_array_join_numbers():
    assert evaluate('[1, 2, 3] * ", "') == "1, 2, 3"


# ----------------------------------------------------------------------
# Equality (==)
# ----------------------------------------------------------------------
def test_array_eq_same():
    assert evaluate("[1, 2] == [1, 2]") is True


def test_array_eq_different_order():
    assert evaluate("[1, 2] == [2, 1]") is False


def test_array_eq_different_length():
    assert evaluate("[1, 2] == [1, 2, 3]") is False


def test_array_eq_empty():
    assert evaluate("[] == []") is True


def test_array_eq_nested():
    assert evaluate("[[1, 2], [3]] == [[1, 2], [3]]") is True


def test_array_neq():
    assert evaluate("[1, 2] != [2, 1]") is True


# ----------------------------------------------------------------------
# Spaceship (<=>)
# ----------------------------------------------------------------------
def test_spaceship_less():
    assert evaluate("[1, 2] <=> [1, 3]") == -1


def test_spaceship_greater():
    assert evaluate("[1, 3] <=> [1, 2]") == 1


def test_spaceship_equal():
    assert evaluate("[1, 2] <=> [1, 2]") == 0


def test_spaceship_prefix_shorter():
    assert evaluate("[1] <=> [1, 2]") == -1


def test_spaceship_prefix_longer():
    assert evaluate("[1, 2] <=> [1]") == 1


# ----------------------------------------------------------------------
# Membership (in)
# ----------------------------------------------------------------------
def test_in_present():
    assert evaluate("2 in [1, 2, 3]") is True


def test_in_absent():
    assert evaluate("4 in [1, 2, 3]") is False


def test_in_string():
    assert evaluate('"x" in ["x", "y"]') is True


def test_in_empty():
    assert evaluate("1 in []") is False


# ----------------------------------------------------------------------
# Empty-array truthiness (Requirement 1)
# ----------------------------------------------------------------------
def test_empty_is_falsy():
    assert evaluate("!![]") is False
    assert evaluate("![]") is True


def test_non_empty_is_truthy():
    assert evaluate("!![1]") is True
    assert evaluate("!!['a']") is True


def test_empty_short_circuits_or():
    assert evaluate('[] || "default"') == "default"


def test_non_empty_short_circuits_and():
    assert evaluate("[1] && 42") == 42


def test_empty_in_conditional():
    # Used in if-like expressions
    assert evaluate("[] ? 'yes' : 'no'") == "no"
    assert evaluate("[1] ? 'yes' : 'no'") == "yes"


# ----------------------------------------------------------------------
# Mixed-type coercion (Requirement 2)
# ----------------------------------------------------------------------
def test_intersect_array_scalar():
    assert evaluate("[1, 2, 3] & 2") == [2]


def test_intersect_array_string():
    assert evaluate('["AI", "ML"] & "AI"') == ["AI"]


def test_intersect_scalar_array():
    assert evaluate("2 & [1, 2, 3]") == [2]


def test_concat_scalar_array():
    assert evaluate("1 + [2, 3]") == [1, 2, 3]


def test_concat_array_scalar():
    assert evaluate("[1, 2] + 3") == [1, 2, 3]


def test_difference_array_scalar():
    assert evaluate("[1, 2, 3] - 2") == [1, 3]


# ----------------------------------------------------------------------
# Validator-pattern integration
# ----------------------------------------------------------------------
def test_validator_include_pattern():
    """match.include replacement: at least one skill matches."""
    expr = Expression()
    expr.variables = {"skills": ["Python", "React", "AI"]}
    assert bool(expr.evaluate('skills & ["AI", "ML"]')) is True
    assert bool(expr.evaluate('skills & ["Java", "C#"]')) is False


def test_validator_exclude_pattern():
    """match.exclude replacement: no skill matches blacklist."""
    expr = Expression()
    expr.variables = {"skills": ["Python", "Django"]}
    assert bool(expr.evaluate('skills & ["Angular", "C#"] == []')) is True
    assert bool(expr.evaluate('skills & ["Python", "Java"] == []')) is False


def test_validator_combined():
    """Combined include and exclude."""
    expr = Expression()
    expr.variables = {"skills": ["Python", "AI", "React"]}
    # Has AI/ML AND doesn't have Angular/Java
    result = expr.evaluate(
        '(skills & ["AI", "ML"]) && (skills & ["Angular", "Java"] == [])'
    )
    assert bool(result) is True


# ----------------------------------------------------------------------
# Precedence
# ----------------------------------------------------------------------
def test_intersection_binds_tighter_than_eq():
    # (a & b) == (c & d), not a & (b == c) & d
    assert evaluate("[1, 2] & [2, 3] == [2]") is True


def test_intersection_binds_tighter_than_union():
    # a | (b & c), intersection first
    assert evaluate("[1] | [2, 3] & [3, 4]") == [1, 3]


def test_concat_binds_tighter_than_eq():
    assert evaluate("[1] + [2] == [1, 2]") is True
