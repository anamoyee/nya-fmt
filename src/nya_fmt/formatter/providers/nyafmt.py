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

	def __init__(self) -> None:
		self._ignored_ids: set[int] = set()

	def _make_exception_occured_text(self, *, fmt: "Formatter", v: Any, e: BaseException) -> Text:
		if fmt.debug_raise_exceptions:
			e.add_note("Raising the exception as part of `Formatter.debug_raise_exceptions`.")
			raise e

		if not hasattr(self, "_ignored_ids"):
			self._ignored_ids = set()

		self._ignored_ids.add(id(v))
		try:
			formated_without_self_provider = fmt(v)
		except Exception as e2:
			return Text(
				"While formatting a message that an exception happend when rendering a self-providing (__nya_fmt__) object, a more fundamental exception occured preventing this very message from being rendered. This is likely a bug within format providers on which the formatter machinery relies, like a broken str format provider, like a broken Str format provider, etc."
				"\nexception: " + str(e2)
			)
		finally:
			self._ignored_ids.discard(id(v))

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
		if not hasattr(self, "_ignored_ids"):
			self._ignored_ids = set()

		if id(v) in self._ignored_ids:
			return Maybe.new_none()

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
			return Maybe.new_some(maybe_text)
		except Exception as e:
			e.add_note("This exception was raised while trying to format an object using its __nya_fmt__ method.")
			return Maybe.new_some(self._make_exception_occured_text(fmt=fmt, v=v, e=e))
