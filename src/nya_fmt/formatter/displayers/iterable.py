from __future__ import annotations

from typing import TypeGuard

from ..providers.pystdlib import FP__builtins__tuple, FP__collections__Mapping


class Len0NoCommaTuple(tuple):
	__slots__ = ()

	class FP(FP__builtins__tuple, priority=100):
		@property
		def is_len1_comma_added(self) -> bool:
			return False

		def accept(self, v: object) -> TypeGuard[Len0NoCommaTuple]:
			if not isinstance(v, Len0NoCommaTuple):
				return False

			return super().accept(v)


class Len1MultilineTuple(tuple):
	__slots__ = ()

	class FP(FP__builtins__tuple, priority=100):
		@property
		def is_len1_skipping_indent(self) -> bool:
			return False

		def accept(self, v: object) -> TypeGuard[Len1MultilineTuple]:
			if not isinstance(v, Len1MultilineTuple):
				return False

			return super().accept(v)


class Len1MultilineDict(dict):  # ruff: ignore[subclass-builtin]
	__slots__ = ()

	class FP(FP__collections__Mapping, priority=100):
		@property
		def is_len1_skipping_indent(self) -> bool:
			return False

		def accept(self, v: object) -> TypeGuard[Len1MultilineDict]:
			if not isinstance(v, Len1MultilineDict):
				return False

			return super().accept(v)
