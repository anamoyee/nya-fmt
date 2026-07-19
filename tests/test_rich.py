def test_rich_style(π):
	π << π.fmt.styles


def test_rich_text(π):
	π << π.fmt("String with quotes that is over the default preview max length limit")
	π << π.fmt(123)
	π << π.fmt(123.456)
	π << π.fmt(True)
