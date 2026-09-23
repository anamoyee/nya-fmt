from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from rich.text import Text

	from .._base import Fmt


class DisplayRawText:
	def __init__(self, text: Text) -> None:
		self.text = text

	def __nya_fmt__(self, *, fmt: Fmt):
		return self.text
