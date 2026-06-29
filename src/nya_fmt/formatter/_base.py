from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from types import FunctionType
from typing import Any, Self

import rich
from rich.style import Style
from rich.text import Text

from . import displayers as m_displayers
from . import providers as m_providers


@dataclass(kw_only=True)
class Styles:
	# fmt: off
	keyword: Style            = field(default_factory=lambda: Style.parse("b #ee8d55"))
	punctuation: Style        = field(default_factory=lambda: Style.parse("b white"))
	string: Style             = field(default_factory=lambda: Style.parse("b yellow"))
	number: Style             = field(default_factory=lambda: Style.parse("b blue"))
	true: Style               = field(default_factory=lambda: Style.parse("b green"))
	false: Style              = field(default_factory=lambda: Style.parse("b red"))
	none: Style               = field(default_factory=lambda: Style.parse("b bright_black"))
	comma: Style              = field(default_factory=lambda: Style.parse("not b cyan")) # ("b bright_black"))
	bracket: Style            = field(default_factory=lambda: Style.parse("b cyan"))
	type: Style               = field(default_factory=lambda: Style.parse("b blue"))
	function: Style           = field(default_factory=lambda: Style.parse("b yellow"))
	error: Style              = field(default_factory=lambda: Style.parse("not b red"))
	module: Style             = field(default_factory=lambda: Style.parse("b orange1"))
	unknown_attribute: Style  = field(default_factory=lambda: Style.parse("b grey62"))
	keyword_arg_name: Style   = field(default_factory=lambda: Style.parse("b grey78"))
	guess: Style              = field(default_factory=lambda: Style.parse("b cyan"))
	"""Used as a color for e.g. `?` (possibly other characters or multi-char indicators in the future) to signify that the further representation has been guessed, for example by `ast.parse`'ing a repr() result, and not rendered from source, structured data."""

	letter_p_Path: Style      = field(default_factory=lambda: Style.parse("b blue"))
	letter_F_frozenset: Style = field(default_factory=lambda: Style.parse("b blue"))
	# fmt: on

	@classmethod
	def no_syntax_highlighting(cls) -> Self:
		return cls(**{
			field_name: Style.null()  #
			for field_name in cls.__dataclass_fields__
		})


