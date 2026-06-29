from dataclasses import dataclass
from typing import Any, Protocol, Self, runtime_checkable

from ._base import Formatter, Text


@dataclass(kw_only=True)
class NyaFmtContext:
	fmt: Formatter

	def __call__(self, __v: Any, /) -> Text:
		return self.fmt(__v)


@runtime_checkable
class NyaFmtProtocol(Protocol):
	def __nya_fmt__(self: Self | None = None, *, ctx: NyaFmtContext) -> Text: ...  # type: ignore
