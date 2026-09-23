from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from rich.text import Text

if TYPE_CHECKING:
	from .._base import Fmt


@dataclass
class DisplayAsKeywordArg:
	name: str
	value: object

	sep: str = field(kw_only=True, default="=")

	def __nya_fmt__(self, fmt: Fmt) -> Text:
		return Text().join((
			Text(self.name, style=fmt.styles.keyword_arg_name),
			Text(self.sep, style=fmt.styles.punctuation),
			fmt(self.value),
		))
