from __future__ import annotations

from typing import TYPE_CHECKING

from nya_result import Maybe
from nya_result._result_base import _ResultBase
from rich.text import Text

from ._base import FormatProviderABC as FPABC

if TYPE_CHECKING:
	from .._base import Fmt


class FP__nya_result___ResultBase(FPABC, priority=-10):
	def try_fmt(self, v: object, /, *, fmt: Fmt) -> Maybe[Text]:
		if not isinstance(v, _ResultBase):
			return Maybe.new_none()

		variant_text = Text("Ok", style=fmt.styles.true) if v.is_ok else Text("Err", style=fmt.styles.false)

		return Maybe.new_some(
			Text().join((
				Text(type(v).__name__, style=fmt.styles.type),
				Text("::", style=fmt.styles.punctuation),
				variant_text,
				fmt._fh__call(v._value),
			))
		)
