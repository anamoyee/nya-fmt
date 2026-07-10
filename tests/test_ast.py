from __future__ import annotations

import ast
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .conftest import π_t

from nya_fmt.formatter.providers.builtins_ import AST_expr_DumpFP, AST_expr_UnparseFP


def parse_expr(expr: str) -> ast.expr:
    return ast.parse(expr, mode="eval").body


class StringRepr:
    def __init__(self, repr_str: Any) -> None:
        self.repr_str = str(repr_str)

    def __repr__(self) -> str:
        return self.repr_str


def test_ast(π: π_t):
    for TestedProvider in π.manual_parametrize(
        *(
            all_tested_providers := (
                AST_expr_UnparseFP,
                AST_expr_DumpFP,
            )
        )
    ):
        with π.fmt.with_tmp_settings():
            π.fmt.providers = (
                *(
                    provider
                    for provider in π.fmt.providers
                    if provider not in all_tested_providers
                ),
                TestedProvider,
            )

            π.comment(ast.Constant)

            π << parse_expr("1")
