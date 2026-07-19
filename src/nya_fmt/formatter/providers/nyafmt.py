import inspect
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from nya_result import Maybe
from rich.style import Style
from rich.text import Text

from ._base import FormatProviderABC as FPABC

if TYPE_CHECKING:
	from .._base import Formatter


@runtime_checkable
class NyaFmtTypingProtocol(Protocol):
	def __nya_fmt__(self, *, fmt: "Formatter") -> Text: ...


class NyaFmtFP(FPABC, priority=100):
	class FailedToBindSignatureError(TypeError):
		"""Raised when the signature of a __nya_fmt__ isn't compatible to do the further call."""

	def _make_exception_occured_text(self, *, fmt: "Formatter", v: Any, e: BaseException) -> Text:
		try:
			# with fmt.with_tmp_settings():
			# 	fmt.ensure_providers_missing(self)
			# 	formated_without_self_provider = fmt(v)  # todo: fix, it causes recursion errors
			formated_without_self_provider = Text(f"{type(v).__qualname__}")
		except Exception as e2:
			return Text(
				"While formatting a message that an exception happend when rendering a self-providing (__nya_fmt__) object, a more fundamental exception occured preventing this very message from being rendered. This is likely a bug within format providers on which the formatter machinery relies, like a broken str format provider, like a broken Str format provider, etc."
				"\nexception: " + str(e2)
			)

		if fmt.debug_raise_exceptions:
			raise e

		style_error_i = fmt.styles.error + Style(italic=True)

		return fmt._fh__spaceship_error_text(
			Text("\n").join((
				Text("Failed to __nya_fmt__ this object: ", style=fmt.styles.error) + formated_without_self_provider,
				Text("due to an uncaught exception: ", style=fmt.styles.error) + fmt(e),
				Text().join((
					Text("-> ", style=fmt.styles.punctuation),
					Text("if you wish to view the exception traceback and terminate the execution,", style=style_error_i),
				)),
				Text().join((
					Text("   "),
					Text("set `debug_raise_exceptions` in your formatter instance to True", style=style_error_i),
				)),
			))
		)

	def try_fmt(self, v: Any, /, *, fmt: "Formatter") -> Maybe[Text]:
		if not isinstance(v, NyaFmtTypingProtocol):
			return Maybe.new_none()

		kwargs: dict[str, object] = dict(
			fmt=fmt,
		)

		try:
			if not inspect.ismethod(v.__nya_fmt__):
				if not hasattr(type(v), "__nya_fmt__"):
					return Maybe.new_none()

				# metaclass defiend __nya_fmt__ method
				nyafmt_metafunc = type(v).__nya_fmt__

				sig = inspect.signature(nyafmt_metafunc)
				try:
					sig.bind(v, **kwargs)
				except TypeError as e:
					msg = f"Failed to bind the signature of {type(v).__qualname__!r}.__nya_fmt__ ({sig!r}) with the provided args & kwargs: (*({v!r},), **{kwargs!r}). "
					raise self.FailedToBindSignatureError(msg) from e

				maybe_text = nyafmt_metafunc(v, **kwargs)
			else:
				# is a normal object method
				nyafmt_func = v.__nya_fmt__

				sig = inspect.signature(nyafmt_func)
				try:
					sig.bind(**kwargs)
				except TypeError as e:
					msg = f"Failed to bind the signature of {type(v).__qualname__!r}.__nya_fmt__ ({sig!r}) with the provided kwargs: {kwargs!r}. "
					raise self.FailedToBindSignatureError(msg) from e

				maybe_text = nyafmt_func(**kwargs)

			if not isinstance(maybe_text, Text):
				msg = f"{type(v).__qualname__!r}.__nya_fmt__(...) must return a rich.text.Text object, got {type(maybe_text)!r} instead."
				raise TypeError(msg)  # ruff:ignore[raise-within-try]
				# todo: how is this raise escaping the except BaseException ...???

			return Maybe.new_some(maybe_text)

			# todo: WHY IS THE BELOW EXCEPT NOT CATCHING ANY ERRORS??? literally add a 1/0 before the return above, and the 1/0 will be raised all the way to the top, ignoring this exception handler
		except Exception as e:
			# e.add_note("This exception was raised while trying to format an object using its __nya_fmt__ method.")
			# Do not add a note, this causes duplicate notes when mutliple __nya_fmt__ passes are done.
			return Maybe.new_some(self._make_exception_occured_text(fmt=fmt, v=v, e=e))
