from typing import TYPE_CHECKING

import rich.style
from nya_result import Maybe
from rich.text import Span, Text

from ._base import FormatProviderABC as FPABC

if TYPE_CHECKING:
	from .._base import Fmt


class FP__rich__style__Style(FPABC):
	def try_fmt(self, v: object, /, *, fmt: "Fmt") -> Maybe[Text]:
		if not isinstance(v, rich.style.Style):
			return Maybe.new_none()

		with fmt.with_tmp_settings():
			fmt.indent = None
			return Maybe.new_some(
				Text().join((
					fmt(type(v)),  #
					(
						fmt._fh__raw_in_angles(
							Text(
								fmt.rich_style_preview,
								style=v,
							),
						)
						if fmt.rich_style_preview
						else Text()
					),
					(
						Text().join((
							fmt._fh__dot(),
							Text("parse", style=fmt.styles.function),
							fmt._fh__call(str(v)),
						))
						if fmt.rich_style_preview
						else fmt._fh__raw_in_parens(
							fmt._fh__raw_in_curlys(
								Text().join((
									Text(" "),
									Text(str(v), style=v),
									Text(" "),
								))
							),
						)
					),
				))
			)


class FP__rich__text__Text(FPABC):
	def make_preview_section(self, v: Text, /, *, fmt: "Fmt") -> Text:
		if fmt.rich_text_preview_max_len >= 0:
			preview = v[: fmt.rich_text_preview_max_len]
			if len(v) > fmt.rich_text_preview_max_len:
				preview += fmt._fh__raw_in_parens(fmt._fh__ellipsis())
		else:
			preview = v[:]

		return fmt._fh__raw_in_angles(preview)

	def make_call_section(self, v: Text, /, *, fmt: "Fmt") -> Text:
		return fmt._fh__call(
			v.plain,
			style=v.style,
			spans=v.spans,
		)

	def try_fmt(self, v: object, /, *, fmt: "Fmt") -> Maybe[Text]:
		if not isinstance(v, Text):
			return Maybe.new_none()

		return Maybe.new_some(
			Text().join((
				fmt(type(v)),
				self.make_preview_section(v, fmt=fmt) if fmt.rich_text_preview else Text(),
				self.make_call_section(v, fmt=fmt),
			))
		)


class FP__rich__text__Span(FPABC, priority=1):
	def try_fmt(self, v: object, /, *, fmt: "Fmt") -> Maybe[Text]:
		if not isinstance(v, Span):
			return Maybe.new_none()

		return Maybe.new_some(
			Text().join((
				fmt(type(v)),
				fmt._fh__call(
					slice=slice(v.start, v.end),
					style=v.style,
				),
			))
		)
