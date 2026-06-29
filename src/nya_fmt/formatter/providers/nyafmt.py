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


class NyaFmtFP(FPABC[Any], priority=100):
	def _make_exception_occured_text(self, *, fmt: "Formatter", v: Any, e: BaseException) -> Text:
		with fmt.with_tmp_settings():
			fmt.providers = tuple(x for x in fmt.providers if x is not self)
			formated_without_self_provider = fmt(v)

		if fmt.debug_raise_exceptions:
			raise e

		hint_msg_text = Text(
			"\n | -> if you wish to view the exception traceback and terminate the execution,"  #
			"\n |    set `debug_raise_exceptions` in your formatter instance to True\n",
			style=fmt.styles.error,
		)

		hint_msg_text.highlight_regex(r".*", "i")
		hint_msg_text.highlight_words(["|"], "not i")
		hint_msg_text.highlight_words(["->"], fmt.styles.punctuation)

		final_text = Text().join((
			Text("<[\n", style=fmt.styles.error + Style.parse("b")),  #
			Text(" | Failed to __nya_fmt__ this object: ", style=fmt.styles.error),
			formated_without_self_provider,
			Text("\n"),
			Text(" | due to an uncaught exception: ", style=fmt.styles.error),
			fmt(e),
			hint_msg_text,
			Text(" ]>", style=fmt.styles.error + Style.parse("b")),  #
		))

		final_text.highlight_words(["<(", ")>", "|"], "b")

		return final_text

	def try_fmt(self, v: Any, /, *, fmt: "Formatter") -> Maybe[Text]:
		if not isinstance(v, NyaFmtTypingProtocol):
			return Maybe.new_none()

		kwargs: dict[str, object] = dict(
			fmt=fmt,
		)

		try:
			return Maybe.new_some(v.__nya_fmt__(**kwargs))  # never pass positional args. it can cause shitass bugs.
		except BaseException as e:
			return Maybe.new_some(self._make_exception_occured_text(fmt=fmt, v=v, e=e))
