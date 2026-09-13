import typing as t

from nya_result import ResultDirect, ResultIndirect

from nya_fmt import Styles

from .conftest import π_t


def test_result_direct_ok(π: π_t):
	π << ResultDirect[int, t.Any].new_ok(42)


def test_result_direct_err(π: π_t):
	π << ResultDirect[t.Any, TypeError].new_err(TypeError("An error occurred"))


def test_result_indirect_ok(π: π_t):
	π << ResultIndirect[int, t.Any].new_ok(42)


def test_result_indirect_err(π: π_t):
	π << ResultIndirect[t.Any, TypeError].new_err(TypeError("An error occurred"))


def test_result_large_inner(π: π_t):
	π << ResultDirect[Styles, t.Any].new_ok(π.fmt.styles)
