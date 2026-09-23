import datetime as dt
from typing import Any

from rich.text import Text

from .._base import Fmt


class _IntWithAlteredFormatting(int):
	def upcast_to_int(self) -> int:
		"""Forget that this int is a unix timestamp, it will now display as any other number in `nya_fmt` formatters.

		Returns:
			int: The integer value of this object.
		"""
		return int(self)


class UnixTimestampInt(_IntWithAlteredFormatting):
	"""Display this int like a datetime.datetime object when formatting (interpret the value as a [unix timestamp](https://en.wikipedia.org/wiki/Unix_time)).

	### ⚠️ Note that this implementation during display will try to guess the precision of the unix timestamp, dividing by 1000 each time (Discarding the included precision!) when it thinks it's at least three orders of magnitude too large, this approach proved good enough to me over the usage of equivalent implementation in `tcrutils`.
	"""

	def to_datetime(self, *, tz: dt.tzinfo | None = dt.UTC) -> dt.datetime:
		"""Evaluate this unix timestamp into a datetime.datetime object.

		### ⚠️ Note that this implementation during display will try to guess the precision of the unix timestamp, dividing by 1000 each time (Discarding the included precision!) when it thinks it's at least three orders of magnitude too large, this approach proved good enough to me over the usage of equivalent implementation in `tcrutils`.

		Args:
			tz (dt.tzinfo | None): The timezone to use for the datetime.datetime object. Pass None if you want to explicitly make a naive datetime.datetime object.

		Returns:
			datetime.datetime: The datetime.datetime object corresponding to this unix timestamp.
		"""
		self_int_copy = int(self)

		while self_int_copy > 99_999_999_999:  # Convert any milisecond or smaller values to seconds
			self_int_copy //= 1000

		return dt.datetime.fromtimestamp(self_int_copy, tz=tz)

	def __nya_fmt__(self, *, fmt: Fmt) -> Text:
		dt = self.to_datetime()

		unix_timestamp_int = int(dt.timestamp())

		return Text().join((
			fmt._fh__raw_in_parens(fmt(dt)),
			fmt._fh__dot(),
			fmt._fh__identifier_function("timestamp"),
			fmt._fh__call(),
			Text(" -> ", style=fmt.styles.punctuation),
			fmt(self.upcast_to_int()),
		))


class HexInt(_IntWithAlteredFormatting):
	leading_zeroes: int
	prefix: str

	def as_hex(self, *, upper: bool = False) -> str:
		"""Slightly more advanced version of builtin `hex()`, offers ability to choose if uppercase and how many leading zeroes.

		Args:
			upper (bool): Whether to return the hexadecimal representation in uppercase. Defaults to True.

		Returns:
			str: The hexadecimal representation of the number, with the specified formatting.
		"""
		hex_output = hex(self)
		hex_value = hex_output[2:].zfill(self.leading_zeroes).upper() if upper else hex_output[2:].zfill(self.leading_zeroes)

		formatted_output = f"{self.prefix}{hex_value}"
		if not upper:
			formatted_output = formatted_output.lower()

		return formatted_output

	def __new__(cls, __o, /, *, leading_zeroes: int = 6, prefix: str = "0x", **kwargs: Any):
		self = super().__new__(cls, __o, **kwargs)

		self.leading_zeroes = leading_zeroes
		self.prefix = prefix

		return self

	def __nya_fmt__(self, *, fmt: Fmt) -> Text:
		text = Text(self.as_hex())

		text.highlight_regex(r"[0-9a-fA-F]+", fmt.styles.number)
		text.highlight_regex(
			r"^0[xX]0*(?=[a-fA-F0-9])",  # that lookahead: don't consume the last zero
			fmt.styles.punctuation,
		)

		return text
