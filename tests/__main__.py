from collections.abc import Callable
from typing import TYPE_CHECKING

from nya_scope import Scope

from .conftest import _print_header, π_t
from .conftest import fmt as fmt_fixture
from .conftest import π as π_fixture
from .test_ast import test_ast
from .test_bool import test_bool
from .test_ellipsis import test_ellipsis
from .test_iterable import test_nonhash_iterable, test_set
from .test_none import test_none
from .test_number import test_float, test_int

if TYPE_CHECKING:
	import nya_fmt as nf


def main():
	class InstallRichTraceback__(Scope):  # install rich traceback without polluting the main scope
		import os

		from rich.traceback import install

		install(
			width=os.get_terminal_size().columns,
		)

	TESTS: list[Callable[[π_t], None]] = [
		test_bool,
		test_none,
		test_ellipsis,
		test_int,
		test_float,
		test_nonhash_iterable,
		test_set,
		test_ast,
	]

	for test_fn in TESTS:
		if True:  # manually invoke the fixture functions to get π, assume they are per-function always
			get_fmt: Callable[[], nf.Formatter] = fmt_fixture._get_wrapped_function()
			get_π: Callable[[nf.Formatter], π_t] = π_fixture._get_wrapped_function()

			π = get_π(get_fmt())

		_print_header(test_fn.__name__)
		test_fn(π)


if __name__ == "__main__":
	main()
