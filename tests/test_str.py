from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from .conftest import π_t


def test_str(π: π_t):
	π.align = "<20"

	π <<= "MEOW MEOW, MEOW!!"
	π <<= "MEOW MEOW, MEOW!!  "
	π <<= "  MEOW MEOW, MEOW!!"
	π <<= "  MEOW MEOW, MEOW!!  "

	print()
	π << "should_not_contain_quotes_since_all_chars_are_ascii_printable"

	print()
	π <<= "🐱"  # cat kitty cat cat kitty cat cat


def test_str_bbcode_NOT_rendered(π: π_t):
	π <<= "[red]NOT RENDERED AS RED"


def test_str_whitespace(π: π_t):
	π.align = ">12"
	π.sep = " -> "

	print()
	π <<= " "
	π <<= " " * 2
	π <<= " " * 3
	π <<= " " * 4
	π <<= " " * 5
	π <<= " " * 6
	π <<= " " * 7
	π <<= " " * 8
	π <<= " " * 9
	π <<= " " * 10


def test_str_escapes(π: π_t):
	π.align = ">13"
	π.sep = " -> "

	π <<= 'a"b'
	π <<= "a'b"
	π <<= "a'\"b"
	π <<= "a'''\"\"\"b"
	π <<= "a'''\"b"
	print()
	π <<= "a\nb"
	π <<= "a\rb"
	π <<= "a\tb"
	π <<= "a\bb"
	π <<= "a\fb"
	print()
	π <<= "a\\b"

	print()
	long_str = """string repr contents (without quotes) that contain escaped \' single quotes and \" double quotes and ones before escaped backslashes too as you can see here: \\\' and ones that are already unescaped: \\', Lots of backslashes: \\\\\\\'"""
	π << long_str
	with π.fmt.with_tmp_settings():
		π.fmt.allow_triple_quotes_for_less_escaping = False
		π << "  " + long_str

	print()
	π << "string with\nnewlines and \r carriage returns"
	π << ["string with\nnewlines and \r carriage returns", ...]

	print()
	(
		π
		<< """Test pre-dedented docstring. This will not work (doctsring first line directly after opening triple quotes) on an indented docstring as it is checking for a \\n\\n.

	Args:
		shitass (ból): shitass is a boolean that indicates whether the function should be shitass or not. If shitass is True, the function will be shitass. If shitass is False, the function will not be shitass.

	Returns:
		nothing (Literal['']): absolutely fucking nothing (also known as `{#|}`)

	Raises:
		ass
"""[:-1]
	)
