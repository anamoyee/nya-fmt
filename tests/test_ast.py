from __future__ import annotations

import ast
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
	from .conftest import π_t

from nya_fmt.formatter.providers.pystdlib import FP__ast__expr_VIA_dump, FP__ast__expr_VIA_unparse


def parse_expr(expr: str) -> ast.expr:
	return ast.parse(expr, mode="eval").body


class StringRepr:
	def __init__(self, repr_str: Any) -> None:
		self.repr_str = str(repr_str)

	def __repr__(self) -> str:
		return self.repr_str


def test_ast(π: π_t):
	for _ in π.parametrize_providers(
		FP__ast__expr_VIA_unparse(),
		FP__ast__expr_VIA_dump(),
	):
		π.comment(ast.Constant)

		π << parse_expr("1")
