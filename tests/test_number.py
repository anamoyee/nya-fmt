from .conftest import π_t


def test_int(π: π_t):
	π << 1
	π << 1234
	π << -1
	π << -1234


def test_intable_float_looks_different_than_int(π: π_t):
	π << 1  # todo: make them display differently, e.g. 1. for float
	π << 1.0
	print()
	π << -1
	π << -1.0
	print()
	π << 0
	π << 0.0
	print()
	π.comment("-0")
	π << -0
	π << -0.0


def test_float(π: π_t):
	π << 1.23e10
	π << -1.23e10
	π << 1.23e4 + 0.4
	π << -1.23e4 - 0.4
	π << 1.23
	π << -1.23
	π << 1.23e-4
	π << -1.23e-4
	π << 1.23e-8
	π << -1.23e-8
	print()
	π << float("inf")
	π << float("-inf")
	π << float("nan")
	π << float("-nan")


def test_hexint(π: π_t):
	from nya_fmt.formatter.types import HexInt

	π << HexInt(0)
	π << HexInt(255)
	π << HexInt(255, leading_zeroes=4)
	π << HexInt(255, leading_zeroes=2)
	π << HexInt(255, leading_zeroes=0)
	π << HexInt(255, leading_zeroes=-1)
	π.hr()
	π << HexInt(0x123456789ABCDEF0)
	π << HexInt(0x123456789ABCDEF0).upcast_to_int()


def test_unixtimestampint(π: π_t):
	from nya_fmt.formatter.types import UnixTimestampInt

	π << UnixTimestampInt(0)
	π << UnixTimestampInt(1_000_000_000)
	π << UnixTimestampInt(1_000_000_000_000)
	π << UnixTimestampInt(1_000_000_000_000_000)
