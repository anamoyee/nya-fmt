from collections.abc import Generator
from typing import Self

import pytest
import rich
from rich.text import Text

import nya_fmt as nf

PRINT_HEADER_LAST_WIDTH_PRINTED: int = 80  # fallback


def _print_header(title: str, *, colored: bool = True) -> None:
	global PRINT_HEADER_LAST_WIDTH_PRINTED

	color_str_gold = "yellow b" if colored else ""
	color_str_white = "white b" if colored else ""

	middle = Text("### ", style=color_str_gold) + Text(title, style=color_str_white) + Text(" ###", style=color_str_gold)

	width = len(middle.plain)

	PRINT_HEADER_LAST_WIDTH_PRINTED = width

	edge = Text("#" * width, style=color_str_gold)

	print("\r", end="")
	rich.print(
		*(
			"\r \b",  # remove the fucking green dot when the test passes
			"\n",
			edge,
			"\n",
			middle,
			"\n",
			edge,
			"\n\n",
		),
		sep="",
		end="",
	)


@pytest.fixture(autouse=True)
def _AUTOUSE_print_test_header(request) -> Generator[None]:
	name = request.node.function.__name__

	# if parametrized
	if hasattr(request.node, "callspec"):
		parametrization_name = request.node.callspec.id
		name += f"[{parametrization_name}]"

	_print_header(name)


@pytest.fixture(scope="session", autouse=True)
def _AUTOUSE_remove_last_dot():
	yield
	print("\r ", end="")


@pytest.fixture
def fmt() -> nf.Formatter:
	return nf.Formatter(
		debug_raise_exceptions=True,
	)


class π_t:
	"""Testing wrapper for the Formatter, with dunder helper methods for easy testing.

	Name comes from previous version of the library where the formatter was called print_iterable (and was often shortened to π in code due to it's long name).
	"""

	def __init__(self, fmt: nf.Formatter) -> None:
		object.__setattr__(self, "fmt", fmt)

	def __call__(self, x: object) -> Self:
		rich.print(self.fmt(x))
		return self

	def __setitem__(self, key: object, value: object) -> None:
		display_as_kwarg = nf.displayers.DisplayAsKeywordArg(
			str(key),
			value,
		)

		rich.print(self.fmt(display_as_kwarg))

	def __setattr__(self, key: str, value: object) -> None:
		self[key] = value

	def __getitem__(self, key: object) -> Self:
		"""Equivalent of adding a !r to a fmt(...), had it supported it :whyyy:."""  # noqa: DOC201
		self[repr(key)] = key

		return self

	def __lshift__(self, other: object) -> Self:
		self(other)
		return self

	def __ilshift__(self, other: object) -> Self:
		self[other]
		return self


@pytest.fixture
def π(fmt: nf.Formatter) -> π_t:
	return π_t(fmt)


def hr():
	rich.print(f"[white b]{"-" * PRINT_HEADER_LAST_WIDTH_PRINTED}")


def manual_parametrize(*values: object) -> Generator[object, None, None]:
	yielded_one = False

	for value in values:
		if yielded_one:
			print()
			hr()
			print()

		yielded_one = True

		yield value
