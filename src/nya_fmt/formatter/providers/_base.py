from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any, ClassVar, Self

if TYPE_CHECKING:
	from nya_result import Maybe
	from rich.text import Text

	from .._base import Formatter


class FormatProviderABC[_](abc.ABC): # removing this generic for some fucking reason breaks subclasses' generics with a hard error??? why the fuck i do not know
	_default_providers: ClassVar[dict[int, list[type[Self]]]] = {}

	@classmethod
	def iter_default_providers(cls):
		to_be_yielded_in_reverse = []

		for priority in sorted(cls._default_providers):
			to_be_yielded_in_reverse.extend(x() for x in cls._default_providers[priority])

		yield from reversed(to_be_yielded_in_reverse)

	def __init_subclass__(
		cls,
		*,
		no_auto_register: bool = False,
		priority: int = 0,
	) -> None:
		if not no_auto_register:
			cls._default_providers.setdefault(priority, []).insert(0, cls)  # type: ignore

	@abc.abstractmethod
	def try_fmt(self, v: Any, /, *, fmt: Formatter) -> Maybe[Text]: ...
