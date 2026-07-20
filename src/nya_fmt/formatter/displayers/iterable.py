from __future__ import annotations

from typing import TypeGuard

from ..providers.pystdlib import FP__builtins__tuple


class CallFromTupleDisplay(tuple):
	__slots__ = ()

	class FP(FP__builtins__tuple, priority=100):
		@property
		def is_len1_comma_added(self) -> bool:
			return False

		def accept(self, v: object) -> TypeGuard[CallFromTupleDisplay]:
			if not isinstance(v, CallFromTupleDisplay):
				return False

			return super().accept(v)
