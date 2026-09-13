from __future__ import annotations

import ast
from typing import TYPE_CHECKING

import nya_fmt as nf

if TYPE_CHECKING:
	from .conftest import π_t


def test_slice(π: π_t):
	π.align = ">25"
	π.sep = " -> "

	def _c(n: int | None) -> ast.Constant:
		return ast.Constant(value=n)

	π <<= slice(1, 2, 3)
	π <<= slice(1, 2)
	π <<= slice(1)
	π <<= slice(None, 2, 3)
	π <<= slice(None, 2)
	π <<= slice(None)
	π <<= slice(1, None, 3)
	π <<= slice(1, None)
	π <<= slice(None, None, 3)
	print()
	π <<= slice("a", "b", "c")
	π <<= slice("a", "b")
	π <<= slice("a")
	π <<= slice(None, "b", "c")
	π <<= slice(None, "b")
	π <<= slice(None)
	π <<= slice("a", None, "c")
	π <<= slice("a", None)
	π <<= slice(None, None, "c")
	print()
	π.align = ">130"
	with π.fmt.with_tmp_settings():
		π.fmt.ensure_provider_types_missing(
			nf.formatter.providers.pystdlib.FP__ast__expr_VIA_astpretty_into_unparse,
		)
		π.fmt.ensure_providers_present(
			nf.formatter.providers.pystdlib.FP__ast__expr_VIA_unparse(),
		)
		π <<= slice(_c(1), _c(2), _c(3))
		π <<= slice(_c(1), _c(2))
		π <<= slice(_c(1))
		π <<= slice(_c(None), _c(2), _c(3))
		π <<= slice(_c(None), _c(2))
		π <<= slice(_c(None))
		π <<= slice(_c(1), _c(None), _c(3))
		π <<= slice(_c(1), _c(None))
		π <<= slice(_c(None), _c(None), _c(3))
