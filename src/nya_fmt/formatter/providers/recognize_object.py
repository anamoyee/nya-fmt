from __future__ import annotations

from .builtins_ import *


class RecognizeObjectFPABC[T](FPABC[T], no_auto_register=True):
	"""Make this object look like a recognized object by the formatter. i.e. format it in blue rather than grey. This is a shortcut for having to implement a whole ass format provider for this object if all you're doing is `fmt(type(v)) + fmt._fh__call()`."""

	@abc.abstractmethod
	def accept(self, v: T) -> bool: ...

	def fmt_call(self, v: T, /, *, fmt: Formatter) -> Text:
		return fmt._fh__call()

	def try_fmt(self, v: T, /, *, fmt: Formatter) -> Maybe[Text]:
		if not self.accept(v):
			return Maybe.new_none()

		return Maybe.new_some(fmt(type(v)) + self.fmt_call(v, fmt=fmt))


class RecognizeFormatProviderFP(RecognizeObjectFPABC[FPABC]):
	def accept(self, v: FPABC) -> bool:
		return isinstance(v, FPABC)
