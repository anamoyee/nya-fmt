from __future__ import annotations

from typing import TypeGuard

from .pystdlib import *


class _FPABCRecognize(FPABC, no_auto_register=True):
	"""Make this object look like a recognized object by the formatter. i.e. format it in blue rather than grey. This is a shortcut for having to implement a whole ass format provider for this object if all you're doing is `fmt(type(v)) + fmt._fh__call()`."""

	@abc.abstractmethod
	def accept(self, v: Any) -> TypeGuard[FPABC]: ...

	def try_fmt(self, v: Any, /, *, fmt: Formatter) -> Maybe[Text]:
		if not self.accept(v):
			return Maybe.new_none()

		return Maybe.new_some(fmt(type(v)) + fmt._fh__call())


class FP__nya_fmt__FPABC_VIA_Recognize(_FPABCRecognize):
	def accept(self, v: Any) -> TypeGuard[FPABC]:
		return isinstance(v, FPABC)
