from __future__ import annotations

import ast
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
	from .conftest import π_t

from nya_fmt.formatter.providers.pystdlib import FP__ast__expr_VIA_astpretty_into_unparse, FP__ast__expr_VIA_unparse


def parse_expr(expr: str) -> ast.expr:
	return ast.parse(expr, mode="eval").body


class StringRepr:
	def __init__(self, repr_str: Any) -> None:
		self.repr_str = str(repr_str)

	def __repr__(self) -> str:
		return self.repr_str


def test_ast(π: π_t):
	for _ in π.parametrize_providers(
		FP__ast__expr_VIA_astpretty_into_unparse(),
		FP__ast__expr_VIA_unparse(),
	):
		π.comment(ast.Constant)
		π << parse_expr("1")

		π.comment(ast.Call)
		π << parse_expr("f()")
		π << parse_expr("f(1)")
		π << parse_expr("f(kw=1)")
		π << parse_expr("f(1, kw=1)")
		π << parse_expr("f(1, 2, 3, kw1=4, kw2=5, kw3=6)")
		# todo: this currently skips mutliple keyword arguments with the same name, which is technically not invalid, but would be nice if it would just be reflected within the ast repr and not skipped
		# π << parse_expr("f(kw=1, kw=2)")

		π.comment(ast.Name)
		π << parse_expr("x")

		π.comment(ast.Attribute)
		π << parse_expr("x.y.z")

		π.comment(ast.Set)
		π << parse_expr("set()")
		π << parse_expr("{1}")
		π << parse_expr("{1, 2, 3}")

		π.comment(ast.Dict)
		π << parse_expr("{}")
		π << parse_expr("{'a': 1}")
		π << parse_expr("{'a': 1, 'b': 2, 'c': 3}")
		π << parse_expr("{**d, 'a': 1, 'b': 2, 'c': 3}")
		π << parse_expr("{**d, 'a': 1, 'b': 2, 'c': 3, **d}")
		π << parse_expr("{'a': 1, 'b': 2, 'c': 3, **d}")

		π.comment(ast.UnaryOp)
		π << parse_expr("not True")
		π << parse_expr("~1")
		π << parse_expr("-1")
		π << parse_expr("+1")
		π << parse_expr("~(not(-+1))")
		π << parse_expr("~(not not(-+1))")

		π.comment(ast.BinOp)
		π << parse_expr("1 + 2")
		π << parse_expr("1 - 2")
		π << parse_expr("1 * 2")
		π << parse_expr("1 / 2")
		π << parse_expr("1 // 2")
		π << parse_expr("1 % 2")
		π << parse_expr("1 ** 2")
		π << parse_expr("1 << 2")
		π << parse_expr("1 >> 2")
		π << parse_expr("1 | 2")
		π << parse_expr("1 ^ 2")
		π << parse_expr("1 & 2")
		print()
		π << parse_expr("1 + 2 * 3 - 4 / 5 // 6 % 7 ** 8 << 9 >> 10 | 11 ^ 12 & 13")
		π << parse_expr(
			"(1 + 3) * 4"
			# todo: theese parentheses get removed, you should detect lower precedence in _inflight_stack and add parentheses if needed
		)

		π.comment(ast.BoolOp)
		π << parse_expr("a and b")
		π << parse_expr("a or b")
		π << parse_expr("a and b or c")
		π << parse_expr("a and b and c")

		π.comment(ast.NamedExpr)
		π << parse_expr("(x := 1)")
		π << parse_expr("(x := (y := 1))")

		π.comment(ast.Lambda)
		π << parse_expr("lambda: None")
		π << parse_expr("lambda x: x")
		π << parse_expr("lambda x, y: x")
		π << parse_expr("lambda x, y, z: x")
		π << parse_expr("lambda x, y, z, /: x")
		π << parse_expr("lambda x, y, /, z: x")
		π << parse_expr("lambda x, /, y, z: x")
		π << parse_expr("lambda *, x, y, z: x")
		π << parse_expr("lambda x, *, y, z: x")
		π << parse_expr("lambda x, y, *, z: x")
		π << parse_expr("lambda x, /, y, *, z: x")
		π << parse_expr("lambda x, y, /, *, z: x")
		π << parse_expr("lambda x, y=1: x + y")  # todo: impl

		π.comment(ast.IfExp)
		π << parse_expr("x if a else y")

		π.comment(ast.ListComp)
		π << parse_expr("[... for x in ...]")
		π << parse_expr("[... for x in ... if ...]")
		π << parse_expr("[... for x in ... if ... if ...]")
		π << parse_expr("[... for x in ... if ... if ... for y in ... if ...]")

		π.comment(ast.SetComp)
		π << parse_expr("{x for x in xs}")

		π.comment(ast.DictComp)
		π << parse_expr("{k: v for k, v in xs}")

		π.comment(ast.GeneratorExp)
		π << parse_expr("(x for x in xs)")

		π.comment(ast.Tuple)
		π << parse_expr("()")
		π << parse_expr("(1,)")
		π << parse_expr("(1, 2, 3)")

		π.comment(ast.List)
		π << parse_expr("[]")
		π << parse_expr("[1]")
		π << parse_expr("[1, 2, 3]")

		π.comment(ast.Await)
		π << parse_expr("await x")

		π.comment(ast.Yield)
		π << parse_expr("(yield)")
		π << parse_expr("(yield x)")

		π.comment(ast.YieldFrom)
		π << parse_expr("(yield from x)")

		π.comment(ast.Compare)
		π << parse_expr("1 == 2")
		π << parse_expr("1 < 2 < 3")
		π << parse_expr("1 in xs")
		π << parse_expr("1 in xs in xs")
		π << parse_expr("1 is not None")
		π << parse_expr("1 is not None > 3")

		# π.comment(ast.JoinedStr) # todo: impl
		# π << parse_expr('f"hello {1}"')
		# π << parse_expr('f"hello {1!r:s}"')

		# if sys.version_info >= (3, 14):
		# 	π.comment(ast.TemplateStr) # todo: impl
		# 	π << parse_expr('t"hello {1}"')
		# 	π << parse_expr('t"hello {1!r:s}"')

		π.comment(ast.Subscript)
		π << parse_expr("x[0]")
		π << parse_expr("x[1:2]")
		π << parse_expr("x[1:2:3]")
		π << parse_expr("x[:3]")
		π << parse_expr("x[:]")

		π.comment(ast.Starred)
		π << parse_expr("[*x]")

		π.comment(ast.List)
		π << parse_expr("[]")
		π << parse_expr("[1]")
		π << parse_expr("[1, 2, 3]")
