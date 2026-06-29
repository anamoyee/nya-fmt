import rich
import rich.style

from .builtins_ import *


class rich_style_StyleFP(FPABC[rich.style.Style]):
	def try_fmt(self, v: object, /, *, fmt: "Formatter") -> Maybe[Text]:
		if not isinstance(v, rich.style.Style):
			return Maybe.new_none()

		style_str = str(v)

		dot_text = Text(".", style=fmt.styles.punctuation)
		parse_text = Text("parse", style=fmt.styles.function)

		with fmt.with_tmp_settings():
			fmt.indent = None
			return Maybe.new_some(
				fmt(rich.style.Style)  #
				+ dot_text
				+ parse_text
				+ fmt._fh__call(style_str)
			)