@dataclass(kw_only=True)
class Formatter:
	styles: Styles = field(default_factory=Styles)
	indent: str | None = " " * 2
	"""The indentation given to nested structures, e.g. lists, dicts, calls, ...other.

	- For `indent=None`
		```python
		[1, 2, 3]
		```
		Tip: If you want to have a compact look (`[1,2,3]`, notice no spaces?), set `redundant_whitespace` to `False` as well.

	- For `indent=" "*2` (default)
		```python
		[
		  1,
		  2,
		  3,
		]
		```

	- For `indent=""`
		```python
		[
		1,
		2,
		3,
		]
		```
	- This is an arbitrary string so anything can be used, (`indent=";;;;"`):
		```
		{
		;;;;Scanf(("%d", 67))
		;;;;Printf(("Score: %d", 42))
		}
		```
	"""  # noqa: E101
	redundant_whitespace: bool = True
	"""Whether to include redundant whitespace in the output, e.g. spaces after commas, colons, etc. If `False`, the output will be more compact, but less readable.

	If you are going for a compact look, it is recommended to also set `indent` to None.
	"""

	debug_raise_exceptions: bool = False

	providers: tuple[m_providers.FormatProviderABC, ...] = field(
		default_factory=lambda: tuple(m_providers.FormatProviderABC.iter_default_providers())
	)

	number_pos_char: str = ""
	number_neg_char: str = "-"
	number_decimal: str = "."

	prefer_short_name: bool = False
	"""Whether to prefer `__qualname__` over `__name__` when displaying `type`s."""

	no_quoteless_str: bool = False
	"""Prevent the behaviour of displaying simple (non-space, non-special chars) strings without quotes."""

	float_format_specifier: str = "g"
	"""f'{float_instance:{float_format_specifier}}' is used to format floats."""

	include_at_notation: bool = True
	"""Whether to append stuff like @dataclass before dataclass objects."""

	include_memory_addresses_in_unknown_objects: bool = True
	"""Whether to include memory addresses in the display of objects that don't have a specific format provider."""

	try_parse_ast_if_only_repr_available: bool = True
	"""Guess the structure of an object based on thet repr() it produces, if it is a valid python expression, parse it and syntax-highlight. Otherwise print raw repr string in the parenthesis."""

	include_guess_question_mark: bool = True
	"""Whether to include the given notation: `Type?(guessed_repr_formatting)` instead of Type(guessed_repr_formatting) when the formatter has to guess the structure of an object based on its repr() output, if it is a valid python expression, parse it and syntax-highlight."""

	def add_indent(self, text: Text) -> Text:
		if self.indent is None:
			return text

		return Text("\n").join(
			Text(self.indent) + line  #
			for line in text.split("\n")
		)

	def __call__(self, __v: Any, /) -> Text:
		return self.fmt(__v)

	def __repr__(self) -> str:
		return f"{self.__class__.__name__}()"

	def fmt(self, v: Any, /) -> Text:
		for provider in self.providers:
			result = provider.try_fmt(v, fmt=self)
			if result.is_some:
				return result.unwrap()

		msg = f"{self.__class__.__name__}.fmt is not implemented for type {v.__class__.__name__}"
		raise NotImplementedError(msg)

	def __lshift__(self, other: object) -> Self:
		rich.print(self(other))
		return self

	def __or__[OtherT](self, other: OtherT) -> OtherT:
		rich.print(self(other))
		return other

	def __ror__[OtherT](self, other: OtherT) -> OtherT:
		return self | other

	@contextmanager
	def with_tmp_settings(self) -> Generator[None, None, None]:
		before = {field_name: getattr(self, field_name) for field_name in self.__dataclass_fields__}

		try:
			yield
		finally:
			for field_name, value in before.items():
				setattr(self, field_name, value)

	if True:  # fh (fmt helper) methods
		if True:  # canonical representations

			def _fh__space(self) -> Text:
				"""Return Text(" ") if redundant spaces are enabled, otherwise Text()."""
				return Text(" ") if self.redundant_whitespace else Text()

			def _fh__comma(self) -> Text:
				"""Return canonical stylizing of a comma (`,`)."""
				return Text(",", style=self.styles.comma)

			def _fh__colon(self) -> Text:
				"""Return canonical stylizing of a colon (`:`)."""
				return Text(":", style=self.styles.punctuation)

			def _fh__guess_question_mark(self) -> Text:
				"""Return canonical stylizing of a question mark (`?`) used for guessed representations."""
				return Text("?", style=self.styles.guess) if self.include_guess_question_mark else Text()

		def _fh__get_partial_name_of_type(self, v: type | FunctionType) -> str:
			"""Return the `__name__` or `__qualname__` of the type `v`."""
			if not self.prefer_short_name:
				return v.__qualname__  # no need to safeguard qualname, as it's guarded by python itself

			if hasattr(v, "__name__"):
				try:
					name = v.__name__
				except Exception:
					pass
				else:
					if isinstance(name, str):
						return str(name)  # convert to normal str, not any subclass

			return v.__qualname__  # fallback if name if not present or of wrong type.

		def _fh__get_full_name_of_type(self, v: type | FunctionType) -> str:
			"""Return the full name of the type | FunctionType `v`, including the module if present."""
			name = self._fh__get_partial_name_of_type(v)

			if self.prefer_short_name:
				return name

			try:
				module = v.__module__
				if module and isinstance(module, str):
					name = f"{module!s}.{name}"

			except Exception:
				return name
			else:
				return name  # weird-looking...

		def _fh__raw_in_parens(self, text: Text) -> Text:
			"""Format a call-like appearence with the given text, e.g. `(arg1, arg2, kw1=...)`, delegating formatting args and kwargs as to the caller (you have to evaluate them into a Text beforehand).

			Returns:
				text: The formatted representation of the call. This does not include the callable identifier (append it if you need it, e.g. `fmt(type(v)) + fmt._fh__call(...)`).
			"""
			return Text("(", style=self.styles.bracket) + text + Text(")", style=self.styles.bracket)

		def _fh__raw_in_brackets(self, text: Text) -> Text:
			"""Format a list/getattr-like appearence with the given text, e.g. `[arg1, arg2, kw1=...]`, delegating formatting args and kwargs as to the caller (you have to evaluate them into a Text beforehand).

			Returns:
				text: The formatted representation of the list. If you meant to display a getattr, add the identifier manually (append it via `fmt(type(v)) + fmt._fh__call(...)`).
			"""
			return Text("[", style=self.styles.bracket) + text + Text("]", style=self.styles.bracket)

		def _fh__raw_in_curlys(self, text: Text) -> Text:
			"""Format a (dict/set)-like appearence with the given text, e.g. `{arg1, arg2, kw1=...}`, delegating formatting args and kwargs as to the caller (you have to evaluate them into a Text beforehand).

			Returns:
				text: The formatted representation of the dict.
			"""
			return Text("{", style=self.styles.bracket) + text + Text("}", style=self.styles.bracket)

		def _fh__call(self, *args: object, **kwargs: object) -> Text:
			"""Format a call with the given args and kwargs, e.g. `(arg1, arg2, kw1=...)`, foarmtting args and kwargs in the process.

			Returns:
				text: The formatted representation of the call. This does not include the callable identifier (append it if you need it, e.g. `fmt(type(v)) + fmt._fh__call(...)`).
			"""

			kwargs_display = [m_displayers.args.DisplayAsKeywordArg(key, value) for key, value in kwargs.items()]

			return self(
				m_displayers.iterable.CallFromTupleDisplay((
					*args,
					*kwargs_display,
				))
			)

		def _fh__call2(
			self,
			*,
			args: object,
			kwargs: object,
			prefix: Text = Text(),
			suffix: Text = Text(),
		) -> Text:
			"""Alternative implementation of `_fh__call` that allows for more control over the formatting: prefix and suffix text.

			Read the docstring of `_fh__call` for more information.

			#### ⚠️ Note that the output might slighly differ (think: indentation/whitespace) from `_fh__call` in some cases, so use this only if you need the extra control. Otherwise, use `_fh__call`.
			TODO: Test the two functions to full equality in the output for same inputs, so the above warning can be removed.

			Returns:
				text: The formatted representation of the call. This does not include the callable identifier (append it if you need it, e.g. `fmt(type(v)) + fmt._fh__call(...)`).
			"""

			kwargs_display = [m_displayers.args.DisplayAsKeywordArg(key, value) for key, value in kwargs.items()]

			return self(
				self._fh__raw_in_parens(
					"".join((
						prefix,
						self._fh__comma().join(
							self(x)  #
							for x in (
								*args,
								*kwargs_display,
							)
						),
						suffix,
					))
				)
			)
