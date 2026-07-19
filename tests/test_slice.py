from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from .conftest import π_t


def test_slice(π: π_t):
	π.align = ">25"
	π.sep = " -> "

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
