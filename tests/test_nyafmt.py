from rich.text import Text

from nya_fmt import Formatter


class TstNyaFmtMeta(type):
	def __nya_fmt__(cls, *, fmt: Formatter) -> Text:
		return Text("nyafmt: formatting type")


class TstNyaFmt(metaclass=TstNyaFmtMeta):
	def __nya_fmt__(self, *, fmt: Formatter) -> Text:
		return Text("nyafmt: formatting instance")


def test_nyafmt(π):
	π <<= TstNyaFmt()
	π <<= TstNyaFmt
