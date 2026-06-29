from collections.abc import Iterable

from ..providers.builtins_ import TupleFP


class CallFromTupleDisplay(tuple):
	__slots__ = ()

	class _TupleWithoutTrailingCommaFP(TupleFP[tuple], priority=100):
		@property
		def is_len1_comma_added(self) -> bool:
			return False

		def accept(self, v: Iterable) -> bool:
			if not isinstance(v, CallFromTupleDisplay):
				return False

			return super().accept(v)
