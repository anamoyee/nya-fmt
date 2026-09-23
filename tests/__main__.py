import sys
from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol

from nya_scope import Scope

from .conftest import _print_header, π_t
from .conftest import fmt as fmt_fixture
from .conftest import π as π_fixture
from .test_ast import test_ast
from .test_bool import test_bool
from .test_datetime import test_date, test_datetime, test_time
from .test_ellipsis import test_ellipsis
from .test_enum import test_enum, test_hikari_enum
from .test_function import test_function, test_lambda
from .test_iterable import (
	test_dict,
	test_infinite_generator,
	test_iterable_max_display_len_overflow_on_listlike,
	test_iterable_max_display_len_overflow_on_mappinglike,
	test_nonhash_iterable,
	test_set,
)
from .test_meta import test_formatter
from .test_none import test_none
from .test_number import test_float, test_hexint, test_int, test_intable_float_looks_different_than_int, test_unixtimestampint
from .test_nyafmt import test_nyafmt
from .test_rich import test_rich_style, test_rich_text
from .test_slice import test_slice
from .test_str import test_str, test_str_bbcode_NOT_rendered, test_str_escapes, test_str_whitespace

if TYPE_CHECKING:
	import nya_fmt as nf


class TestFnT(Protocol):
	__name__: str

	def __call__(self, π: π_t) -> None: ...


def main():
	class _(Scope):  # install rich traceback without polluting the main scope
		import os

		from rich.traceback import install

		install(
			width=os.get_terminal_size().columns,
		)

	test_names_to_keep = tuple(f"test_{name}" for name in sys.argv[1:])

	TESTS: list[TestFnT] = [
		test_bool,
		test_none,
		test_ellipsis,
		test_int,
		test_float,
		test_intable_float_looks_different_than_int,
		test_nonhash_iterable,
		test_set,
		test_hexint,
		test_nyafmt,
		test_unixtimestampint,
		test_date,
		test_time,
		test_datetime,
		test_lambda,
		test_formatter,
		test_rich_style,
		test_rich_text,
		test_function,
		test_slice,
		test_str_whitespace,
		test_str_bbcode_NOT_rendered,
		test_str,
		test_str_escapes,
		test_dict,
		# test_ast,
		test_enum,
		test_hikari_enum,
		# test_iterable_max_display_len_overflow_on_listlike,
		# test_iterable_max_display_len_overflow_on_mappinglike,
		# test_infinite_generator,
	]

	class _(Scope):  # Test for duplicates in TESTS, raise RuntimeError if duplicate found
		__test_for_duplicates_set = set()  # ruff:ignore[mutable-class-default]
		for test_fn in TESTS:
			if test_fn.__name__ in __test_for_duplicates_set:
				msg = f"Duplicate test function in `TESTS`: {test_fn.__name__}"
				raise RuntimeError(msg)
			__test_for_duplicates_set.add(test_fn.__name__)
		del __test_for_duplicates_set

	for test_fn in TESTS:
		if test_names_to_keep and test_fn.__name__ not in test_names_to_keep:
			continue

		if True:  # manually invoke the fixture functions to get π, assume they are per-function always
			get_fmt: Callable[[], nf.Fmt] = fmt_fixture._get_wrapped_function()
			get_π: Callable[[nf.Fmt], π_t] = π_fixture._get_wrapped_function()

			π = get_π(get_fmt())

		_print_header(test_fn.__name__)
		test_fn(π)


if __name__ == "__main__":
	main()
