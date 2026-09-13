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
from . import types as types_m


@dataclass(kw_only=True)
class Styles:
	# fmt: off
	keyword                           :Style= field(default_factory=lambda: Style.parse("b #ee8d55"))
	punctuation                       :Style= field(default_factory=lambda: Style.parse("b white"))
	punctuation_muted                 :Style= field(default_factory=lambda: Style.parse("b bright_black"))
	string                            :Style= field(default_factory=lambda: Style.parse("b yellow"))
	number                            :Style= field(default_factory=lambda: Style.parse("b bright_blue"))
	true                              :Style= field(default_factory=lambda: Style.parse("b green"))
	false                             :Style= field(default_factory=lambda: Style.parse("b red"))
	none                              :Style= field(default_factory=lambda: Style.parse("b bright_black"))
	comment                           :Style= field(default_factory=lambda: Style.parse("b bright_black"))
	comma                             :Style= field(default_factory=lambda: Style.parse("not b cyan")) # ("b bright_black"))
	bracket                           :Style= field(default_factory=lambda: Style.parse("b cyan"))
	type                              :Style= field(default_factory=lambda: Style.parse("b bright_blue"))
	function                          :Style= field(default_factory=lambda: Style.parse("b yellow"))
	error                             :Style= field(default_factory=lambda: Style.parse("not b red"))
	module                            :Style= field(default_factory=lambda: Style.parse("b orange1"))
	unknown_attribute                 :Style= field(default_factory=lambda: Style.parse("b grey62"))
	keyword_arg_name                  :Style= field(default_factory=lambda: Style.parse("b grey78"))
	guess                             :Style= field(default_factory=lambda: Style.parse("b cyan"))
	"""Used as a color for e.g. `?` (possibly other characters or multi-char indicators in the future) to signify that the further representation has been guessed, for example by `ast.parse`'ing a repr() result, and not rendered from source, structured data."""
	operator                          :Style= field(default_factory=lambda: Style.parse("b #e89064"))
	enum_member                       :Style= field(default_factory=lambda: Style.parse("b white"))
	iterable_max_display_len_overflow :Style= field(default_factory=lambda: Style.parse("b purple"))


	letter_p_Path      :Style= field(default_factory=lambda: Style.parse("b bright_blue"))
	letter_F_frozenset :Style= field(default_factory=lambda: Style.parse("b bright_blue"))
	word_Meta_enum     :Style= field(default_factory=lambda: Style.parse("b purple"))
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

	indent: str | None = " " * 4
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

	# todo: performance optimization: turn providers into a dict[type, tuple[provider]], type should be the broadest type that this provider supports,
	#       then the MRO of the type should be walked from the most specific to the least specific and the first provider from the list which accepts
	#       should be given the job.
	# todo: performance optimization: forgo Maybe type and instead return Text|None everywhere, instead of Maybe[Text], as i belive the creation of
	#       Maybe objects to then immediately unwrap them is really shitty on the performace.
	providers: tuple[m_providers.FormatProviderABC, ...] = field(
		default_factory=lambda: tuple(m_providers.FormatProviderABC.iter_default_providers())
	)

	doublequotes_preference: bool | None = None
	"""Whether to prefer double quotes over single quotes when formatting strings.

	- `None`: (recommended) Same as python repr, but with preference to doublequotes over single quotes, which means it WILL use singlequotes if the string contains doublequotes, but not single quotes, which would make the string look less cluttered with less escaping.
	- `True`: Always use double quotes, even if the string contains double quotes, which will require escaping them.
	- `False`: Same behaviour as python built-in `repr()` (prefer single quotes, but use double quotes if the string contains single quotes and not double quotes).
	- Sorry, no 'Always' option for singlequotes :c
	"""
	allow_triple_quotes_for_less_escaping: bool = False
	"""Whether to allow triple quotes (including both: made out of `'''` and `\"""`) whenever this would lead to less escaping within the string content."""
	allow_triple_quotes_for_newlines: bool = True
	"""Whether to allow triple quotes (including both: made out of `'''` and `\"""`) whenever the string contains newlines. This also enabled tabs (`\\t`) to be expanded into `indent` within a string that contains newlines"""

	prefer_short_name: bool = False
	"""Whether to prefer `__name__` over `__qualname__` when displaying `type`."""

	no_quoteless_str: bool = False
	"""Prevent the behaviour of displaying simple (non-space, non-special chars) strings without quotes."""

	int_format_specifier: str = "d"
	"""f'{int_instance:{int_format_specifier}}' is used to format integers."""
	float_format_specifier: str = "z#"
	"""f'{float_instance:{float_format_specifier}}' is used to format floats."""
	float_use_infinity_symbol: bool = True
	"""Whether to use the infinity symbol (∞) instead of 'inf' when formatting floats."""

	date_format_specifier: str = "%Y-%m-%d"
	"""f'{date_instance:{date_format_specifier}}' is used to format datetime.date."""

	time_format_specifier: str = "%H:%M:%S"
	"""f'{time_instance:{time_format_specifier}}' is used to format datetime.time."""

	include_at_notation: bool = True
	"""Whether to append stuff like @dataclass before dataclass objects."""

	include_memory_addresses_in_unknown_objects: bool = True
	"""Whether to include memory addresses in the display of objects that don't have a specific format provider."""

	try_parse_ast_if_only_repr_available: bool = True
	"""Guess the structure of an object based on thet repr() it produces, if it is a valid python expression, parse it and syntax-highlight. Otherwise print raw repr string in the parenthesis."""

	include_guess_question_mark: bool = True
	"""Whether to include the given notation: `Type?(guessed_repr_formatting)` instead of Type(guessed_repr_formatting) when the formatter has to guess the structure of an object based on its repr() output, if it is a valid python expression, parse it and syntax-highlight."""

	rich_style_preview: str = "Preview"
	"""Whether to format `rich.style.Style` with a preview, which's value is itself formatted with that style. To disable set this to `""`, any other value customizes the text."""

	rich_text_preview: bool = True
	"""Whether to format `rich.text.Text` with a preview of said text, within angle brackets."""

	rich_text_preview_max_len: int = 20
	"""The maximum length of the preview of `rich.text.Text` when `rich_text_preview` is `True`. If the text is longer than this, it will be truncated and a `(...)` will be added. Set to -1 to disable truncation (any other negative integer counts the same as -1)."""

	align_dataclass_field_keys_if_all_values_of_same_type: bool = True
	"""Whether to right-align the keys of dataclass fields if all values are of the same."""

	dataclass_key_align_char: str = " "
	"""The character to use for aligning dataclass field keys if `align_dataclass_field_keys_if_all_values_of_same_type` is `True`. This should be either len()=0 or len()=1, any other length will be truncated to 1 (thus characters as indices >=1 will have no effect). This is pasted directly (after aformentioned truncation) into the format specifier for the string key therefore a len()=0 string means align with str.__format__'s default (a space)."""

	iterable_max_display_len: int = 100
	"""The maximum number of items to display in an iterable, if the iterable is larger, ."""

	pydantic_field_descriptions: bool = True
	"""Whether to display a comment-style '# {field_info.description}' after pydantic model instance fields. Descriptions are a built-in, optional feature of pydantic."""

	_inflight_stack: list[object] = field(default_factory=list, repr=True)
	"""A list of objects that the next fmt() call will be canonically "providing" a subfomatting for.

	Items may format themselves differently based on this variable, each fmt() the object to be formatted is appended to this list, and popped afterwards.
	e.g. If you want to code the behaviour that ast nodes check for the parent node and decide if they need to wrap themselves in parentheses, you may check _inflight_stack[-2] for being an ast node that requires parenthesising
	While you shouldn't modify this list in a custom format provider, you technically can.
	"""

	def add_indent(self, text: Text) -> Text:
		if self.indent is None:
			return text

		return Text("\n").join(
			Text(self.indent) + line  #
			for line in text.split("\n")
		)

	def __call__(self, __v: object, /) -> Text:
		return self.fmt(__v)

	def __repr__(self) -> str:
		return f"{self.__class__.__name__}()"

	def fmt(self, v: object, /) -> Text:
		if any(id(v) == id(item) for item in self._inflight_stack):
			return self._fh__recursive_reference(v)

		self._inflight_stack.append(v)
		try:
			for provider in self.providers:
				result = provider.try_fmt(v, fmt=self)
				if result.is_some:
					return result.unwrap()
		finally:
			self._inflight_stack.pop()
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

	def ensure_providers_present(self, *providers: m_providers.FormatProviderABC) -> None:
		"""Ensure that the given providers are present in the formatter's providers list. If any of the given providers are not present, append them.

		Raises:
			TypeError: If any of the given providers are classes instead of instances. This causes many bugs if is allowed into the `providers` tuple.
		"""
		if any(isinstance(provider, type) for provider in providers):
			msg = "All providers must be instances, not classes. This causes many bugs if is allowed into the `providers` tuple."
			raise TypeError(msg)

		self.providers = (
			*(
				provider  #
				for provider in providers
				if provider not in self.providers
			),
			*self.providers,
		)

	def ensure_provider_types_missing(self, *provider_types: type[m_providers.FormatProviderABC]) -> None:
		"""Ensure that the given providers are not present in the formatter's providers list. If any of the given providers are present, remove them."""
		# todo: this does not work if type(self) is provided - subclassing breaks this
		# 1. replace type(self) with actual hardcoded self type, so subclasses dont do their own class, but rather the lowest class to remove
		# 2. make this do an isinstance check and not  ... wait this is already done , well impl the above

		self.providers = tuple(provider for provider in self.providers if not any(isinstance(provider, p_t) for p_t in provider_types))

	if True:  # fh (fmt helper) methods
		if True:  # canonical representations

			def _fh__space(self) -> Text:
				"""Return Text(" ") if redundant spaces are enabled, otherwise Text()."""
				# todo: find occurences where this function could've been used in builtin format providers, but a string literal is, this is a problem because it breaks self.redundant_whitespace setting
				return Text(" ") if self.redundant_whitespace else Text()

			def _fh__comma(self) -> Text:
				"""Return canonical stylizing of a comma (`,`)."""
				return Text(",", style=self.styles.comma)

			def _fh__colon(self) -> Text:
				"""Return canonical stylizing of a colon (`:`)."""
				return Text(":", style=self.styles.punctuation)

			def _fh__dot(self) -> Text:
				"""Return canonical stylizing of a dot (`.`)."""
				return Text(".", style=self.styles.punctuation)

			def _fh__ellipsis(self) -> Text:
				"""Return canonical stylizing of an ellipsis (`...`)."""
				return Text("...", style=self.styles.punctuation)

			def _fh__guess_question_mark(self) -> Text:
				"""Return canonical stylizing of a question mark (`?`) used for guessed representations."""
				return Text("?", style=self.styles.guess) if self.include_guess_question_mark else Text()

		def _fh__recursive_reference(self, v: object) -> Text:
			"""Return a canonical representation of a recursive reference, e.g. `<Recursive reference to Foo instance at 0x7f8c9c8c8c8c>`."""

			return Text().join((
				Text("<Recursive reference to ", style=self.styles.error),
				self(type(v)),
				Text(" instance at ", style=self.styles.error),
				self(types_m.HexInt(id(v), leading_zeroes=0)),
				Text(">", style=self.styles.error),
			))

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
				text: The formatted representation of the call. This does not include the callable identifier (append it if you need it, e.g. `fmt(type(v)) + fmt._fh__raw_in_parens(...)`).
			"""
			return Text("(", style=self.styles.bracket) + text + Text(")", style=self.styles.bracket)

		def _fh__raw_in_brackets(self, text: Text) -> Text:
			"""Format a list/getattr-like appearence with the given text, e.g. `[arg1, arg2, kw1=...]`, delegating formatting args and kwargs as to the caller (you have to evaluate them into a Text beforehand).

			Returns:
				text: The formatted representation of the list. If you meant to display a getattr, add the identifier manually (append it via `fmt(type(v)) + fmt._fh__raw_in_brackets(...)`).
			"""
			return Text("[", style=self.styles.bracket) + text + Text("]", style=self.styles.bracket)

		def _fh__raw_in_curlys(self, text: Text) -> Text:
			"""Format a (dict/set)-like appearence with the given text, e.g. `{arg1, arg2, kw1=...}`, delegating formatting args and kwargs as to the caller (you have to evaluate them into a Text beforehand).

			Returns:
				text: The formatted representation of the dict.
			"""
			return Text("{", style=self.styles.bracket) + text + Text("}", style=self.styles.bracket)

		def _fh__raw_in_angles(self, text: Text) -> Text:
			"""Format a genericdef-like appearence with the given text, e.g. `<arg1, arg2, kw1=...>`, delegating formatting args and kwargs as to the caller (you have to evaluate them into a Text beforehand).

			Returns:
				text: The formatted representation of the genericdef.
			"""
			return Text("<", style=self.styles.bracket) + text + Text(">", style=self.styles.bracket)

		def _fh__call(self, *args: object, **kwargs: object) -> Text:
			"""Format a call with the given args and kwargs, e.g. `(arg1, arg2, kw1=...)`, foarmtting args and kwargs in the process.

			Returns:
				text: The formatted representation of the call. This does not include the callable identifier (append it if you need it, e.g. `fmt(type(v)) + fmt._fh__call(...)`).
			"""

			kwargs_display = [m_displayers.args.DisplayAsKeywordArg(key, value) for key, value in kwargs.items()]

			return self(
				m_displayers.iterable.Len0NoCommaTuple((
					*args,
					*kwargs_display,
				))
			)

		def _fh__call2(
			self,
			*,
			args: tuple[Any, ...],
			kwargs: dict[str, Any],
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
					Text().join((
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

		def _fh__add_indentlike_prefix(self, text: Text, *, prefix: Text) -> Text:
			r"""Add a prefix to each line of the given text, splitting at '\n'.

			Args:
				text: The Text to which the prefix should be added.
				prefix: The prefix to add to each line of the `text`.

			Returns:
				text: The formatted representation of the text with the prefix added to each line.
			"""
			return Text("\n").join(
				prefix + line  #
				for line in text.split("\n")
			)

		def _fh__spaceship_error_text(
			self,
			text: Text,
		) -> Text:
			"""Produce a multiline error-looking message for when a __nya_fmt__ method raises an exception, or further use in other cases.

			```
			this_but_highlighted_with_colors = '''
			<[
			 | Text of the error message
			 | Can be multiline, no problem
			 | It is recommended it's set to style=fmt.styles.error, though not required.
			 ]>
			'''[1:-1]
			```

			Returns:
				text: The formatted representation of the error message that gave off spaceship energy at the time of naming this function for some reason...

			"""  # ruff:ignore[mixed-spaces-and-tabs]

			style_error_b = self.styles.error + Style(bold=True)

			return Text("\n").join((
				Text("<[", style=style_error_b),
				self._fh__add_indentlike_prefix(
					text,
					prefix=Text(" | ", style=style_error_b),
				),
				Text(" ]>", style=style_error_b),
			))
